import asyncio
from scraper import scrape_articles, scrape_proxies_from_url

proxy_list_url = "https://raw.githubusercontent.com/Bob-Bragg/Tools/main/httpproxies28.txt"

def display_menu():
    print("\nThreatscape Miner")
    print("1. Run a Google News Query")
    print("2. Exit")

async def main():
    proxies = scrape_proxies_from_url(proxy_list_url)

    while True:
        display_menu()
        choice = input("Enter your choice: ")

        if choice == "1":
            search_query = input("Enter your search query: ")
            max_articles_input = input("Enter the maximum number of articles to scrape (default 10): ")
            max_articles = int(max_articles_input) if max_articles_input.isdigit() else 10

            await scrape_articles(search_query, max_articles, proxies)

        elif choice == "2":
            print("Exiting Newscraper CLI.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())
