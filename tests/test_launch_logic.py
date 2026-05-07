import pytest
from launch import estimate_model_params

def test_estimate_model_params_new_models():
    assert estimate_model_params("moonshotai/Kimi-K2.5") == 1100.0
    assert estimate_model_params("tiiuae/Falcon3-10B-Instruct") == 10.0
    assert estimate_model_params("meta-llama/Llama-4-Maverick-17B-128E-Instruct") == 400.0
    assert estimate_model_params("Qwen/Qwen3-235B-A22B") == 235.0
    assert estimate_model_params("zai-org/GLM-4.6") == 357.0
    assert estimate_model_params("openai/gpt-oss-120b") == 117.0
    assert estimate_model_params("Qwen/Qwen3-235B-A22B-Instruct-2507") == 235.0

def test_estimate_model_params_existing_models():
    assert estimate_model_params("facebook/opt-125m") == 0.125
    assert estimate_model_params("google/gemma-2-9b-it") == 9.0
    assert estimate_model_params("mistralai/Mistral-Small-Instruct-2409") == 22.0

from launch import get_vllm_args

def test_get_vllm_args_trust_remote_code():
    token = "test-token"
    # Models that SHOULD have the flag
    assert "--trust-remote-code" in get_vllm_args("moonshotai/Kimi-K2.5", 1, token)
    assert "--trust-remote-code" in get_vllm_args("Qwen/Qwen3-235B-A22B", 1, token)
    assert "--trust-remote-code" in get_vllm_args("zai-org/GLM-4.6", 1, token)
    assert "--trust-remote-code" in get_vllm_args("openai/gpt-oss-120b", 1, token)
    assert "--trust-remote-code" in get_vllm_args("google/gemma-4-31B-it", 1, token)

    # Models that SHOULD NOT have the flag
    assert "--trust-remote-code" not in get_vllm_args("facebook/opt-125m", 1, token)
    assert "--trust-remote-code" not in get_vllm_args("meta-llama/Llama-4-Maverick-17B-128E-Instruct", 1, token)
    assert "--trust-remote-code" not in get_vllm_args("tiiuae/Falcon3-10B-Instruct", 1, token)
