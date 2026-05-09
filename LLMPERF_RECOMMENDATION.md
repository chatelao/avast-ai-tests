# LLMPerf Best Practices & Recommendations

This document outlines the recommended configurations and architectural patterns for running `llmperf` effectively, based on the implementation in `benchmark.py`.

## 1. Ray Initialization & Environment

When using `llmperf` with a remote vLLM endpoint, Ray should be initialized with the necessary environment variables via `runtime_env`. This ensures that all distributed actors have access to the API configuration.

### Recommended `ray.init` Parameters:
- **`OPENAI_API_BASE`**: Set to the `/v1` endpoint of your vLLM server.
- **`OPENAI_API_KEY`**: Provide a placeholder or actual key if authentication is enabled.
- **`RAY_ACCEL_ENV_VAR_OVERRIDE_ON_ZERO`**: Set to `"0"` to suppress unnecessary accelerator override warnings when running on CPU-only client nodes.

```python
ray.init(
    runtime_env={"env_vars": {
        "OPENAI_API_BASE": "http://<vast-ip>:<port>/v1",
        "OPENAI_API_KEY": "your-token",
        "RAY_ACCEL_ENV_VAR_OVERRIDE_ON_ZERO": "0"
    }}
)
```

## 2. Actor Pool Management

To scale benchmarking to high concurrency without overwhelming the Ray Global Control Service (GCS), use a fixed-size pool of Ray actors.

- **`MAX_RAY_ACTORS`**: Cap the number of actors (e.g., at 32). This is sufficient for generating massive load while keeping the Ray cluster stable.
- **Load Balancing**: Use `itertools.cycle` to distribute requests across the actor pool.

```python
num_actors = min(concurrency, 32)
clients = [OpenAIChatCompletionsClient.remote() for _ in range(num_actors)]
client_pool = itertools.cycle(clients)
```

## 3. Concurrency Control

Relying solely on Ray for concurrency can lead to scheduling overhead. Use `asyncio.Semaphore` in the client-side loop to precisely control the number of active requests.

- **Semaphore**: Match the semaphore value to your desired concurrency level.
- **Async Gathering**: Use `asyncio.gather` to manage multiple concurrent requests efficiently.

```python
semaphore = asyncio.Semaphore(concurrency)

async def worker():
    async with semaphore:
        client = next(client_pool)
        return await client.llm_request.remote(request_config)
```

## 4. Request Configuration

Ensure the `RequestConfig` matches the expectations of the model and the `llmperf` client.

- **Prompt Format**: `llmperf` expects the prompt as a tuple: `(prompt_text, estimated_token_count)`.
- **Sampling Params**: Explicitly set `max_tokens` to ensure consistent benchmark durations.

```python
prompt = (prompt_text, len(prompt_text.split()))
request_config = RequestConfig(
    model=self.model_name,
    prompt=prompt,
    sampling_params={"max_tokens": 100}
)
```

## 5. Performance Metrics

Focus on the following metrics provided by `llmperf` via `common_metrics`:
- **TTFT (Time to First Token)**: Critical for interactive applications.
- **Output Throughput**: Measured in tokens per second (TPS).
- **Success Rate**: Monitor for error codes in the metrics output to ensure the endpoint isn't being overloaded.

## 6. Cleanup

Always kill Ray actors after a benchmark run to free up resources, especially if running multiple trials in a single script.

```python
for client in clients:
    ray.kill(client)
```
