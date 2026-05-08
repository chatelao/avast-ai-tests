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
import numpy as np
from transformers import AutoTokenizer

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
    """Enhanced vLLM benchmark implementation using aiohttp and transformers for accuracy."""
    def __init__(self, base_url, model_name, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.api_key = api_key
        log(f"Loading tokenizer for {model_name}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        except Exception as e:
            log(f"Warning: Could not load tokenizer for {model_name}, falling back to default. Error: {e}")
            self.tokenizer = AutoTokenizer.from_pretrained("facebook/opt-125m")

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
        itls = []
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
                        try:
                            content_json = json.loads(line[6:])
                            if content_json.get("choices") and content_json["choices"][0].get("delta", {}).get("content"):
                                tokens += 1
                                if ttft is None:
                                    ttft = now - start_time
                                elif last_token_time:
                                    itls.append(now - last_token_time)
                                last_token_time = now
                        except json.JSONDecodeError:
                            pass

            duration = time.perf_counter() - start_time
            return {
                "ttft": ttft,
                "tokens": tokens,
                "duration": duration,
                "itls": itls,
                "tpot": (duration - ttft) / (tokens - 1) if tokens > 1 else 0
            }
        except Exception as e:
            log(f"::error::Exception during request: {type(e).__name__}: {e}")
            return None

    async def run(self, concurrency, num_requests):
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
            valid = [r for r in results if r and r['tokens'] > 0]
            if not valid: return None

            ttfts = [r['ttft'] for r in valid]
            tpots = [r['tpot'] for r in valid if r['tpot'] > 0]
            itls = []
            for r in valid: itls.extend(r['itls'])

            return {
                "concurrency": concurrency,
                "success_rate": len(valid) / num_requests,
                "avg_ttft": np.mean(ttfts),
                "p99_ttft": np.percentile(ttfts, 99),
                "avg_tpot": np.mean(tpots) if tpots else 0,
                "avg_itl": np.mean(itls) if itls else 0,
                "avg_tps": np.mean([r['tokens']/r['duration'] for r in valid]),
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

        # Create a pool of actors to handle requests
        clients = [OpenAIChatCompletionsClient.remote() for _ in range(concurrency)]
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
            "avg_tps": statistics.mean([r[common_metrics.REQ_OUTPUT_THROUGHPUT] for r in valid]),
            "total_tps": sum([r[common_metrics.NUM_OUTPUT_TOKENS] for r in valid]) / duration_run
        }

async def run_benchmark(tester, concurrency_levels, requests_per_level, model_name):
    all_results = []
    log(f"Starting benchmark for {model_name}...")
    for c in concurrency_levels:
        log(f"  Concurrency {c}...")
        # Use more requests for higher concurrency to get better stats
        num_reqs = max(c, requests_per_level)
        res = await tester.run(c, num_reqs)
        if res:
            all_results.append(res)
            log(f"    TPS: {res['total_tps']:.2f} (Success: {res['success_rate']*100:.1f}%)")
    return all_results

def report_results(all_results, model_name, gpu_name, num_gpus):
    if not all_results:
        log("::error::No results collected.")
        return False

    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a") as f:
            f.write(f"## Results: {model_name} on {num_gpus}x {gpu_name}\n")
            f.write("| C | Success Rate | Avg TTFT | P99 TTFT | Avg ITL | Total TPS |\n|---|---|---|---|---|---|\n")
            for r in all_results:
                p99_ttft = r.get('p99_ttft', 0)
                avg_itl = r.get('avg_itl', 0)
                f.write(f"| {r['concurrency']} | {r['success_rate']*100:.1f}% | {r['avg_ttft']:.3f} | {p99_ttft:.3f} | {avg_itl*1000:.1f}ms | {r['total_tps']:.2f} |\n")
        log(f"Summary written to {summary_file}")

    gpu_str = f"{num_gpus}x_{gpu_name.replace(' ', '_')}"
    timestamp = int(time.time())
    output_file = f"benchmark_{gpu_str}_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    log(f"Results written to {output_file}")

    # Also write to a fixed name for easier artifact collection
    with open("results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    return True

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
    args = parser.parse_args()

    api_url = args.url
    if not api_url:
        if not os.path.exists(".vast_api_url"):
            log("::error::.vast_api_url not found and --url not provided")
            sys.exit(1)
        with open(".vast_api_url", "r") as f:
            api_url = f.read().strip()

    vllm_api_key = os.getenv("VLLM_API_KEY_OVERRIDE", "vllm-benchmark-token")

    if args.benchmark_type == "llmperf":
        tester = LLMPerfTester(api_url, args.model, vllm_api_key)
    else:
        tester = LoadTester(api_url, args.model, vllm_api_key)

    all_results = await run_benchmark(tester, args.concurrency_levels, args.requests_per_level, args.model)
    success = report_results(all_results, args.model, args.gpu, args.num_gpus)

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
