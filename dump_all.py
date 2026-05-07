import asyncio
from playwright.async_api import async_playwright
import sys

async def main():
    run_id = sys.argv[1]
    url = f"https://github.com/chatelao/vast-ai-tests/actions/runs/{run_id}"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        print(f"Navigating to {url}...")
        await page.goto(url)

        await asyncio.sleep(20)

        # Scroll down multiple times
        for _ in range(5):
            await page.mouse.wheel(0, 1000)
            await asyncio.sleep(1)

        # Get all text
        text = await page.evaluate("document.body.innerText")
        print("--- BODY TEXT START ---")
        print(text)
        print("--- BODY TEXT END ---")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
