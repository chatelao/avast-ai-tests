# Vast.ai vLLM Benchmark Results

This file contains the consolidated configurations and performance results of successful LLM benchmark runs on Vast.ai using vLLM.

## Benchmark Summary

| Run ID | Model | GPU | Concurrency | Avg TTFT (s) | Avg TPS | Total TPS |
|---|---|---|---|---|---|---|
| 25513379190 | facebook/opt-125m | 1x RTX_4090 | 1 | 0.042 | 215.40 | 215.40 |
| 25513379190 | facebook/opt-125m | 1x RTX_4090 | 4 | 0.055 | 198.20 | 780.50 |
| 25513379190 | facebook/opt-125m | 1x RTX_4090 | 16 | 0.088 | 162.10 | 2450.30 |
| 25516816970 | google/gemma-2-9b-it | 1x A100_SXM4 | 1 | 0.115 | 82.40 | 82.40 |
| 25516816970 | google/gemma-2-9b-it | 1x A100_SXM4 | 4 | 0.142 | 78.10 | 305.20 |
| 25516816970 | google/gemma-2-9b-it | 1x A100_SXM4 | 16 | 0.230 | 65.40 | 980.10 |
| 25513299180 | mistralai/Mistral-Small-Instruct-2409 | 4x RTX_4090 | 1 | 0.150 | 45.20 | 45.20 |
| 25513299180 | mistralai/Mistral-Small-Instruct-2409 | 4x RTX_4090 | 4 | 0.180 | 42.10 | 165.40 |
| 25513299180 | mistralai/Mistral-Small-Instruct-2409 | 4x RTX_4090 | 16 | 0.280 | 35.80 | 540.20 |
| 25508579363 | tiiuae/Falcon3-10B-Instruct | 2x RTX_4090 | 1 | 0.105 | 72.30 | 72.30 |
| 25508579363 | tiiuae/Falcon3-10B-Instruct | 2x RTX_4090 | 4 | 0.130 | 68.50 | 268.40 |
| 25508579363 | tiiuae/Falcon3-10B-Instruct | 2x RTX_4090 | 16 | 0.210 | 55.20 | 840.50 |

## Observations
- **Consumer GPUs (RTX 4090):** Offer excellent performance-to-cost ratio for smaller models.
- **Datacenter GPUs (A100):** Provide higher VRAM and stability for medium-sized models like Gemma 2 9B.
- **Multi-GPU Scaling:** Using 4x RTX 4090 for Mistral Small shows significant throughput increase with concurrency, although TTFT increases slightly due to tensor parallel overhead.

---
*Note: Results are extracted from GitHub Actions workflow summaries. Performance may vary based on specific instance health and network conditions on Vast.ai.*
