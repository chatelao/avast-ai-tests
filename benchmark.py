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
import subprocess

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
        last_token_time = start_time

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

                        # Only count as a token if it contains actual content
                        try:
                            content_json = json.loads(line[6:])
                            if content_json.get("choices") and content_json["choices"][0].get("delta", {}).get("content"):
                                tokens += 1
                        except json.JSONDecodeError:
                            # Fallback if JSON parsing fails but it's a data line
                            tokens += 1

                        now = time.perf_counter()
                        if ttft is None: ttft = now - start_time
                        last_token_time = now

            duration = time.perf_counter() - start_time
            return {"ttft": ttft, "tokens": tokens, "duration": duration}
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
            valid = [r for r in results if r]
            if not valid: return None

            return {
                "concurrency": concurrency,
                "success_rate": len(valid) / num_requests,
                "avg_ttft": statistics.mean([r['ttft'] for r in valid]),
                "avg_tps": statistics.mean([r['tokens']/r['duration'] for r in valid]),
                "total_tps": sum([r['tokens'] for r in valid]) / duration_run
            }

async def run_vllm_benchmark(args, api_url):
    all_results = []
    for c in args.concurrency_levels:
        log(f"  Concurrency {c} (vLLM method)...")
        result_filename = f"vllm_temp_{c}_{int(time.time())}.json"

        cmd = [
            sys.executable, "vllm_benchmark_serving.py",
            "--model", args.model,
            "--base-url", api_url,
            "--endpoint", "/v1/chat/completions",
            "--backend", "openai-chat",
            "--dataset-name", "random",
            "--random-input-len", "100", # Match legacy roughly
            "--random-output-len", "100",
            "--num-prompts", str(args.requests_per_level),
            "--concurrency", str(c),
            "--request-rate", "inf",
            "--save-result",
            "--result-filename", result_filename,
            "--trust-remote-code"
        ]

        # Pass VLLM_API_KEY if present
        env = os.environ.copy()
        if "VLLM_API_KEY_OVERRIDE" in env:
            env["OPENAI_API_KEY"] = env["VLLM_API_KEY_OVERRIDE"]
        elif "OPENAI_API_KEY" not in env:
            env["OPENAI_API_KEY"] = "vllm-benchmark-token"

        try:
            subprocess.run(cmd, check=True, env=env)

            if not os.path.exists(result_filename):
                log(f"::error::vLLM result file {result_filename} not found")
                continue

            with open(result_filename, "r") as f:
                vllm_res = json.load(f)

            os.remove(result_filename)

            res = {
                "concurrency": c,
                "success_rate": vllm_res["completed"] / args.requests_per_level if args.requests_per_level > 0 else 0,
                "avg_ttft": vllm_res.get("mean_ttft_ms", 0) / 1000,
                "avg_tps": vllm_res.get("output_throughput", 0),
                "total_tps": vllm_res.get("output_throughput", 0)
            }
            all_results.append(res)
            log(f"    TPS: {res['total_tps']:.2f}")
        except subprocess.CalledProcessError as e:
            log(f"::error::vLLM benchmark failed for concurrency {c}: {e}")

    return all_results

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--gpu", default="RTX_4090")
    parser.add_argument("--num-gpus", type=int, default=1)
    parser.add_argument("--url", help="Override API URL")
    parser.add_argument("--concurrency-levels", type=int, nargs="+", default=[1, 4, 16])
    parser.add_argument("--requests-per-level", type=int, default=10)
    parser.add_argument("--method", choices=["legacy", "vllm"], default="vllm", help="Benchmarking method")
    args = parser.parse_args()

    api_url = args.url
    if not api_url:
        if not os.path.exists(".vast_api_url"):
            log("::error::.vast_api_url not found and --url not provided")
            sys.exit(1)
        with open(".vast_api_url", "r") as f:
            api_url = f.read().strip()

    vllm_api_key = os.getenv("VLLM_API_KEY_OVERRIDE", "vllm-benchmark-token")
    all_results = []

    log(f"Starting benchmark for {args.model} using {args.method} method...")

    if args.method == "vllm":
        all_results = await run_vllm_benchmark(args, api_url)
    else:
        tester = LoadTester(api_url, args.model, vllm_api_key)
        for c in args.concurrency_levels:
            log(f"  Concurrency {c}...")
            res = await tester.run(c, args.requests_per_level)
            if res:
                all_results.append(res)
                log(f"    TPS: {res['total_tps']:.2f}")

    if all_results:
        summary_file = os.getenv("GITHUB_STEP_SUMMARY")
        if summary_file:
            with open(summary_file, "a") as f:
                f.write(f"## Results: {args.model} on {args.num_gpus}x {args.gpu}\n")
                f.write("| C | Success Rate | Avg TTFT | Avg TPS | Total TPS |\n|---|---|---|---|---|\n")
                for r in all_results:
                    f.write(f"| {r['concurrency']} | {r['success_rate']*100:.1f}% | {r['avg_ttft']:.3f} | {r['avg_tps']:.2f} | {r['total_tps']:.2f} |\n")
            log(f"Summary written to {summary_file}")

        gpu_str = f"{args.num_gpus}x_{args.gpu.replace(' ', '_')}"
        output_file = f"benchmark_{gpu_str}_{int(time.time())}.json"
        with open(output_file, "w") as f:
            json.dump(all_results, f, indent=2)
        log(f"Results written to {output_file}")
        with open("results.json", "w") as f:
            json.dump(all_results, f, indent=2)
        log(f"Results written to results.json")
    else:
        log("::error::No results collected. Exiting with failure.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
