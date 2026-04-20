# CONCEPT: Gemma Performance Lab on Vast.ai

## Overview
The Gemma Performance Lab is an automated benchmarking framework designed to evaluate the performance and cost-efficiency of Gemma models across the diverse hardware landscape of Vast.ai. By automating the entire lifecycle—from hardware provisioning to data analysis—it provides objective data to help developers choose the optimal GPU for their specific LLM workloads.

## Core Objectives
- **Hardware Benchmarking:** Compare high-end datacenter GPUs (A100, H100) against consumer-grade flagships (RTX 4090, 3090) for LLM serving.
- **Latency Analysis:** Quantify the user experience through Time to First Token (TTFT) and Inter-Token Latency (ITL).
- **Economic Evaluation:** Determine the "Tokens per Dollar" efficiency of different instance types.

## Architecture

![Architecture](https://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/chatelao/vast-ai-tests/main/architecture.puml)

The system is composed of four standalone Python scripts orchestrated by GitHub Actions. State is shared between steps using local files (`.vast_instance_id` and `.vast_api_url`).

### 1. Provisioning (`launch.py`)
- **Responsibility:** Automated marketplace search and instance rental.
- **Inputs:** GPU name, Model name, Template Hash.
- **Outputs:** Persists the Instance ID to `.vast_instance_id`.
- **Features:**
    - Queries Vast.ai for specific GPU models (e.g., RTX 4090).
    - Configures vLLM environment variables and port mappings (8000 for API).
    - Uses predefined template hashes for consistent deployments.

### 2. Readiness Check (`poll.py`)
- **Responsibility:** Verifies the instance is running and the vLLM API is healthy.
- **Inputs:** Reads Instance ID from `.vast_instance_id`.
- **Outputs:** Persists the resolved API URL to `.vast_api_url`.
- **Features:**
    - Polls Vast.ai instance metadata for public IP and mapped external ports.
    - Performs health checks against the `/v1/models` endpoint.
    - Implements retry logic with absolute timestamps in logs.

### 3. Load Testing (`benchmark.py`)
- **Responsibility:** High-concurrency performance measurement.
- **Inputs:** Reads API URL from `.vast_api_url`, takes model and concurrency levels.
- **Outputs:** JSON reports and GitHub Step Summary table.
- **Features:**
    - Asynchronous request handling using `aiohttp`.
    - Captures TTFT and TPS for varying concurrency levels.
    - Supports streaming responses for granular timing data.

### 4. Cleanup (`teardown.py`)
- **Responsibility:** Guaranteed resource destruction to prevent runaway costs.
- **Inputs:** Reads Instance ID from `.vast_instance_id`.
- **Features:**
    - Destroys the Vast.ai instance regardless of benchmark success/failure.
    - Removes temporary state files.

## Target Metrics
- **TTFT (Time to First Token):** The time from request initiation to the first character received.
- **TPS (Tokens Per Second):** Total throughput across all concurrent users.
- **TPS/$:** Tokens per second divided by the hourly rental rate.

## Workflow Execution
The primary entry point is the **GitHub Actions workflow** (`vast_ai_benchmark.yml`), which executes the scripts in sequence:
1. **Launch:** Request a GPU and start the vLLM container.
2. **Poll:** Wait for the server to be fully responsive.
3. **Benchmark:** Run a series of load tests at different concurrency levels.
4. **Teardown:** Destroy the instance and cleanup.
