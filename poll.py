import os
import sys
import time
import json
import requests
import asyncio
import aiohttp

def get_instance_details(instance_id):
    api_key = os.getenv("VAST_AI_API_KEY")
    # Using the 'instances' endpoint with filter is often more reliable than the direct ID path
    url = "https://console.vast.ai/api/v0/instances/"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        print(f"Fetching metadata from {url}...", flush=True)
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        instances = data.get("instances", [])
        inst = next((i for i in instances if str(i.get('id')) == str(instance_id)), None)

        if inst:
            return inst

        print(f"Warning: Instance {instance_id} not found in the list of {len(instances)} instances.", flush=True)
        # Fallback to direct ID if list fails
        direct_url = f"https://console.vast.ai/api/v0/instances/{instance_id}/"
        print(f"Trying direct path: {direct_url}...", flush=True)
        resp = requests.get(direct_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("instance") or resp.json()

        return None
    except Exception as e:
        print(f"Error fetching metadata: {e}", flush=True)
        return None

async def wait_for_api(url, api_key, timeout=1200):
    endpoint = f"{url}/v1/models"
    print(f"\n--- Starting API Health Check ---", flush=True)
    print(f"Endpoint: {endpoint}", flush=True)
    headers = {"Authorization": f"Bearer {api_key}"}
    start = time.time()

    async with aiohttp.ClientSession() as session:
        while time.time() - start < timeout:
            elapsed = int(time.time() - start)
            try:
                print(f"[{elapsed}s] GET {endpoint}...", end=" ", flush=True)
                async with session.get(endpoint, headers=headers, timeout=15) as resp:
                    print(f"HTTP {resp.status}", flush=True)
                    if resp.status == 200:
                        content = await resp.text()
                        print(f"Success! API is ready.", flush=True)
                        print(f"Response: {content[:200]}...", flush=True)
                        return True
                    elif resp.status == 401:
                        print("Error: 401 Unauthorized. Check Bearer Token.", flush=True)
                    else:
                        text = await resp.text()
                        print(f"Detail: {text[:100]}", flush=True)
            except aiohttp.ClientConnectorError as e:
                print(f"Connection failed: {e}", flush=True)
            except asyncio.TimeoutError:
                print("Request timed out.", flush=True)
            except Exception as e:
                print(f"Unexpected error: {type(e).__name__}: {e}", flush=True)

            await asyncio.sleep(20)
    return False

async def main():
    print("--- Poll Script Startup ---", flush=True)
    if not os.path.exists(".vast_instance_id"):
        print("::error::.vast_instance_id not found", flush=True)
        sys.exit(1)

    with open(".vast_instance_id", "r") as f:
        instance_id = f.read().strip()
    print(f"Targeting Instance ID: {instance_id}", flush=True)

    api_url = None
    start_time = time.time()
    print(f"Waiting for instance {instance_id} to initialize...", flush=True)

    while time.time() - start_time < 1200:
        details = get_instance_details(instance_id)
        if details:
            status = details.get("actual_status") or details.get("state")
            ip = details.get("public_ipaddr")
            progress = details.get("status_msg") or "N/A"
            print(f"  Status: {status} | IP: {ip} | Info: {progress}", flush=True)

            if status == "running" and ip:
                ports = details.get("ports", {})
                print(f"  Detected Port Mappings: {json.dumps(ports)}", flush=True)

                ext_port = None
                # Check for 8000/tcp mapping
                for p_key, mappings in ports.items():
                    if p_key.startswith("8000"):
                        if isinstance(mappings, list) and mappings:
                            ext_port = mappings[0].get("HostPort")
                            print(f"  Found mapping: internal 8000 -> external {ext_port}", flush=True)
                            break

                if ext_port:
                    api_url = f"http://{ip}:{ext_port}"
                    break
                else:
                    print(f"  Waiting for port 8000 mapping to appear...", flush=True)
            elif status == "error":
                print(f"::error::Instance entered error state: {progress}", flush=True)
                sys.exit(1)
        else:
            print("  Instance metadata not yet available.", flush=True)

        await asyncio.sleep(20)

    if not api_url:
        print("::error::Timeout waiting for instance running state or port 8000 mapping", flush=True)
        sys.exit(1)

    print(f"::notice::Resolved vLLM API URL: {api_url}", flush=True)
    with open(".vast_api_url", "w") as f:
        f.write(api_url)

    if await wait_for_api(api_url, "vllm-benchmark-token"):
        print("\n--- Polling SUCCESS ---", flush=True)
    else:
        print("::error::API failed to respond 200 OK within 20 minutes", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
