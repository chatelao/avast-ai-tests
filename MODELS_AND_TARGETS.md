# Model and Hardware Targets

This document provides recommendations for matching LLM models with appropriate hardware on Vast.ai, based on the resource estimation logic used in this project.

## Hardware Selection Logic

The recommendations are based on the following formulas used in `launch.py`:
- **Model Weight Size (GB):** `Parameters (Billion) * 2` (assuming BF16/FP16).
- **Required VRAM per GPU (GB):** `(Model Size / Number of GPUs) + 12GB Buffer`.
- **Required Disk Space (GB):** `Model Size + 12GB Buffer`.

*Note: The 12GB buffer is a conservative estimate used by the automation scripts to ensure sufficient VRAM for KV cache and system overhead.*

## Recommendations Table

| Model Family | Model Name | Recommended GPU(s) | Min VRAM/GPU | Min Disk | Arch | Experts | Coding | Refac | Architectural Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gemma 4*** | `google/gemma-4-E2B-it` | 1x RTX 4090 / 3090 | 16 GB | 16 GB | Dense | - | Low | Low | |
|  | `google/gemma-4-E4B-it` | 1x RTX 4090 / 3090 | 20 GB | 20 GB | Dense | - | Mid | Mid | |
|  | `google/gemma-4-26B-A4B-it` | 1x A100 (80GB) | 64 GB | 64 GB | MoE | 4 | Mid | Mid | |
|  | `google/gemma-4-31B-it` | 1x A100 (80GB) | 74 GB | 74 GB | Dense | - | Mid | Mid | |
| **Gemma 2** | `google/gemma-2-9b-it` | 2x RTX 4090 or 1x A100 | 21 GB / 30 GB | 30 GB | Dense | - | Low | Low | |
| **Mistral** | `mistralai/Mistral-Small-Instruct-2409` | 4x RTX 4090 or 1x A100 | 23 GB / 56 GB | 56 GB | Dense | - | Mid | Mid | |
|  | `mistralai/Mistral-Large-Instruct-2411` | 4x A100 (80GB) / H100 | 74 GB | 258 GB | Dense | - | High | High | |
|  | `mistralai/Devstral-2-123B-Instruct` | 4x A100 (80GB) / H100 | 74 GB | 258 GB | Dense | - | High | High | |
|  | `mistralai/Mistral-Medium-3.5-128B` | 4x A100 (80GB) / H100 | 76 GB | 268 GB | Dense | - | High | High | EAGLE |
|  | `mistralai/Codestral-22B-v0.1` | 4x RTX 4090 or 1x A100 | 23 GB / 56 GB | 56 GB | Dense | - | High | High | |
|  | `mistralai/Codestral-v0.2` | 4x RTX 4090 or 1x A100 | 23 GB / 56 GB | 56 GB | Dense | - | High | High | |
|  | `mistralai/Codestral-2` | 4x RTX 4090 or 1x A100 | 23 GB / 56 GB | 56 GB | Dense | - | High++| High++| Standard Instruct & FIM |
| **Qwen** | `Qwen/Qwen2.5-Coder-32B-Instruct` | 1x A100 (80GB) | 76 GB | 76 GB | Dense | - | High++| High++| |
|  | `Qwen/Qwen3-235B-A22B` | 8x A100 (80GB) | 71 GB | 482 GB | MoE | 64 | High | High | |
|  | `Qwen/Qwen3-235B-A22B-Instruct-2507` | 8x A100 (80GB) | 71 GB | 482 GB | MoE | 64 | High | High | |
|  | `Qwen/Qwen-3.6-35B-A3B` | 1x A100 (80GB) | 82 GB | 82 GB | Sparse| - | Mid | Mid | Extreme Sparsity |
| **DeepSeek** | `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct`| 4x RTX 4090 or 1x A100 | 20 GB / 44 GB | 44 GB | MoE | 16 | High | High | |
|  | `deepseek-ai/DeepSeek-V4-Flash` | 8x H200 / B200 | 83 GB | 580 GB | MoE | 128 | High | High | |
|  | `deepseek-ai/DeepSeek-V4-Pro` | Multi-node / 8x B200 | 412 GB | 3212 GB| MoE | 256 | High++| High++| |
|  | `deepseek-ai/DeepSeek-V3.2` | Multi-node / 8x H200 | 180 GB | 1354 GB| MoE | 160 | High | High | |
|  | `deepseek-ai/DeepSeek-R1` | Multi-node / 8x H200 | 180 GB | 1354 GB| MoE | 160 | High++| High++| |
| **Kimi** | `moonshotai/Kimi-K2.5` | Requires Multi-node | 287 GB | 2212 GB| MoE | 128 | High | High | |
|  | `moonshotai/Kimi-K2.6` | Requires Multi-node | 262 GB | 2012 GB| MoE | 256 | High++| High++| Agentic Swarm |
| **Falcon** | `tiiuae/Falcon3-10B-Instruct` | 2x RTX 4090 or 1x A100 | 22 GB / 32 GB | 32 GB | Dense | - | Mid | Mid | |
| **Llama 4** | `meta-llama/Llama-4-Maverick-17B-128E-Instruct`| 8x H200 | 112 GB | 812 GB | MoE | 128 | High | High | |
|  | `meta-llama/Llama-4-Scout-400B-Instruct` | 8x H200 | 112 GB | 812 GB | MoE | 256 | High++| High++| 10M Kontext, NoPE |
| **GLM** | `zai-org/GLM-4.6` | 8x H200 | 101 GB | 726 GB | MoE | 64 | High | High | |
|  | `zai-org/GLM-5.1` | Multi-node / 8x H200 | 201 GB | 1520 GB| MoE | 128 | High++| High++| 754B MoE, MIT-Lizenz |
| **GPT-OSS** | `openai/gpt-oss-120b` | 4x A100 (80GB) / H100 | 70 GB | 246 GB | Dense | - | High | High | |
| **Small/Test** | `facebook/opt-125m` | 1x RTX 4090 / 3090 | 12 GB | 12 GB | Dense | - | N/A | N/A | |
|  | `step-ai/Step-3.5-Flash` | 1x A100 (80GB) | 52 GB | 52 GB | Dense | - | Mid | Mid | MTP-3 |
|  | `ibm/Granite-4.0-8B-Instruct` | 2x RTX 4090 or 1x A100 | 20 GB / 28 GB | 28 GB | Hybrid| - | Mid | Mid | Hybrid Mamba2 |

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
