import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 800, 'height': 350})
        page = await context.new_page()

        file_path = f"file://{os.path.abspath('reddit_mock.html')}"
        print(f"Loading {file_path}")
        await page.goto(file_path)

        # Take screenshot of just the post element
        element = await page.query_selector('.post')
        if element:
            await element.screenshot(path='output/deepseek-v4-hands-on/reddit-post.png')
            print("Reddit mock captured successfully!")
        else:
            print("Element not found")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
