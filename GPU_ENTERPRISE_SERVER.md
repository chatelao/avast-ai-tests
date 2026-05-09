# Enterprise LLM Server Configurations

This document outlines recommended GPU server configurations for enterprise Large Language Model (LLM) workloads, including training, fine-tuning, and inference.

## Summary Table

| Tier | Use Case | GPU Configuration | Est. Price (USD) | Nutanix Ready |
| :--- | :--- | :--- | :--- | :--- |
| **Ultra-Scale** | Foundation Training / Large MoE | 8x H100/H200/B200 (SXM) | $350k - $500k+ | Yes (AHV + vGPU) |
| **Mid-Range** | Fine-tuning / Perf Inference | 8x L40S (PCIe) | $80k - $130k | Yes (vGPU/NVAIE) |
| **Entry-Level** | Edge / Standard Inference | 4x L4 (PCIe) | $15k - $30k | Yes (vGPU) |

---

## 1. Ultra-Scale: High-Performance Training (HGX/SXM)
Designed for training large foundation models and serving massive MoE models (e.g., DeepSeek-V3, Llama-4-Scout) with minimal latency.

*   **GPU:** 8x NVIDIA H100 / H200 / B200 SXM5
*   **Interconnect:** NVIDIA NVLink + NVSwitch (up to 900GB/s bandwidth)
*   **Server Mainboard/Platform:**
    *   **Supermicro:** SYS-821GE-TNHR (Air-cooled) or Liquid-cooled variants.
    *   **Dell:** PowerEdge XE9680 (based on HGX reference architecture).
*   **CPU:** Dual 4th/5th Gen Intel Xeon Scalable or AMD EPYC 9004 Series (up to 128 cores).
*   **RAM:** 2TB+ DDR5-4800 ECC.
*   **Networking:** 8x 400G InfiniBand/Ethernet (1:1 GPU-to-NIC ratio) for multi-node clustering.
*   **Storage:** 30TB+ NVMe Gen5 SSDs.
*   **Pricing Guess:** $350,000 - $500,000 per node.
*   **Nutanix Compatibility:** Supported via Nutanix AHV with NVIDIA vGPU software. Requires NVIDIA AI Enterprise (NVAIE) licensing for full stack support.

## 2. Mid-Range: Performance Inference & Fine-Tuning (PCIe)
The "workhorse" of the enterprise AI lab. Ideal for fine-tuning 70B+ models or high-throughput inference using L40S.

*   **GPU:** 8x NVIDIA L40S (48GB GDDR6 each)
*   **Interconnect:** PCIe Gen5 with NVLink Bridge (optional).
*   **Server Mainboard/Platform:**
    *   **Supermicro:** AS-4125GS-TNRT (Dual AMD EPYC) or SYS-421GU-TNXR (Intel).
*   **CPU:** Dual AMD EPYC 9004 or Intel Xeon Scalable (32-64 cores per socket).
*   **RAM:** 1TB DDR5 ECC.
*   **Networking:** Dual 100G/200G Ethernet.
*   **Storage:** 15TB+ NVMe Gen4/Gen5 SSDs.
*   **Pricing Guess:** $80,000 - $130,000.
*   **Nutanix Compatibility:** Fully certified for Nutanix "GPT-in-a-Box". Supports AHV vGPU and NVAIE.

## 3. Entry-Level: Edge & Small Model Inference
Cost-effective solution for deploying specialized models (e.g., Gemma 2 9B, Mistral Small) and RAG applications at the edge.

*   **GPU:** 4x NVIDIA L4 (24GB GDDR6 low-profile)
*   **Interconnect:** PCIe Gen4/Gen5.
*   **Server Mainboard/Platform:**
    *   **Supermicro:** SYS-111E-WR (1U) or SYS-221H-TNR (2U).
*   **CPU:** Single or Dual Intel Xeon Scalable (16-32 cores).
*   **RAM:** 256GB - 512GB DDR5.
*   **Networking:** Dual 10G/25G Ethernet.
*   **Storage:** 7.68TB NVMe SSD.
*   **Pricing Guess:** $15,000 - $30,000.
*   **Nutanix Compatibility:** Excellent. Low power draw and PCIe density make these ideal for distributed Nutanix clusters.

---

## Nutanix Implementation Notes

### Nutanix GPT-in-a-Box
Nutanix offers a pre-validated software-defined AI solution called **GPT-in-a-Box**. It simplifies the deployment of AI infrastructure by providing:
*   **Nutanix AHV:** The primary hypervisor for running GPU-accelerated VMs.
*   **NVIDIA vGPU Support:** Allows slicing physical GPUs into virtual instances or aggregating multiple GPUs into a single VM.
*   **Kubernetes Integration:** Uses Nutanix Kubernetes Engine (NKE) to orchestrate LLM containers (vLLM, TGI).
*   **Data Services:** Nutanix Objects/Files provides the S3-compatible storage needed for model weights and training datasets.

### Technical Requirements
1.  **NVIDIA AI Enterprise (NVAIE):** Mandatory for official support and access to optimized frameworks.
2.  **vGPU Licensing:** Required for AHV to communicate with the NVIDIA driver stack.
3.  **HCI Interconnect:** Ensure 25GbE+ backend networking between Nutanix nodes to handle high-speed storage traffic during LLM loading.
