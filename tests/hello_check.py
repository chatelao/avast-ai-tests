import requests
import argparse
import sys
import os

def check_hello(api_url, model, api_key):
    url = f"{api_url.rstrip('/')}/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "hello"}],
        "max_tokens": 10
    }

    print(f"Checking model {model} at {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            print(f"SUCCESS: Received response from {model}")
            data = response.json()
            content = data['choices'][0]['message']['content']
            print(f"Response: {content}")
            return True
        else:
            print(f"FAILURE: Status code {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"FAILURE: Exception occurred: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--url", help="API URL")
    args = parser.parse_args()

    api_url = args.url
    if not api_url:
        if os.path.exists(".vast_api_url"):
            with open(".vast_api_url", "r") as f:
                api_url = f.read().strip()
        else:
            print("Error: API URL not provided and .vast_api_url not found")
            sys.exit(1)

    api_key = os.getenv("VLLM_API_KEY_OVERRIDE", "vllm-benchmark-token")

    if check_hello(api_url, args.model, api_key):
        sys.exit(0)
    else:
        sys.exit(1)
