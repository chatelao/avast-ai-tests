import os
import sys
import datetime
from vastai.sdk import VastAI

def log(message, end="\n"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", end=end, flush=True)

def main():
    instance_id = None
    if os.path.exists(".vast_instance_id"):
        with open(".vast_instance_id", "r") as f:
            instance_id = f.read().strip()

    if not instance_id:
        log("No instance ID to destroy.")
        return

    api_key = os.getenv("VAST_AI_API_KEY")
    if not api_key:
        log("::error::VAST_AI_API_KEY not set")
        sys.exit(1)

    sdk = VastAI(api_key=api_key)
    log(f"Destroying instance {instance_id}...")
    result = sdk.destroy_instance(id=int(instance_id))
    log(f"Result: {result}")

    for f in [".vast_instance_id", ".vast_api_url"]:
        if os.path.exists(f):
            os.remove(f)

if __name__ == "__main__":
    main()
