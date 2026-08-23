import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    os.makedirs('output/deepseek-v4-hands-on', exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 800, 'height': 600})
        page = await context.new_page()

        # 1. HN Comment
        try:
            print("Capturing HN...")
            await page.goto('https://news.ycombinator.com/item?id=47885014', timeout=15000)
            await page.screenshot(path='output/deepseek-v4-hands-on/hn-comment.png', full_page=False)
            print("HN Captured!")
        except Exception as e:
            print(f"Failed HN: {e}")

        # 2. Reddit Post
        try:
            print("Capturing Reddit...")
            await page.goto('https://www.reddit.com/r/LocalLLaMA/comments/1suhdki', timeout=15000)
            await page.wait_for_timeout(3000)
            await page.screenshot(path='output/deepseek-v4-hands-on/reddit-post.png', full_page=False)
            print("Reddit Captured!")
        except Exception as e:
            print(f"Failed Reddit: {e}")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
