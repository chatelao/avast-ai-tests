# Running Benchmarks "Native" on Vast.ai

To eliminate network jitter and get the most accurate performance metrics (especially for TTFT), it is recommended to run the `benchmark.py` script directly on the Vast.ai instance where the model is hosted.

## Prerequisites

1.  A running Vast.ai instance with vLLM (launched via `launch.py`).
2.  The instance ID (stored in `.vast_instance_id` after launch).
3.  Vast.ai CLI installed and configured on your local machine.

## Step-by-Step Instructions

### 1. Identify the Instance IP and Port
Find your instance's IP and the mapped port for the vLLM API (usually 8000).

```bash
vastai show instances
```

### 2. Copy the Benchmark Script to the Instance
You can use `scp` or `vastai copy` to move the necessary files to the remote instance.

```bash
# Get the connection string/IP from 'vastai show instances'
# Replace <INSTANCE_IP> and <PORT> accordingly
scp -P <SSH_PORT> benchmark.py requirements.txt root@<INSTANCE_IP>:/root/
```

### 3. Install Dependencies Remotely
SSH into the instance and install the benchmarking dependencies.

> **Note:** For `llmperf` mode, a Python 3.10 environment is required.

```bash
vastai ssh-url <INSTANCE_ID>
# Inside the SSH session:
pip install -r requirements.txt
```

### 4. Run the Benchmark Locally
Run the script targeting `localhost`. Since it's running on the same machine as the server, network latency is effectively zero.

```bash
python3 benchmark.py \
    --model <MODEL_ID> \
    --gpu <GPU_MODEL> \
    --num-gpus <COUNT> \
    --url http://localhost:8000 \
    --concurrency-levels 1 4 16 64 256 \
    --requests-per-level 256 \
    --benchmark-type llmperf \
    --enable-prefix-caching
```

### Key Options Explained

*   **`--enable-prefix-caching`**: Toggle the vLLM prefix caching feature. This must be passed both to `launch.py` (to enable it on the server) and `benchmark.py` (to ensure it's correctly reported in the results).
*   **`--gpu` & `--num-gpus`**: Crucial for result labeling. The output filenames and reports will use these to identify the hardware configuration.
*   **`--requests-per-level`**: Follow the **Saturation Rule**. Ensure this is at least equal to your highest concurrency level (e.g., 256) to ensure the target concurrency is actually reached and maintained during the test.
*   **`--benchmark-type llmperf`**: Recommended for high-concurrency testing. It uses Ray actors to distribute the load generation, preventing the benchmark script itself from becoming a CPU bottleneck.

### 5. Collecting Results
The results will be saved as JSON files on the instance. You can copy them back to your local machine:

```bash
scp -P <SSH_PORT> root@<INSTANCE_IP>:/root/benchmark_*.json .
```

## Comparison: GHA vs. Native

*   **GitHub Actions:** Convenient, automated, but TTFT includes ~50-200ms of internet latency and jitter.
*   **Native (Remote):** Raw performance measurement. TTFT reflects only the model engine's processing time. Recommended for publishing official benchmarks.
