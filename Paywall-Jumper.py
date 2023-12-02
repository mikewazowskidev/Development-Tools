import asyncio
from pyppeteer import launch
import webbrowser
from fake_useragent import UserAgent  # Import UserAgent from fake_useragent

URLA = 'https://archive.today/?run=1&url='

async def archive_page(uri):
    browser = await launch(headless=True)
    page = await browser.newPage()
    
    # Generate a random user agent
    user_agent = UserAgent()
    await page.setUserAgent(user_agent.random)
    
    await page.goto(URLA + uri)
    print("Page archived successfully.")
    await browser.close()

def open_in_browser(url):
    webbrowser.open(url)

async def main(uri):
    print("[*] Information is the currency of democracy. - Thomas Jefferson [*]")
    await archive_page(uri)
    open_in_browser(URLA + uri)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Archive and open a web page")
    parser.add_argument("url", help="URL to archive and open")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.url))
    loop.close()
