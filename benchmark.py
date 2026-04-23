import asyncio
import aiohttp
import time
import json
import statistics
import os
import argparse
import sys
import datetime

def log(message, end="\n"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", end=end, flush=True)

class LoadTester:
    def __init__(self, base_url, model_name, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.api_key = api_key

    async def send_request(self, session, prompt):
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
                        tokens += 1
                        now = time.perf_counter()
                        if ttft is None: ttft = now - start_time
                        last_token_time = now

            duration = time.perf_counter() - start_time
            return {"ttft": ttft, "tokens": tokens, "duration": duration}
        except Exception as e:
            log(f"::error::Exception during request: {type(e).__name__}: {e}")
            return None

    async def run(self, concurrency, num_requests, prompt):
        semaphore = asyncio.Semaphore(concurrency)
        async with aiohttp.ClientSession() as session:
            async def worker():
                async with semaphore:
                    return await self.send_request(session, prompt)

            results = await asyncio.gather(*(worker() for _ in range(num_requests)))
            valid = [r for r in results if r]
            if not valid: return None

            return {
                "concurrency": concurrency,
                "avg_ttft": statistics.mean([r['ttft'] for r in valid]),
                "avg_tps": statistics.mean([r['tokens']/r['duration'] for r in valid]),
                "total_tps": sum([r['tokens'] for r in valid]) / max([r['duration'] for r in valid])
            }

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--gpu", default="RTX_4090")
    parser.add_argument("--url", help="Override API URL")
    parser.add_argument("--concurrency-levels", type=int, nargs="+", default=[1, 4, 16])
    parser.add_argument("--requests-per-level", type=int, default=10)
    args = parser.parse_args()

    api_url = args.url
    if not api_url:
        if not os.path.exists(".vast_api_url"):
            log("::error::.vast_api_url not found and --url not provided")
            sys.exit(1)
        with open(".vast_api_url", "r") as f:
            api_url = f.read().strip()

    vllm_api_key = os.getenv("VLLM_API_KEY_OVERRIDE", "vllm-benchmark-token")
    tester = LoadTester(api_url, args.model, vllm_api_key)
    all_results = []

    log(f"Starting benchmark for {args.model}...")
    for c in args.concurrency_levels:
        log(f"  Concurrency {c}...")
        res = await tester.run(c, args.requests_per_level, "Explain quantum physics in one sentence.")
        if res:
            all_results.append(res)
            log(f"    TPS: {res['total_tps']:.2f}")

    if all_results:
        summary_file = os.getenv("GITHUB_STEP_SUMMARY")
        if summary_file:
            with open(summary_file, "a") as f:
                f.write(f"## Results: {args.model} on {args.gpu}\n")
                f.write("| C | Avg TTFT | Avg TPS | Total TPS |\n|---|---|---|---|\n")
                for r in all_results:
                    f.write(f"| {r['concurrency']} | {r['avg_ttft']:.3f} | {r['avg_tps']:.2f} | {r['total_tps']:.2f} |\n")
            log(f"Summary written to {summary_file}")

        output_file = f"benchmark_{args.gpu.replace(' ', '_')}_{int(time.time())}.json"
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
