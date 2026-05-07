import asyncio
from playwright.async_api import async_playwright
import sys

async def main():
    job_id = sys.argv[1]
    url = f"https://github.com/chatelao/vast-ai-tests/actions/runs/25513379190/job/{job_id}"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        print(f"Navigating to {url}...")
        await page.goto(url)

        await asyncio.sleep(15)

        # In the job page, the summary is often at the bottom or in a specific tab
        # But usually, it's displayed if you scroll down.

        content = await page.content()
        if "Results:" in content:
            print("FOUND_RESULTS")
            # Extract
            summary = await page.locator(".markdown-body").first
            if await summary.count() > 0:
                 print(await summary.inner_text())
        else:
            print("RESULTS_NOT_FOUND")
            await page.screenshot(path=f"job_debug_{job_id}.png", full_page=True)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
