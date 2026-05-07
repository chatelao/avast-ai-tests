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

        await asyncio.sleep(15)

        # Look for buttons that might need to be clicked
        buttons = await page.query_selector_all("button")
        for button in buttons:
            text = await button.inner_text()
            if "Summary" in text:
                print(f"Clicking button: {text}")
                await button.click()
                await asyncio.sleep(5)

        content = await page.content()
        if "Results:" in content:
            print("FOUND_RESULTS")
            # ...
        else:
            # Maybe it's in the log?
            print("Trying to find 'Results:' in any element...")
            found = await page.evaluate("""() => {
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
                let node;
                while (node = walker.nextNode()) {
                    if (node.textContent.includes('Results:')) return node.parentElement.innerText;
                }
                return null;
            }""")
            if found:
                print("--- FOUND VIA TREEWALKER ---")
                print(found)
            else:
                print("NOT FOUND VIA TREEWALKER")
                # List all iframes
                frames = page.frames
                for f in frames:
                    print(f"Frame: {f.name} {f.url}")
                    try:
                        f_content = await f.content()
                        if "Results:" in f_content:
                            print(f"FOUND IN FRAME {f.name}")
                    except:
                        pass

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
