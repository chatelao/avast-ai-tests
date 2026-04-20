import os
import sys
import time
import json
import requests
import asyncio
import aiohttp
from vastai.sdk import VastAI

def get_instance_details(instance_id):
    api_key = os.getenv("VAST_AI_API_KEY")
    url = f"https://console.vast.ai/api/v0/instances/{instance_id}/"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        print(f"Fetching details for Instance {instance_id} from {url}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Log structure for debugging
        if "instances" in data:
            instances = data["instances"]
            print(f"Found {len(instances)} instances in response.")
            inst = next((i for i in instances if str(i.get('id')) == str(instance_id)), None)
            if inst:
                return inst

        inst = data.get("instance") or data
        if isinstance(inst, dict) and str(inst.get('id')) == str(instance_id):
            return inst

        print(f"Warning: Could not find Instance {instance_id} in response keys: {list(data.keys())}")
        return None
    except Exception as e:
        print(f"Error fetching details: {e}")
        return None

async def wait_for_api(url, api_key, timeout=1200):
    endpoint = f"{url}/v1/models"
    print(f"Starting API health check at {endpoint}...")
    headers = {"Authorization": f"Bearer {api_key}"}
    start = time.time()

    async with aiohttp.ClientSession() as session:
        while time.time() - start < timeout:
            elapsed = int(time.time() - start)
            try:
                print(f"[{elapsed}s] GET {endpoint}...", end=" ", flush=True)
                async with session.get(endpoint, headers=headers, timeout=10) as resp:
                    print(f"Status: {resp.status}")
                    if resp.status == 200:
                        content = await resp.text()
                        print(f"API is ready! Response snippet: {content[:100]}...")
                        return True
                    elif resp.status == 401:
                        print("Error: 401 Unauthorized - Check Bearer Token.")
            except aiohttp.ClientConnectorError:
                print("Connection failed (Server starting?)")
            except asyncio.TimeoutError:
                print("Request timed out.")
            except Exception as e:
                print(f"Unexpected error: {type(e).__name__}: {e}")

            await asyncio.sleep(15)
    return False

async def main():
    print("--- Poll Script Startup ---")
    if not os.path.exists(".vast_instance_id"):
        print("::error::.vast_instance_id not found")
        sys.exit(1)

    with open(".vast_instance_id", "r") as f:
        instance_id = f.read().strip()
    print(f"Targeting Instance ID: {instance_id}")

    api_url = None
    start_time = time.time()
    print(f"Waiting for instance {instance_id} to reach 'running' state...")

    while time.time() - start_time < 1200:
        details = get_instance_details(instance_id)
        if details:
            status = details.get("actual_status") or details.get("state")
            ip = details.get("public_ipaddr")
            print(f"  Current Status: {status} | Public IP: {ip}")

            if status == "running" and ip:
                host = ip
                port = 8000
                ports = details.get("ports", {})
                print(f"  Port Mappings: {json.dumps(ports)}")

                resolved = False
                for p_key, mappings in ports.items():
                    if p_key.startswith("8000"):
                        if isinstance(mappings, list) and mappings:
                            port = mappings[0].get("HostPort", port)
                            print(f"  Resolved internal 8000 -> external {port}")
                            resolved = True
                        break

                if not resolved:
                    print(f"  Warning: No explicit mapping for 8000 found. Falling back to {port}")

                api_url = f"http://{host}:{port}"
                break
        else:
            print("  Instance details not available yet.")

        await asyncio.sleep(15)

    if not api_url:
        print("::error::Timeout waiting for instance networking or running state")
        sys.exit(1)

    with open(".vast_api_url", "w") as f:
        f.write(api_url)
    print(f"Resolved API URL: {api_url}")

    if await wait_for_api(api_url, "vllm-benchmark-token"):
        print("Polling lifecycle complete: SUCCESS")
    else:
        print("::error::API failed to become ready within timeout")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
