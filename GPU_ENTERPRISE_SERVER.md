# Enterprise LLM Server Configurations

This document outlines recommended GPU server configurations for enterprise Large Language Model (LLM) workloads, including training, fine-tuning, and inference.

## Summary Table

| Tier | Use Case | GPU Configuration | Est. Price (USD) | Nutanix Ready | Market Availability |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ultra-Scale** | Foundation Training / Large MoE | 8x B200 / H200 (SXM) | $400k - $600k+ | Yes (AHV + vGPU) | Limited / High Lead Time |
| **High-Performance**| Large Model Training / Inf | 8x H100 (SXM) | $300k - $480k | Yes (AHV + vGPU) | Improving / Moderate |
| **Legacy High-Perf** | Training / Large Batch Inf | 8x A100 80GB (SXM) | $130k - $330k | Yes (AHV + vGPU) | Secondary Market / Limited New |
| **Mid-Range** | Fine-tuning / Perf Inference | 8x L40S (PCIe) | $80k - $130k | Yes (vGPU/NVAIE) | General Availability |
| **Entry-Level** | Edge / Standard Inference | 4x L4 (PCIe) | $15k - $30k | Yes (vGPU) | Widely Available |

---

## 1. Ultra-Scale: High-Performance Training (HGX/SXM)
Designed for training large foundation models and serving massive MoE models (e.g., DeepSeek-V3, Llama-4-Scout) with minimal latency.

*   **GPU:** 8x NVIDIA B200 / H200 SXM
*   **Interconnect:** NVIDIA NVLink + NVSwitch (up to 1.8TB/s for B200)
*   **Server Mainboard/Platform:**
    *   **Supermicro:** SYS-821GE-TNHR (Hopper) / Liquid-cooled Blackwell clusters.
    *   **Dell:** PowerEdge XE9680 (supports H100/H200/B200).
*   **CPU:** Dual 5th Gen Intel Xeon Scalable or AMD EPYC 9005 Series.
*   **RAM:** 2TB+ DDR5-5600 ECC.
*   **Networking:** 8x 400G/800G InfiniBand/Ethernet (1:1 GPU-to-NIC ratio).
*   **Pricing Guess:** $400,000 - $600,000+ per node.
*   **Availability:** **Low**. Blackwell (B200) is in extreme demand with priority given to hyperscalers. H200 lead times are typically 3-6 months.

## 2. High-Performance: H100 Standard
The current industry benchmark for enterprise LLM training and high-end inference.

*   **GPU:** 8x NVIDIA H100 SXM5 (80GB)
*   **Server Mainboard/Platform:** Supermicro SYS-821GE-TNHR / Dell PowerEdge XE9680.
*   **Pricing Guess:** $300,000 - $480,000.
*   **Availability:** **Moderate**. Lead times have improved significantly from the 2023 peak but still require planned procurement.

## 3. Legacy High-Performance: A100 80GB
Still highly capable for massive batch inference and training where the latest transformer engine (FP8) is not a requirement.

*   **GPU:** 8x NVIDIA A100 80GB SXM4
*   **Server Mainboard/Platform:** Supermicro SYS-420GP-TNAR / Dell PowerEdge XE8545.
*   **CPU:** Dual AMD EPYC 7003 (Milan) or Intel Xeon 3rd Gen (Ice Lake).
*   **RAM:** 1TB - 2TB DDR4-3200 ECC.
*   **Pricing Guess:** $130,000 (Refurbished/Milan) - $330,000 (New Old Stock).
*   **Availability:** **Limited New / High Secondary**. Most A100 systems are now sourced through secondary markets or specialized value-added resellers (VARs).

## 4. Mid-Range: Performance Inference & Fine-Tuning (PCIe)
The "workhorse" of the enterprise AI lab. Ideal for fine-tuning 70B+ models or high-throughput inference using L40S.

*   **GPU:** 8x NVIDIA L40S (48GB GDDR6 each)
*   **Server Mainboard/Platform:** Supermicro AS-4125GS-TNRT (Dual AMD EPYC) or SYS-421GU-TNXR (Intel).
*   **Pricing Guess:** $80,000 - $130,000.
*   **Availability:** **High**. L40S is widely available with short lead times. It is often the best choice for immediate project starts.

## 5. Entry-Level: Edge & Small Model Inference
Cost-effective solution for deploying specialized models (e.g., Gemma 2 9B, Mistral Small) and RAG applications at the edge.

*   **GPU:** 4x NVIDIA L4 (24GB GDDR6 low-profile)
*   **Pricing Guess:** $15,000 - $30,000.
*   **Availability:** **High**. Stock is generally available through standard distribution channels.

---

## Nutanix Implementation Notes

### Nutanix GPT-in-a-Box
Nutanix offers a pre-validated software-defined AI solution called **GPT-in-a-Box**. It simplifies the deployment of AI infrastructure by providing:
*   **Nutanix AHV:** The primary hypervisor for running GPU-accelerated VMs.
*   **NVIDIA vGPU Support:** Supported for A100, H100, H200, L40S, and L4.
*   **Data Services:** Nutanix Objects/Files provides the S3-compatible storage needed for model weights and training datasets.

### Technical Requirements
1.  **NVIDIA AI Enterprise (NVAIE):** Mandatory for official support and access to optimized frameworks.
2.  **vGPU Licensing:** Required for AHV to communicate with the NVIDIA driver stack.
3.  **HCI Interconnect:** Ensure 25GbE+ backend networking between Nutanix nodes.
