import asyncio
from playwright.async_api import async_playwright
import sys
import os

async def scrape_run(context, run_id):
    url = f"https://github.com/chatelao/vast-ai-tests/actions/runs/{run_id}"
    page = await context.new_page()
    try:
        print(f"Scraping run {run_id}...")
        await page.goto(url)
        # Give it enough time to load the summary
        await asyncio.sleep(5)

        summary = await page.query_selector(".markdown-body")
        if summary:
            content = await summary.inner_text()
            with open(f"summary_{run_id}.txt", "w") as f:
                f.write(content)
            print(f"Saved summary for {run_id}")
            return True
        else:
            print(f"Summary not found for {run_id}")
            # Try to see if it's because it's a very old run or something else
            return False
    except Exception as e:
        print(f"Error scraping {run_id}: {e}")
        return False
    finally:
        await page.close()

async def main():
    with open("successful_ids.txt", "r") as f:
        run_ids = [line.strip() for line in f if line.strip()]

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()

        # Scrape in batches to avoid overwhelming
        batch_size = 5
        for i in range(0, len(run_ids), batch_size):
            batch = run_ids[i:i+batch_size]
            tasks = [scrape_run(context, rid) for rid in batch]
            await asyncio.gather(*tasks)
            await asyncio.sleep(2)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
