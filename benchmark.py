import asyncio
import aiohttp
import time
import json
import statistics
import os
import argparse
import sys
import datetime
import random
import itertools
import shlex

PROMPTS = [
    "Explain quantum physics in one sentence.",
    "What are the benefits of exercise?",
    "How does a combustion engine work?",
    "Write a short poem about the ocean.",
    "Summarize the plot of Hamlet.",
    "What is the capital of France?",
    "Give me a recipe for chocolate chip cookies.",
    "Who won the Nobel Prize in Physics in 2023?",
    "Explain the theory of relativity.",
    "What is the meaning of life?",
    "How do I bake a cake?",
    "What is the fastest land animal?",
    "Write a joke about a programmer.",
    "What are the three laws of thermodynamics?",
    "Translate 'hello' to Japanese.",
    "How far is the moon from Earth?",
    "What is the square root of 144?",
    "Tell me a fun fact about dolphins.",
    "Who wrote '1984'?",
    "What is the tallest mountain in the world?"
]

def log(message, end="\n"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", end=end, flush=True)

class LoadTester:
    """Old vLLM benchmark implementation using aiohttp."""
    def __init__(self, base_url, model_name, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.api_key = api_key

    async def send_request(self, session, prompt):
        log(f" Sending request with prompt: {prompt[:50]}...")
        url = f"{self.base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "stream": True
        }

        start_time = time.perf_counter()
        ttft = None
        tokens = 0
        token_latencies = []
        last_token_time = None

        try:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    text = await response.text()
                    log(f"::error::Request failed with status {response.status}: {text[:200]}")
                    return None

                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data: "):
                        if line == "data: [DONE]": break

                        now = time.perf_counter()
                        # Only count as a token if it contains actual content
                        is_token = False
                        try:
                            content_json = json.loads(line[6:])
                            if content_json.get("choices") and content_json["choices"][0].get("delta", {}).get("content"):
                                tokens += 1
                                is_token = True
                        except json.JSONDecodeError:
                            # Fallback if JSON parsing fails but it's a data line
                            tokens += 1
                            is_token = True

                        if is_token:
                            if ttft is None:
                                ttft = now - start_time
                            else:
                                token_latencies.append(now - last_token_time)
                            last_token_time = now

            duration = time.perf_counter() - start_time
            itl = statistics.mean(token_latencies) if token_latencies else 0
            return {"ttft": ttft, "tokens": tokens, "duration": duration, "itl": itl}
        except Exception as e:
            log(f"::error::Exception during request: {type(e).__name__}: {e}")
            return None

    async def run(self, concurrency, num_requests):
        # Ensure we run at least as many requests as the concurrency level
        num_requests = max(num_requests, concurrency)
        semaphore = asyncio.Semaphore(concurrency)
        connector = aiohttp.TCPConnector(limit=0)
        async with aiohttp.ClientSession(connector=connector) as session:
            async def worker():
                prompt = random.choice(PROMPTS)
                async with semaphore:
                    return await self.send_request(session, prompt)

            start_run = time.perf_counter()
            results = await asyncio.gather(*(worker() for _ in range(num_requests)))
            duration_run = time.perf_counter() - start_run
            valid = [r for r in results if r]
            if not valid: return None

            return {
                "concurrency": concurrency,
                "success_rate": len(valid) / num_requests,
                "avg_ttft": statistics.mean([r['ttft'] for r in valid]),
                "avg_itl": statistics.mean([r['itl'] for r in valid]),
                "avg_tps": statistics.mean([r['tokens']/r['duration'] for r in valid]),
                "total_tps": sum([r['tokens'] for r in valid]) / duration_run
            }

class LLMPerfTester:
    """New benchmark implementation using the llmperf library actors."""
    def __init__(self, base_url, model_name, api_key=None):
        self.base_url = base_url.rstrip('/')
        if not self.base_url.endswith("/v1"):
            self.base_url += "/v1"
        self.model_name = model_name
        self.api_key = api_key

        import ray
        if not ray.is_initialized():
            log(f"Initializing Ray with OPENAI_API_BASE={self.base_url}")
            ray.init(
                ignore_reinit_error=True,
                runtime_env={"env_vars": {
                    "OPENAI_API_BASE": self.base_url,
                    "OPENAI_API_KEY": self.api_key or "vllm-benchmark-token",
                    "RAY_ACCEL_ENV_VAR_OVERRIDE_ON_ZERO": "0"
                }}
            )

    async def run(self, concurrency, num_requests):
        from llmperf.ray_clients.openai_chat_completions_client import OpenAIChatCompletionsClient
        from llmperf.models import RequestConfig
        from llmperf import common_metrics

        # Ensure we run at least as many requests as the concurrency level
        num_requests = max(num_requests, concurrency)

        # Create a pool of actors to handle requests.
        # Cap at 32 actors to avoid "too many worker processes" and Ray resource exhaustion.
        # Use num_cpus=0 as these actors are primarily waiting for I/O.
        # Set max_concurrency to allow each actor to handle multiple concurrent requests.
        num_actors = min(concurrency, 32)
        clients = [OpenAIChatCompletionsClient.options(num_cpus=0, max_concurrency=1000).remote() for _ in range(num_actors)]
        client_pool = itertools.cycle(clients)
        semaphore = asyncio.Semaphore(concurrency)

        async def worker():
            async with semaphore:
                client = next(client_pool)
                prompt_text = random.choice(PROMPTS)
                # LLMPerf expects prompt as (text, token_count)
                # Using a simple split for token count estimation
                prompt = (prompt_text, len(prompt_text.split()))
                request_config = RequestConfig(
                    model=self.model_name,
                    prompt=prompt,
                    sampling_params={"max_tokens": 100}
                )
                # Ray method calls return ObjectRefs which are awaitable
                try:
                    return await client.llm_request.remote(request_config)
                except Exception as e:
                    log(f"::error::LLMPerf request failed: {e}")
                    return None

        start_run = time.perf_counter()
        results = await asyncio.gather(*(worker() for _ in range(num_requests)))
        duration_run = time.perf_counter() - start_run

        # Shutdown actors to free up resources
        import ray
        for client in clients:
            ray.kill(client)

        # results is a list of (metrics, generated_text, request_config) tuples
        valid = [r[0] for r in results if r and r[0].get(common_metrics.ERROR_CODE) is None]

        if not valid:
            log(f"::error::All {num_requests} requests failed with LLMPerf")
            return None

        return {
            "concurrency": concurrency,
            "success_rate": len(valid) / num_requests,
            "avg_ttft": statistics.mean([r[common_metrics.TTFT] for r in valid]),
            "avg_itl": statistics.mean([r[common_metrics.INTER_TOKEN_LAT] for r in valid]),
            "avg_tps": statistics.mean([r[common_metrics.REQ_OUTPUT_THROUGHPUT] for r in valid]),
            "total_tps": sum([r[common_metrics.NUM_OUTPUT_TOKENS] for r in valid]) / duration_run
        }

async def run_benchmark(tester, args):
    all_results = []
    log(f"Starting benchmark for {args.model}...")
    for c in args.concurrency_levels:
        log(f"  Concurrency {c}...")
        res = await tester.run(c, args.requests_per_level)
        if res:
            all_results.append(res)
            log(f"    TPS: {res['total_tps']:.2f}")
    return all_results

def report_results(all_results, args):
    if not all_results:
        log("::error::No results collected. Exiting with failure.")
        sys.exit(1)

    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a") as f:
            f.write(f"## Results: {args.model} on {args.num_gpus}x {args.gpu}\n")
            f.write("| C | Success Rate | Avg TTFT | Avg TPS | Total TPS |\n|---|---|---|---|---|\n")
            for r in all_results:
                f.write(f"| {r['concurrency']} | {r['success_rate']*100:.1f}% | {r['avg_ttft']:.3f} | {r['avg_tps']:.2f} | {r['total_tps']:.2f} |\n")
        log(f"Summary written to {summary_file}")

    gpu_str = f"{args.num_gpus}x_{args.gpu.replace(' ', '_')}"
    timestamp = int(time.time())
    output_file = os.path.join(args.output_dir, f"benchmark_{gpu_str}_{timestamp}.json")
    results_json = os.path.join(args.output_dir, "results.json")

    os.makedirs(args.output_dir, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    log(f"Results written to {output_file}")
    with open(results_json, "w") as f:
        json.dump(all_results, f, indent=2)
    log(f"Results written to {results_json}")

async def run_remote(args):
    from vastai.sdk import VastAI

    if not os.path.exists(".vast_instance_id"):
        log("::error::.vast_instance_id not found")
        sys.exit(1)

    with open(".vast_instance_id", "r") as f:
        instance_id = f.read().strip()

    api_key = os.getenv("VAST_AI_API_KEY")
    if not api_key:
        log("::error::VAST_AI_API_KEY not set")
        sys.exit(1)

    sdk = VastAI(api_key=api_key)
    log(f"Running remote benchmark on instance {instance_id}...")

    # 1. Copy benchmark script to instance
    log("Copying benchmark.py to instance...")
    sdk.copy("local:benchmark.py", f"{instance_id}:benchmark.py")

    # 2. Prepare remote command
    # Filter out --remote and use localhost URL
    remote_args = []
    skip_next = False
    for i, arg in enumerate(sys.argv[1:]):
        if skip_next:
            skip_next = False
            continue
        if arg == "--remote":
            continue
        if arg == "--url":
            skip_next = True
            continue
        remote_args.append(arg)

    remote_args.extend(["--url", "http://localhost:8000"])
    remote_args.extend(["--output-dir", "results_remote"])

    quoted_args = [shlex.quote(a) for a in remote_args]
    cmd = (
        "pip install aiohttp requests tqdm transformers numpy ray && "
        "pip install git+https://github.com/ray-project/llmperf.git && "
        "mkdir -p results_remote && "
        f"python3 benchmark.py {' '.join(quoted_args)}"
    )

    # 3. Execute remote command
    log(f"Executing remote command: {cmd}")
    res = sdk.execute(int(instance_id), cmd)
    # The result of execute is a dict. Depending on the SDK version it might contain more info.
    # We log it for debugging and check if we got a response.
    log(f"Remote execution finished. Result: {str(res)[:200]}")

    # 4. Download results
    log("Downloading results from instance...")
    # Download the whole results directory
    # vastai copy remote:dir local:path copies the directory INTO the local path.
    # So results_remote/ becomes ./results_remote/
    sdk.copy(f"{instance_id}:results_remote/", "local:.")

    local_results = os.path.join("results_remote", "results.json")
    if os.path.exists(local_results):
        with open(local_results, "r") as f:
            return json.load(f)

    # Fallback to local root if it was somehow copied there
    if os.path.exists("results.json"):
        with open("results.json", "r") as f:
            return json.load(f)

    return None

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--gpu", default="RTX_4090")
    parser.add_argument("--num-gpus", type=int, default=1)
    parser.add_argument("--url", help="Override API URL")
    parser.add_argument("--concurrency-levels", type=int, nargs="+", default=[1, 4, 16, 64, 256, 1024, 4096])
    parser.add_argument("--requests-per-level", type=int, default=10)
    parser.add_argument("--benchmark-type", choices=["llmperf", "vllm"], default="llmperf",
                        help="Benchmark engine to use (default: llmperf)")
    parser.add_argument("--remote", action="store_true", help="Run benchmark remote on the Vast.ai instance")
    parser.add_argument("--output-dir", default=".", help="Directory to save result files")
    args = parser.parse_args()

    api_url = args.url
    if not api_url:
        if not os.path.exists(".vast_api_url"):
            log("::error::.vast_api_url not found and --url not provided")
            sys.exit(1)
        with open(".vast_api_url", "r") as f:
            api_url = f.read().strip()

    vllm_api_key = os.getenv("VLLM_API_KEY_OVERRIDE", "vllm-benchmark-token")

    if args.remote:
        all_results = await run_remote(args)
    else:
        if args.benchmark_type == "llmperf":
            tester = LLMPerfTester(api_url, args.model, vllm_api_key)
        else:
            tester = LoadTester(api_url, args.model, vllm_api_key)
        all_results = await run_benchmark(tester, args)

    report_results(all_results, args)

if __name__ == "__main__":
    asyncio.run(main())
