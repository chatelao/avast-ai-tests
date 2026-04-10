# HOWTO: Using the Vast.ai vLLM Template

This guide explains how to use the pre-configured Vast.ai template to deploy vLLM quickly. Using a template automates the server startup, reducing the number of manual steps required to start benchmarking.

**Template Hash:** `7e24e4e5c2e551d012344a9bf4f141c2`

## Option 1: Using the Vast.ai Web Console

1.  **Go to the Create Instance Page:** Navigate to [vast.ai/console/create/](https://vast.ai/console/create/).
2.  **Select the Template:**
    - Click on **"EDIT IMAGE & CONFIG"**.
    - Go to the **"Templates"** tab.
    - Search for the template using the hash: `7e24e4e5c2e551d012344a9bf4f141c2` (or look for the vLLM template if available in the recommended list).
    - Select it and click **"SELECT AND CLOSE"**.
3.  **Find Hardware:** Search for your desired GPU (e.g., "RTX 4090").
4.  **Rent:** Click **"RENT"** on your chosen offer.
5.  **Wait for Ready:** The instance will automatically pull the Docker image and start the vLLM server. You can monitor the progress in the "Instances" tab.

## Option 2: Using the Command Line (CLI)

If you have the `vastai` CLI installed and configured, you can rent an instance using the template hash directly.

1.  **Find an Offer ID:**
    ```bash
    vastai search offers 'gpu_name = RTX_4090'
    ```
2.  **Rent with Template:**
    ```bash
    vastai create instance <OFFER_ID> --template_hash 7e24e4e5c2e551d012344a9bf4f141c2 --disk 50
    ```

## Benefits of Using the Template

-   **Automatic Startup:** The vLLM engine starts automatically upon instance creation.
-   **Optimized Configuration:** The template comes with pre-configured environment variables and start commands.
-   **Faster Setup:** No need to manually `docker run` via SSH, which saves time on expensive GPU instances.

## Benchmarking with the Template

Once the instance is ready and the API is up, you can run the orchestrator from your local machine (if it has network access to the instance) or from another inexpensive instance:

```bash
python3 orchestrator.py --gpu "RTX 4090" --model "gemma-2-9b-it" --url http://<INSTANCE_IP>:<PORT> --run
```
