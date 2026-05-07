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

        await asyncio.sleep(20)

        # Click on Benchmark step if possible
        benchmark_step = page.locator("span", has_text="Benchmark").first
        if await benchmark_step.count() > 0:
            print("Clicking Benchmark step...")
            await benchmark_step.click()
            await asyncio.sleep(5)

        text = await page.evaluate("document.body.innerText")
        print("--- JOB BODY TEXT START ---")
        print(text)
        print("--- JOB BODY TEXT END ---")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
