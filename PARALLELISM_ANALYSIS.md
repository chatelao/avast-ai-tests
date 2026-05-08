# Parallelism Analysis in Vast.ai Benchmark Suite

This document details how parallelism is implemented at both the infrastructure (server) level and the load testing (client) level.

## 1. Server-Side Parallelism: Tensor Parallelism (TP)

Server-side parallelism is managed by `launch.py` during the instance provisioning phase. It leverages vLLM's built-in support for distributed inference.

- **Mechanism:** When multiple GPUs are requested (`--num-gpus > 1`), the script automatically appends the `--tensor-parallel-size {num_gpus}` flag to the `VLLM_ARGS` environment variable.
- **Resource Estimation:** `launch.py` calculates the required VRAM per GPU by estimating the model size (`params * 2`) and dividing it by the number of GPUs, adding a 12GB buffer for KV cache and system overhead.
- **Hardware Requirement:** For optimal performance with Tensor Parallelism, SXM/NVLink instances are recommended to minimize Inter-Token Latency (ITL) caused by GPU-to-GPU communication overhead.

## 2. Client-Side Parallelism: Load Generation

The `benchmark.py` script provides two engines for generating parallel load, each handling concurrency differently.

### A. LoadTester (vLLM mode)
The `LoadTester` uses a lightweight, `asyncio`-based approach to simulate multiple concurrent users.

- **Concurrency Control:** Uses an `asyncio.Semaphore(concurrency)` to ensure that no more than `c` requests are active at any given time.
- **Connection Management:** Initializes `aiohttp.ClientSession` with `TCPConnector(limit=0)`. This disables the default connection limit, preventing the client from becoming a bottleneck during high-concurrency tests (e.g., 256+ users).
- **Execution:** Uses `asyncio.gather` to launch all requests for a given level. The semaphore throttles execution to the desired concurrency.

### B. LLMPerfTester (llmperf mode)
The `LLMPerfTester` leverages Ray to scale load generation, which is better suited for very high throughput or distributed benchmarking.

- **Actor-Based Scaling:** Creates a pool of Ray actors (`OpenAIChatCompletionsClient`) equal to the `concurrency` level.
- **Request Distribution:** Uses `itertools.cycle` to round-robin requests across the pool of actors.
- **Environment Isolation:** Each actor is initialized with its own `OPENAI_API_BASE` and `OPENAI_API_KEY` via Ray's `runtime_env`, ensuring clean separation of request state.

## 3. Interaction and Measurement

- **TPS (Tokens Per Second):** The suite calculates "Total TPS" using the wall-clock duration of the entire concurrency level run, providing a realistic measure of system throughput under sustained load.
- **Success Rate:** Tracks the reliability of the system under different parallelism levels, identifying the "breaking point" where the server starts rejecting connections or timing out.
