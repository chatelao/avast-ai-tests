# Benchmark Design: Scaling to 1024+ Parallel Sessions

This document outlines 10 architectural variants to achieve a robust and accurate benchmark at 1024 concurrent sessions, addressing the bottlenecks observed with the current Ray/llmperf implementation.

## The Challenge
At 1024+ concurrency, benchmarking clients face several bottlenecks:
1.  **CPU Saturation:** Managing 1024+ concurrent TLS/HTTP streams requires significant CPU cycles for context switching and network I/O.
2.  **Ray Worker Overload:** Rapidly starting many Ray actors triggers startup concurrency warnings and can lead to GCS (Global Control Service) instability.
3.  **Network Throughput:** The client's network interface or the intermediate internet path may become saturated.
4.  **Ephemeral Port Exhaustion:** Running out of available local ports for outgoing connections.

---

## 1. Staggered Ray Actor Initialization
**Concept:** Instead of creating all Ray actors at once, initialize them in small batches with a cooldown period.

*   **Pros:** Eliminates the "startup concurrency" warning; reduces initial CPU spikes.
*   **Cons:** Increases benchmark setup time.
*   **Implementation:** Wrap actor creation in a loop with `asyncio.sleep(0.5)` every 4-8 actors.

## 2. Horizontal Ray Cluster (Multi-Node)
**Concept:** Deploy a Ray cluster across multiple client machines (e.g., 4x GHA runners or small Vast.ai instances) to distribute the load generation.

*   **Pros:** Scales horizontally; bypasses single-machine CPU/Bandwidth limits.
*   **Cons:** Higher orchestration complexity; requires a head node.
*   **Implementation:** Use `ray start --head` and `ray start --address` to join nodes before running `benchmark.py`.

## 3. Pure `aiohttp` with Connection Pooling Tuning
**Concept:** Bypass Ray/llmperf and use a highly optimized single-process `asyncio` loop with a tuned `TCPConnector`.

*   **Pros:** Minimal overhead; no multi-process communication lag.
*   **Cons:** Limited by the single-core performance of the Python event loop.
*   **Implementation:** Use `aiohttp.TCPConnector(limit=0, ttl_dns_cache=300, use_dns_cache=True)` and `keepalive_timeout=60`.

## 4. Rust-based Load Generator (e.g., `llm-bench`)
**Concept:** Use a high-performance compiled language like Rust to generate the load.

*   **Pros:** Extremely efficient; can handle 10k+ connections on a single core; low jitter.
*   **Cons:** Requires a separate binary; harder to integrate with Python-based result reporting.
*   **Implementation:** Integrate a tool like `oai-benchmark` (Rust) or a custom `tokio`-based generator.

## 5. Persistent Session Warm-up & Ramp-up
**Concept:** Gradually increase concurrency from 1 to 1024 while reusing the same HTTP sessions and TCP connections.

*   **Pros:** Avoids the "thundering herd" effect; reduces TLS handshake overhead.
*   **Cons:** Benchmark takes longer; might not reflect "cold start" performance.
*   **Implementation:** Modify `benchmark.py` to maintain a persistent `ClientSession` across all concurrency levels.

## 6. Distributed Load via Kubernetes (K8s) Jobs
**Concept:** Spin up a fleet of small "Load Generator" pods, each handling 32-64 sessions.

*   **Pros:** Massive scalability; cloud-native approach.
*   **Cons:** High infrastructure overhead; requires a K8s cluster.
*   **Implementation:** Use a K8s Job to dispatch `n` replicas of a lightweight benchmark container.

## 7. Local Loopback (Same-Instance) Execution
**Concept:** Execute the benchmark script directly on the Vast.ai instance hosting the model.

*   **Pros:** Zero network latency; massive bandwidth; eliminates internet jitter.
*   **Cons:** Risks resource contention with the vLLM engine (GPU vs CPU).
*   **Implementation:** SSH into the Vast instance, install dependencies, and run `benchmark.py --url http://localhost:8000`.

## 8. HTTP/2 Multiplexing
**Concept:** Use an HTTP/2 compatible client to multiplex hundreds of requests over a single TCP connection.

*   **Pros:** Dramatically reduces the number of TCP handshakes and local port usage.
*   **Cons:** vLLM server must support HTTP/2; single TCP stream might become a bottleneck.
*   **Implementation:** Use `httpx` with HTTP/2 support enabled instead of `aiohttp`.

## 9. Queue-based Worker Pool (Celery/Redis)
**Concept:** Decouple request generation from execution using a message queue.

*   **Pros:** Highly resilient; easy to scale workers up/down; prevents client-side event loop lag.
*   **Cons:** Adds Redis as a dependency; introduces queueing latency.
*   **Implementation:** Use Celery workers to pull "request tasks" and execute them against the API.

## 10. Hardware-Optimized Client Node
**Concept:** Use a high-performance "Bare Metal" or "Compute-Optimized" instance (e.g., AWS `c7g` or Vast.ai CPU-only node) for the benchmark client.

*   **Pros:** Dedicated CPU cores for the event loop; high-performance NICs.
*   **Cons:** Higher cost; less automated than GHA.
*   **Implementation:** Provision a 32-core instance to run the benchmark client, ensuring Ray has plenty of `num_cpus` for workers.
