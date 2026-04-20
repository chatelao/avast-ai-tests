import os
import sys
import time
import json
import asyncio
import aiohttp
import datetime
from vastai.sdk import VastAI

def log(message, end="\n"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", end=end, flush=True)

def get_instance_details(sdk, instance_id):
    try:
        log(f"Fetching metadata for instance {instance_id}...")
        instances = sdk.show_instances()
        inst = next((i for i in instances if str(i.get('id')) == str(instance_id)), None)

        if inst:
            return inst

        log(f"Warning: Instance {instance_id} not found in the list of {len(instances)} instances.")
        # Attempting direct access via raw client if SDK doesn't have it
        # The mock server handles /api/v0/instances/{id}/
        url = f"/instances/{instance_id}/"
        resp = sdk.client.get(url)
        if resp.status_code == 200:
            return resp.json().get("instance") or resp.json()

        return None
    except Exception as e:
        log(f"Error fetching metadata: {e}")
        return None

async def wait_for_api(url, api_key, timeout=1200):
    endpoint = f"{url}/v1/models"
    log(f"\n--- Starting API Health Check ---")
    log(f"Endpoint: {endpoint}")
    headers = {"Authorization": f"Bearer {api_key}"}
    start = time.time()

    async with aiohttp.ClientSession() as session:
        while time.time() - start < timeout:
            elapsed = int(time.time() - start)
            try:
                # Need special handling for the "end" parameter in timestamped log
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] [{elapsed}s] GET {endpoint}...", end=" ", flush=True)
                async with session.get(endpoint, headers=headers, timeout=15) as resp:
                    print(f"HTTP {resp.status}", flush=True)
                    if resp.status == 200:
                        content = await resp.text()
                        log(f"Success! API is ready.")
                        log(f"Response: {content[:200]}...")
                        return True
                    elif resp.status == 401:
                        log("Error: 401 Unauthorized. Check Bearer Token.")
                    else:
                        text = await resp.text()
                        log(f"Detail: {text[:100]}")
            except aiohttp.ClientConnectorError as e:
                print(f"Connection failed: {e}", flush=True)
            except asyncio.TimeoutError:
                print("Request timed out.", flush=True)
            except Exception as e:
                print(f"Unexpected error: {type(e).__name__}: {e}", flush=True)

            await asyncio.sleep(1)
    return False

async def main():
    log("--- Poll Script Startup ---")

    api_key = os.getenv("VAST_AI_API_KEY")
    server_url = os.getenv("VAST_API_URL")
    sdk = VastAI(api_key=api_key, server_url=server_url)

    if not os.path.exists(".vast_instance_id"):
        log("::error::.vast_instance_id not found")
        sys.exit(1)

    with open(".vast_instance_id", "r") as f:
        instance_id = f.read().strip()
    log(f"Targeting Instance ID: {instance_id}")

    api_url = None
    start_time = time.time()
    log(f"Waiting for instance {instance_id} to initialize...")

    while time.time() - start_time < 1200:
        details = get_instance_details(sdk, instance_id)
        if details:
            status = details.get("actual_status") or details.get("state")
            ip = details.get("public_ipaddr")
            progress = details.get("status_msg") or "N/A"
            log(f"  Status: {status} | IP: {ip} | Info: {progress}")

            if status == "running" and ip:
                ports = details.get("ports", {})
                log(f"  Detected Port Mappings: {json.dumps(ports)}")

                ext_port = None
                for p_key, mappings in ports.items():
                    if p_key.startswith("8000"):
                        if isinstance(mappings, list) and mappings:
                            ext_port = mappings[0].get("HostPort")
                            log(f"  Found mapping: internal 8000 -> external {ext_port}")
                            break

                if ext_port:
                    api_url = f"http://{ip}:{ext_port}"
                    break
                else:
                    log(f"  Waiting for port 8000 mapping to appear...")
            elif status == "error":
                log(f"::error::Instance entered error state: {progress}")
                sys.exit(1)
        else:
            log("  Instance metadata not yet available.")

        await asyncio.sleep(1)

    if not api_url:
        log("::error::Timeout waiting for instance running state or port 8000 mapping")
        sys.exit(1)

    log(f"::notice::Resolved vLLM API URL: {api_url}")
    with open(".vast_api_url", "w") as f:
        f.write(api_url)

    if await wait_for_api(api_url, "vllm-benchmark-token"):
        log("\n--- Polling SUCCESS ---")
    else:
        log("::error::API failed to respond 200 OK within 20 minutes")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
