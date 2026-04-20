import os
import sys
import time
import requests
import asyncio
import aiohttp
from vastai.sdk import VastAI

def get_instance_details(sdk, instance_id):
    # Using REST API directly for detailed port mappings if SDK is limited
    api_key = os.getenv("VAST_AI_API_KEY")
    url = f"https://console.vast.ai/api/v0/instances/{instance_id}/"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if "instances" in data:
            return next((i for i in data["instances"] if str(i.get('id')) == str(instance_id)), None)
        return data.get("instance") or data
    except Exception as e:
        print(f"Error fetching details: {e}")
        return None

async def wait_for_api(url, api_key, timeout=1200):
    print(f"Polling API at {url}...")
    headers = {"Authorization": f"Bearer {api_key}"}
    start = time.time()
    async with aiohttp.ClientSession() as session:
        while time.time() - start < timeout:
            try:
                async with session.get(f"{url}/v1/models", headers=headers, timeout=5) as resp:
                    if resp.status == 200:
                        print(f"API is ready!")
                        return True
                    else:
                        print(f"  Status {resp.status}")
            except Exception:
                pass
            await asyncio.sleep(15)
    return False

async def main():
    if not os.path.exists(".vast_instance_id"):
        print("::error::.vast_instance_id not found")
        sys.exit(1)

    with open(".vast_instance_id", "r") as f:
        instance_id = f.read().strip()

    sdk = VastAI(api_key=os.getenv("VAST_AI_API_KEY"))
    print(f"Waiting for instance {instance_id} to start...")

    api_url = None
    start_time = time.time()
    while time.time() - start_time < 1200:
        details = get_instance_details(sdk, instance_id)
        if details:
            status = details.get("actual_status") or details.get("state")
            print(f"  Status: {status}")
            if status == "running" and details.get("public_ipaddr"):
                host = details.get("public_ipaddr")
                port = 8000
                ports = details.get("ports", {})
                for p_key, mappings in ports.items():
                    if p_key.startswith("8000"):
                        if isinstance(mappings, list) and mappings:
                            port = mappings[0].get("HostPort", port)
                        break
                api_url = f"http://{host}:{port}"
                break
        await asyncio.sleep(15)

    if not api_url:
        print("::error::Timeout waiting for instance networking")
        sys.exit(1)

    with open(".vast_api_url", "w") as f:
        f.write(api_url)
    print(f"Instance IP resolved: {api_url}")

    if await wait_for_api(api_url, "vllm-benchmark-token"):
        print("Poll successful.")
    else:
        print("::error::API failed to become ready")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
