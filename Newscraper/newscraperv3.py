# main.py
import asyncio
from scraper import scrape_articles

async def main():
    while True:
        search_query = input("Enter your search query (or 'exit' to quit): ")
        if search_query.lower() == 'exit':
            break

        max_articles_input = input("Enter the maximum number of articles to scrape (default 10): ")
        max_articles = int(max_articles_input) if max_articles_input.isdigit() else 10

        await scrape_articles(search_query, max_articles)

if __name__ == "__main__":
    asyncio.run(main())

