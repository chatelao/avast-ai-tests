# Model and Hardware Targets

This document provides recommendations for matching LLM models with appropriate hardware on Vast.ai, based on the resource estimation logic used in this project.

## Hardware Selection Logic

The recommendations are based on the following formulas used in `launch.py`:
- **Model Weight Size (GB):** `Parameters (Billion) * 2` (assuming BF16/FP16).
- **Required VRAM per GPU (GB):** `(Model Size / Number of GPUs) + 12GB Buffer`.
- **Required Disk Space (GB):** `Model Size + 12GB Buffer`.

*Note: The 12GB buffer is a conservative estimate used by the automation scripts to ensure sufficient VRAM for KV cache and system overhead.*

## Recommendations Table

| Model Family | Model Name | Recommended GPU(s) | Min VRAM/GPU (Est) | Min Disk (Est) |
| :--- | :--- | :--- | :--- | :--- |
| **Gemma 4*** | `google/gemma-4-E2B-it` | 1x RTX 4090 / 3090 | 16 GB | 16 GB |
| | `google/gemma-4-E4B-it` | 1x RTX 4090 / 3090 | 20 GB | 20 GB |
| | `google/gemma-4-26B-A4B-it` | 1x A100 (80GB) | 64 GB | 64 GB |
| | `google/gemma-4-31B-it` | 1x A100 (80GB) | 74 GB | 74 GB |
| **Gemma 2** | `google/gemma-2-9b-it` | 2x RTX 4090 or 1x A100 | 21 GB (2x) / 30 GB (1x) | 30 GB |
| **Mistral** | `mistral-small-instruct-2409` | 4x RTX 4090 or 1x A100 | 23 GB (4x) / 56 GB (1x) | 56 GB |
| | `mistral-large-instruct-2411` | 4x A100 (80GB) / H100 | 74 GB | 258 GB |
| | `Codestral-22B-v0.1` | 4x RTX 4090 or 1x A100 | 23 GB (4x) / 56 GB (1x) | 56 GB |
| **Qwen** | `Qwen2.5-Coder-32B-Instruct`| 4x A100 (40GB+) | 28 GB | 76 GB |
| **DeepSeek** | `DeepSeek-Coder-V2-Lite` | 4x RTX 4090 or 1x A100 | 20 GB (4x) / 44 GB (1x) | 44 GB |
| **Small/Test**| `facebook/opt-125m` | 1x RTX 4090 / 3090 | 13 GB | 13 GB |

*\*Gemma 4 refers to specific experimental model variants supported in this benchmark suite.*

## GPU Overview

| GPU Model | VRAM | Optimal Bus | Best Use Case |
| :--- | :--- | :--- | :--- |
| **RTX 3090 / 4090** | 24 GB | PCIe 4.0 | Small models (<10B) or Multi-GPU (4x) for medium models. Best TPS/$. |
| **A100 (PCIE/SXM)** | 40 / 80 GB | SXM (NVLink) | Medium to Large models. High reliability and bandwidth. |
| **H100 (SXM/NVL/PCIE)**| 80 GB | SXM (NVLink) | State-of-the-art performance for large models. |
| **H200 / B200** | 141+ GB | SXM (NVLink) | Massive models or extremely large context windows. |

## Bus Technology & Interconnects

The choice of bus technology significantly impacts multi-GPU performance:

- **PCIe (Peripheral Component Interconnect Express):**
  - **Best for:** Single-GPU setups or high-throughput batch processing where GPU-to-GPU communication is minimal.
  - **Limitation:** Bottleneck for Tensor Parallelism due to lower bandwidth compared to NVLink.
- **NVLink / SXM (NVIDIA Link):**
  - **Best for:** Multi-GPU configurations (2x, 4x, 8x) using Tensor Parallelism (vLLM).
  - **Advantage:** Dramatically reduces Inter-Token Latency (ITL) and synchronization overhead. Essential for large models that don't fit on a single GPU.
- **Optimal Deployment:**
  - **Small Models (<10B):** PCIe is sufficient.
  - **Medium/Large Models (Multi-GPU):** Prioritize SXM/NVLink instances on Vast.ai to ensure stable ITL.

## Storage Considerations

Always ensure your `--disk` parameter in `launch.py` (or the "Disk size in GB" input in the GitHub Action) is at least as large as the **Min Disk** value above.

The workflow default is **40GB**, which is sufficient for models up to ~14B parameters. For larger models, you **must** increase this value during workflow dispatch.
