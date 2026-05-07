import asyncio
from playwright.async_api import async_playwright
import sys
import os

async def download_artifact(run_id):
    url = f"https://github.com/chatelao/vast-ai-tests/actions/runs/{run_id}"
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        print(f"Navigating to {url}...")
        await page.goto(url)
        await asyncio.sleep(10)

        # Look for the artifact link
        # It's usually a link containing "artifacts" and the name
        try:
            artifact_link = page.get_by_role("link", name="benchmark-results")
            if await artifact_link.count() > 0:
                print(f"Found artifact link for run {run_id}. Clicking...")
                async with page.expect_download() as download_info:
                    await artifact_link.click()
                download = await download_info.value
                path = f"results_{run_id}.zip"
                await download.save_as(path)
                print(f"Downloaded artifact to {path}")
                return path
            else:
                print(f"Artifact link not found for run {run_id}")
                return None
        except Exception as e:
            print(f"Error downloading for {run_id}: {e}")
            return None
        finally:
            await browser.close()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python download_artifacts.py <run_id>")
        return
    await download_artifact(sys.argv[1])

if __name__ == "__main__":
    asyncio.run(main())
