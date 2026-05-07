import asyncio
from playwright.async_api import async_playwright
import sys

async def main():
    run_id = sys.argv[1]
    # We need the job ID to get to the job page where the summary is more likely to be visible
    # But let's try the run page again with a better selector and more wait time
    url = f"https://github.com/chatelao/vast-ai-tests/actions/runs/{run_id}"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = await context.new_page()
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle")

        await asyncio.sleep(20) # Heavy wait for summary to load

        # GitHub Step Summaries are often inside an element with [data-test-selector="step-summary-content"] or similar
        # But .markdown-body is the most common.

        summary_locator = page.locator(".markdown-body")
        count = await summary_locator.count()
        print(f"Found {count} markdown-body elements")

        for i in range(count):
            text = await summary_locator.nth(i).inner_text()
            if "Results:" in text:
                print(f"--- SUMMARY {i} START ---")
                print(text)
                print(f"--- SUMMARY {i} END ---")

        # If not found, try searching for the text "Results:" directly
        results_locator = page.get_by_text("Results:", exact=False)
        r_count = await results_locator.count()
        print(f"Found {r_count} elements with 'Results:'")

        if r_count == 0:
             await page.screenshot(path=f"final_debug_{run_id}.png", full_page=True)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
