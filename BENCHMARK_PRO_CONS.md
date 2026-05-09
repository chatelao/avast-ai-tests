# Benchmarking Analysis: GitHub Actions vs. Remote (Vast.ai)

This document analyzes the current benchmarking architecture, which executes from GitHub Actions (GHA) targeting a Vast.ai instance, and explores the implications of shifting to remote execution directly on the Vast.ai instance.

## Current Architecture: Benchmarking from GitHub Actions

Currently, `benchmark.py` runs within a GitHub Actions runner (`ubuntu-latest`). It communicates with the vLLM engine hosted on a Vast.ai GPU instance over the public internet.

### Weaknesses of GHA-based Execution

1.  **Network Latency & Jitter:**
    *   **TTFT Contamination:** Time to First Token (TTFT) metrics are heavily influenced by the geographic distance between the GHA runner (often Azure US East/West) and the Vast.ai provider.
    *   **Internet Noise:** Routing through the public internet introduces variable latency (jitter), making performance comparisons between different runs less reliable.
2.  **Bandwidth Constraints:**
    *   For high-concurrency benchmarks (e.g., 4096 concurrent requests), the GHA runner's network interface may become a bottleneck, especially when streaming large amounts of text data from multiple requests simultaneously.
3.  **Resource Limitations:**
    *   GHA runners are relatively modest (2-core CPU, 7GB RAM). Running heavy client-side logic or high-concurrency `llmperf` / Ray actors can lead to CPU saturation, negatively impacting the accuracy of client-side timing metrics.
4.  **IP Blocking & Rate Limiting:**
    *   Sudden bursts of high-concurrency traffic from GHA IP ranges can sometimes trigger firewall rules or DDoS protection on the provider side, leading to failed requests or artificial latency.

---

## Remote Execution: Running Benchmarks on Vast.ai

In this model, the `benchmark.py` script would be executed directly on the same instance (or same local network) as the vLLM engine.

### Pros

1.  **Elimination of Network Overhead:**
    *   Benchmarks target `localhost` or a local network IP. This provides the most accurate measurement of the engine's internal latency (TTFT and ITL) without external noise.
2.  **Scalability:**
    *   Vast.ai instances typically have much higher CPU core counts and significantly more RAM than GHA runners. This allows for much higher client-side concurrency without hitting local resource bottlenecks.
3.  **Consistency:**
    *   By removing the "public internet" variable, benchmark results become highly reproducible across different times of day and geographic regions.
4.  **Simplified Security:**
    *   No need to expose the vLLM port to the public internet, reducing the security surface area during the benchmark.

### Cons

1.  **Resource Contention:**
    *   **The Main Drawback:** Running the benchmark client on the same machine as the vLLM engine can consume CPU cycles and memory that the vLLM engine might otherwise use. This is particularly relevant for `llmperf` which uses Ray actors.
    *   *Mitigation:* vLLM is primarily GPU-bound, while the client is CPU-bound. On machines with high core counts, the impact may be negligible.
2.  **Complexity of Orchestration:**
    *   Requires a mechanism to "inject" the benchmark script and its dependencies into the remote container or instance after it starts.
    *   Logs and results must be collected back from the remote instance to GHA for artifact uploading.
3.  **Environment Isolation:**
    *   The benchmark's Python dependencies (Ray, `llmperf`, etc.) might conflict with the vLLM container's environment if not handled via a separate virtualenv or container.

---

## Benchmark Type Specifics

### `llmperf` (Ray-based)
*   **GHA:** Very prone to resource exhaustion on the GHA runner due to the overhead of Ray GCS and multiple actor processes.
*   **Remote:** Benefits significantly from the higher CPU/RAM of Vast.ai instances, but creates more resource contention with vLLM if the machine is small.

### `vllm` (aiohttp-based)
*   **GHA:** Suffers primarily from network jitter. Lightweight enough for the GHA CPU, but network-limited at high concurrency.
*   **Remote:** Ideal for capturing raw throughput and minimum TTFT, as `aiohttp` is extremely efficient on the local loopback.

## Conclusion & Recommendation

For **production-grade benchmarks** where precision is paramount, **remote execution on the Vast.ai instance** is recommended. The "Local" measurement provides a baseline for the model's theoretical maximum performance.

For **quick verification and health checks**, the current **GitHub Actions** approach is sufficient and easier to maintain, as it doesn't require complex remote script injection.
