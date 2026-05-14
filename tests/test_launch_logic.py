import pytest
from launch import estimate_model_params

def test_estimate_model_params_new_models():
    assert estimate_model_params("google/gemma-4-E2B-it") == 2.0
    assert estimate_model_params("google/gemma-4-26B-A4B-it") == 26.0
    assert estimate_model_params("moonshotai/Kimi-K2.5") == 1100.0
    assert estimate_model_params("tiiuae/Falcon3-10B-Instruct") == 10.0
    assert estimate_model_params("meta-llama/Llama-4-Maverick-17B-128E-Instruct") == 17.0
    assert estimate_model_params("Qwen/Qwen3-235B-A22B") == 235.0
    assert estimate_model_params("zai-org/GLM-4.6") == 357.0
    assert estimate_model_params("openai/gpt-oss-120b") == 120.0
    assert estimate_model_params("Qwen/Qwen3-235B-A22B-Instruct-2507") == 235.0
    # Added in upgrade
    assert estimate_model_params("deepseek-ai/DeepSeek-V4-Flash") == 284.0
    assert estimate_model_params("deepseek-ai/DeepSeek-V4-Pro") == 1600.0
    assert estimate_model_params("deepseek-ai/DeepSeek-R1") == 671.0
    assert estimate_model_params("meta-llama/Llama-4-Scout-400B-Instruct") == 400.0
    assert estimate_model_params("mistralai/Devstral-2-123B-Instruct") == 123.0
    assert estimate_model_params("mistralai/Mistral-Medium-3.5-128B") == 128.0
    assert estimate_model_params("mistralai/Codestral-v0.2") == 22.0
    assert estimate_model_params("Qwen/Qwen-3.6-35B-A3B") == 35.0
    assert estimate_model_params("zai-org/GLM-5.1") == 754.0
    assert estimate_model_params("moonshotai/Kimi-K2.6") == 1000.0
    assert estimate_model_params("step-ai/Step-3.5-Flash") == 20.0
    assert estimate_model_params("ibm/Granite-4.0-8B-Instruct") == 8.0
    assert estimate_model_params("microsoft/phi-4") == 14.7

def test_estimate_model_params_existing_models():
    assert estimate_model_params("facebook/opt-125m") == 0.125
    assert estimate_model_params("google/gemma-2-9b-it") == 9.0
    # Mistral Large 3 is caught by regex because of 675B
    assert estimate_model_params("mistralai/Mistral-Large-3-675B-Instruct-2512") == 675.0
    # Mistral Small 4 is caught by regex because of 119B
    assert estimate_model_params("mistralai/Mistral-Small-4-119B-2603") == 119.0
    assert estimate_model_params("mistralai/Mistral-Medium-3.5-128B") == 128.0
    assert estimate_model_params("mistralai/Ministral-3-3B-Instruct-2512") == 3.0
    assert estimate_model_params("mistralai/Ministral-3-8B-Instruct-2512") == 8.0
    assert estimate_model_params("mistralai/Ministral-3-14B-Instruct-2512") == 14.0
    assert estimate_model_params("mistralai/Devstral-2-123B-Instruct-2512") == 123.0

from launch import get_vllm_args

def test_get_vllm_args_trust_remote_code():
    token = "test-token"
    # Verify prefix caching flag
    assert "--enable-prefix-caching" in get_vllm_args("opt-125m", 1, token, enable_prefix_caching=True)
    assert "--enable-prefix-caching" not in get_vllm_args("opt-125m", 1, token, enable_prefix_caching=False)

    # Models that SHOULD have the flag
    assert "--trust-remote-code" in get_vllm_args("moonshotai/Kimi-K2.5", 1, token)
    assert "--trust-remote-code" in get_vllm_args("moonshotai/Kimi-K2.6", 1, token)
    assert "--trust-remote-code" in get_vllm_args("Qwen/Qwen3-235B-A22B", 1, token)
    assert "--trust-remote-code" in get_vllm_args("Qwen/Qwen-3.6-35B-A3B", 1, token)
    assert "--trust-remote-code" in get_vllm_args("zai-org/GLM-4.6", 1, token)
    assert "--trust-remote-code" in get_vllm_args("zai-org/GLM-5.1", 1, token)
    assert "--trust-remote-code" in get_vllm_args("openai/gpt-oss-120b", 1, token)
    assert "--trust-remote-code" in get_vllm_args("google/gemma-4-31B-it", 1, token)
    assert "--trust-remote-code" in get_vllm_args("deepseek-ai/DeepSeek-V4-Flash", 1, token)
    assert "--trust-remote-code" in get_vllm_args("step-ai/Step-3.5-Flash", 1, token)
    assert "--trust-remote-code" in get_vllm_args("ibm/Granite-4.0-8B-Instruct", 1, token)
    assert "--trust-remote-code" in get_vllm_args("mistralai/Ministral-3-3B-Instruct-2512", 1, token)
    assert "--trust-remote-code" in get_vllm_args("mistralai/Devstral-2-123B-Instruct-2512", 1, token)
    assert "--trust-remote-code" in get_vllm_args("mistralai/Mistral-Small-4-119B-2603", 1, token)
    assert "--trust-remote-code" in get_vllm_args("mistralai/Mistral-Medium-3.5-128B", 1, token)
    assert "--trust-remote-code" in get_vllm_args("microsoft/phi-4", 1, token)

    # Models that SHOULD NOT have the flag
    assert "--trust-remote-code" not in get_vllm_args("facebook/opt-125m", 1, token)
    # Llama 4 now has the flag
    assert "--trust-remote-code" in get_vllm_args("meta-llama/Llama-4-Maverick-17B-128E-Instruct", 1, token)
    assert "--trust-remote-code" not in get_vllm_args("tiiuae/Falcon3-10B-Instruct", 1, token)
