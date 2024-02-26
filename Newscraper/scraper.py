import asyncio
from pyppeteer import launch
from datetime import datetime
import os
import logging
from fake_useragent import UserAgent
from urllib.parse import quote_plus

# Setting up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

output_directory = "Saved_Articles"
os.makedirs(output_directory, exist_ok=True)

async def archive_page(uri, use_random_user_agent=True):
    browser = await launch(headless=True)
    page = await browser.newPage()
    user_agent = UserAgent().random if use_random_user_agent else "Your Fixed User Agent Here"
    await page.setUserAgent(user_agent)
    await page.goto('https://archive.today/?run=1&url=' + uri)
    logging.info("Page archived successfully.")
    await browser.close()

async def scrape_and_save_article(browser, link, idx, search_query, max_retries=3):
    for retry in range(max_retries):
        page = await browser.newPage()
        try:
            await page.setUserAgent(UserAgent().random)
            await page.goto(str(link))  # Ensure link is a string
            await asyncio.sleep(2)

            page_content = await page.content()
            title_element = await page.querySelector("h1")
            article_title = await page.evaluate('(element) => element.textContent', title_element) if title_element else "UnknownTitle"
            valid_title = ''.join(char for char in article_title if char.isalnum() or char.isspace())

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = os.path.join(output_directory, f"{timestamp}_{search_query}_{valid_title}_{idx + 1}.html")

            with open(file_name, "w", encoding="utf-8") as file:
                file.write(f"<a href='{link}' target='_blank'>Source Article</a>\n\n")
                file.write(page_content)

            logging.info(f"Article {idx + 1} saved: {file_name}")
            return
        except Exception as e:
            logging.error(f"Error on attempt {retry + 1} for article {idx + 1}: {e}")
            if retry < max_retries - 1:
                await asyncio.sleep(5)  # Wait before retrying
            else:
                logging.error(f"Failed to scrape and save article {idx + 1} after {max_retries} retries.")
        finally:
            if page:
                await page.close()

async def get_article_links(query, max_articles, max_pages=5):
    browser = await launch(headless=True)
    page = await browser.newPage()
    await page.setUserAgent(UserAgent().random)
    all_links = []

    for p in range(max_pages):
        try:
            page_url = f"https://news.google.com/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en&p={p}"
            await page.goto(page_url)
            await page.waitForSelector('article')

            articles = await page.querySelectorAll('article')
            links = [await page.evaluate('(article) => article.querySelector("a") ? article.querySelector("a").href : null', article) for article in articles]
            all_links.extend(links)

            if len(all_links) >= max_articles:
                break
        except Exception as e:
            logging.error(f"Error fetching article links: {e}")
            break  # Exit the loop on error

    await browser.close()
    return all_links[:max_articles]

async def scrape_articles(search_query, max_articles):
    browser = None
    try:
        article_links = await get_article_links(search_query, max_articles)
        browser = await launch(headless=True)
        tasks = [scrape_and_save_article(browser, link, idx, search_query) for idx, link in enumerate(article_links)]
        await asyncio.gather(*tasks)
    finally:
        if browser:
            await browser.close()

# Ethical Consideration Note:
# Ensure to comply with the terms of service of the websites and respect robots.txt files.

# Example usage
if __name__ == "__main__":
    asyncio.run(scrape_articles("Your Search Query Here", 10))
