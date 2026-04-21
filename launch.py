import os
import sys
import argparse
import datetime
from vastai.sdk import VastAI
from vastai.utils import parse_env

def log(message, end="\n"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", end=end, flush=True)

def main():
    parser = argparse.ArgumentParser(description="Launch Vast.ai vLLM instance")
    parser.add_argument("--gpu", type=str, default="RTX_4090")
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--template-hash", type=str, default="38b2b68cf896e8582dff6f305a2041b1")
    args = parser.parse_args()

    api_key = os.getenv("VAST_AI_API_KEY")
    if not api_key:
        log("::error::VAST_AI_API_KEY not set")
        sys.exit(1)

    server_url = os.getenv("VAST_API_URL")
    if server_url:
        log(f"Using custom Vast.ai API URL: {server_url}")

    sdk = VastAI(api_key=api_key, server_url=server_url)

    log(f"Searching for {args.gpu}...")
    query = f"gpu_name={args.gpu} num_gpus=1 rentable=True verified=True"
    offers = sdk.search_offers(query=query, order="dph_total")
    if not offers:
        log(f"::error::No offers found for {args.gpu}")
        sys.exit(1)

    offer_id = offers[0]['id']
    log(f"Found offer {offer_id} at ${offers[0].get('dph_total'):.3f}/hr")

    hf_token = os.getenv("HF_TOKEN", "")
    vllm_api_key = "vllm-benchmark-token"
    vllm_args = "--dtype auto --enforce-eager --max-model-len 512 --block-size 16 --port 8000"

    # As of transformers v4.44, certain models (like OPT) require a chat template to be explicitly provided.
    # We provide a basic template if the model is from a family known to lack one.
    models_needing_template = ["facebook/opt-125m"]
    if any(m in args.model for m in models_needing_template):
        vllm_args += " --chat-template \"{% for message in messages %}{{ message['content'] }}{% endfor %}\""

    env_str = f"-e VLLM_MODEL={args.model} -e VLLM_ARGS='{vllm_args}' -e HF_TOKEN={hf_token} -e OPEN_BUTTON_TOKEN={vllm_api_key} -p 1111:1111 -p 7860:7860 -p 8000:8000 -p 8265:8265 -p 8080:8080"
    env_dict = parse_env(env_str)

    log(f"Renting instance with template {args.template_hash}...")
    result = sdk.create_instance(id=offer_id, template_hash=args.template_hash, env=env_dict)
    if result.get("success"):
        instance_id = result.get("new_contract")
        log(f"Successfully created instance {instance_id}")
        with open(".vast_instance_id", "w") as f:
            f.write(str(instance_id))
    else:
        log(f"::error::Failed to rent instance: {result}")
        sys.exit(1)

if __name__ == "__main__":
    main()
