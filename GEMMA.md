# Goal
Compare LLM model performances using vast.ai as remote GPU / vLLM provider:

## Metrics defined
- TTFT: Time to First Token (ms) - Measures responsiveness.
- ITL: Inter-Token Latency (ms) - Measures reading speed consistency.
- TPS: Tokens Per Second - Measures total throughput.
- TPS/$: Cost efficiency of the hardware.

## Models to be tested
- <tbd>

## GPUs to be tested
- RTX_3090
- RTX_4090
- A100
- H100

# HOWTO
- Use the vast.ai template "38b2b68cf896e8582dff6f305a2041b1" to setup a vLLM instance.
- General rule: Add a date/timestamp to every line logged.

# Secrets 
- Use "VAST_AI_API_KEY" to access "vast.ai"
- Use "HF_TOKEN" to access Hugging Face
