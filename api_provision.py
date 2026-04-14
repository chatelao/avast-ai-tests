import requests
import json
import time
import os

# Configuration
VAST_API_KEY = os.getenv("VAST_AI_API_KEY")
TEMPLATE_HASH = "38b2b68cf896e8582dff6f305a2041b1"
GPU_NAME = "RTX_4090"

def find_offer():
    """Search for an available RTX 4090 offer."""
    url = "https://console.vast.ai/api/v0/bundles/"
    headers = {"Authorization": f"Bearer {VAST_API_KEY}"} if VAST_API_KEY else {}
    query = {
        "gpu_name": {"in": [GPU_NAME]},
        "num_gpus": {"gte": 1},
        "rentable": {"eq": True},
        "verified": {"eq": True},
        "type": "ondemand"
    }
    response = requests.post(url, headers=headers, json=query)
    response.raise_for_status()
    offers = response.json().get("offers", [])
    if not offers:
        raise Exception(f"No offers found for {GPU_NAME}")
    return offers[0]["id"]

def create_instance(offer_id):
    """Rent an instance using a template hash."""
    url = f"https://console.vast.ai/api/v0/asks/{offer_id}/"
    headers = {"Authorization": f"Bearer {VAST_API_KEY}"} if VAST_API_KEY else {}
    data = {
        "template_hash_id": TEMPLATE_HASH,
        "disk": 50
    }
    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    if not result.get("success"):
        raise Exception(f"Failed to create instance: {result}")
    return result.get("new_contract")

def get_instance_details(instance_id):
    """Fetch current details for a specific instance."""
    url = f"https://console.vast.ai/api/v0/instances/{instance_id}/"
    headers = {"Authorization": f"Bearer {VAST_API_KEY}"} if VAST_API_KEY else {}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    # The API returns a list of instances or a single instance object
    data = response.json()
    if "instances" in data:
        return data["instances"]
    return data

def wait_for_instance(instance_id, timeout=1200):
    """Wait for the instance to reach 'running' state and have networking."""
    print(f"Waiting for instance {instance_id} to be running...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        details = get_instance_details(instance_id)
        # Handle both list and dict responses
        if isinstance(details, list):
            details = next((i for i in details if i['id'] == instance_id), {})

        status = details.get("actual_status") or details.get("state")
        print(f"Current status: {status}")

        if status == "running" and details.get("public_ipaddr"):
            return details

        if status == "error":
            raise Exception(f"Instance {instance_id} entered error state")

        time.sleep(15)
    raise Exception("Timeout waiting for instance to start")

def download_openapi(api_url):
    """Attempt to download openapi.json/yaml from the running service."""
    os.makedirs("api", exist_ok=True)
    paths = ["/openapi.json", "/openapi.yaml", "/v1/openapi.json"]

    for path in paths:
        url = f"{api_url}{path}"
        print(f"Trying to download from {url}...")
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                target = "api/openapi.yaml"
                with open(target, "w") as f:
                    f.write(resp.text)
                print(f"Successfully downloaded to {target}")
                return True
        except Exception as e:
            print(f"Failed path {path}: {e}")
    return False

def main():
    if not VAST_API_KEY:
        print("Error: VAST_AI_API_KEY environment variable is required.")
        return

    try:
        # 1. Find Offer
        offer_id = find_offer()
        print(f"Found offer: {offer_id}")

        # 2. Create Instance
        instance_id = create_instance(offer_id)
        print(f"Created instance: {instance_id}")

        # 3. Wait for Ready
        details = wait_for_instance(instance_id)
        host = details.get("public_ipaddr")

        # Extract mapped port for internal 8000
        port_8000 = None
        ports = details.get("ports", {})
        for p_key, mapping in ports.items():
            if p_key.startswith("8000"):
                if isinstance(mapping, list) and len(mapping) > 0:
                    port_8000 = mapping[0].get("HostPort")
                break

        if not port_8000:
            print("Warning: Could not resolve mapped port for 8000. Trying default.")
            port_8000 = 8000

        api_url = f"http://{host}:{port_8000}"
        print(f"Instance Access URL: {api_url}")

        # 4. Download OpenAPI
        # Give the service a moment to start up its API server
        print("Waiting 30s for service startup...")
        time.sleep(30)
        if not download_openapi(api_url):
            print("Could not download OpenAPI specification from the instance.")

    except Exception as e:
        print(f"Error during provisioning: {e}")

if __name__ == "__main__":
    main()
