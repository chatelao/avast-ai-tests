# LLM Benchmarking Recommendations

This document outlines the best practices for running LLM benchmarks within this repository, specifically comparing the original `vllm` mode and the `llmperf` integration.

## Benchmark Mode Selection

The `benchmark.py` script supports two engines via the `--benchmark-type` flag:

### 1. `llmperf` (Default)
- **Best for:** High-concurrency testing (>100 concurrent requests).
- **How it works:** Uses Ray actors to distribute the load generation across multiple processes, preventing the benchmark client itself from becoming the bottleneck.
- **Prerequisites:** Requires a Python 3.10 environment (due to `llmperf` and Ray compatibility issues on newer versions like 3.11+).
- **Advantages:** More accurate for massive scale; provides standardized metrics.

### 2. `vllm` (Original)
- **Best for:** Quick sanity checks, low-concurrency testing, and environments where Ray cannot be easily initialized.
- **How it works:** Uses a single-process `asyncio` loop with `aiohttp`.
- **Advantages:** Lower overhead; no dependency on Ray; easier to debug.

## Execution Best Practices

To get the most accurate results, follow these recommendations:

### Concurrency and Request Volume
*   **Saturation Rule:** Always set `--requests-per-level` to be at least equal to your highest `--concurrency-levels`. If you test concurrency 1024 with only 10 requests, you never actually achieve 1024 concurrent requests.
*   **Recommended Command:**
    ```bash
    python benchmark.py --model <MODEL_ID> --concurrency-levels 1 4 16 64 256 --requests-per-level 256 --benchmark-type llmperf
    ```

### Hardware Optimization
*   **Multi-GPU Synchronization:** For models requiring multiple GPUs, prioritize instances with **NVLink / SXM** interconnects. Standard PCIe instances often suffer from high Inter-Token Latency (ITL) due to communication bottlenecks between GPUs during Tensor Parallelism.
*   **VRAM Overhead:** The benchmark assumes a ~12GB VRAM buffer for the KV cache. Ensure the chosen GPU has sufficient VRAM beyond the raw model weights (calculated as `Parameters * 2` for FP16/BF16).

### Client-Side Performance
*   **Connection Pooling:** The script is optimized with `TCPConnector(limit=0)` in `vllm` mode to prevent the client from limiting outgoing connections.
*   **Ray Actor Scaling:** In `llmperf` mode, the script caps Ray actors at 32 (`MAX_RAY_ACTORS`). This is a balance between load generation power and Ray GCS stability.

## Environment Setup

Due to specific dependency constraints:
1.  **Python Version:** Use **Python 3.10**.
2.  **Dependencies:** Install via `pip install -r requirements.txt`.
    *   Note: `llmperf` is installed directly from the Ray Project's GitHub repository to ensure the latest fixes for OpenAI API compatibility.

## Metrics to Watch
*   **TTFT (Time to First Token):** Essential for assessing the responsiveness of the model.
*   **TPS (Tokens Per Second):** The primary throughput metric. Compare `Total TPS` across different concurrency levels to find the saturation point.
*   **Success Rate:** If the success rate drops below 100% at high concurrency, it indicates the vLLM server is dropping requests or the network is saturated.
