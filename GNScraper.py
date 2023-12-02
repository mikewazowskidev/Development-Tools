import os
import asyncio
from googlesearch import search
from pyppeteer import launch
from pyppeteer.errors import NetworkError, PageError

# User agent to mimic Google bot
user_agent = (
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
)

# Create a directory to save the articles
output_directory = "Saved_Articles"
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Function to scrape and save an article with retries
async def scrape_and_save_article(link, idx, max_retries=3):
    for retry in range(max_retries):
        try:
            browser = await launch(headless=True)
            page = await browser.newPage()

            # Set user agent to mimic Google bot
            await page.setUserAgent(user_agent)

            await page.goto(link)

            # Reduce wait time for page loads and selectors if the website is fast
            await asyncio.sleep(2)  # Adjust the sleep time as needed

            # Get the entire HTML content of the page
            page_content = await page.content()

            # Save the entire HTML content to a text file
            file_name = os.path.join(output_directory, f"article_{idx + 1}.html")
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(page_content)

            print(f"Article {idx + 1} saved: {file_name}")
            return  # Successfully scraped, exit retry loop
        except (NetworkError, PageError) as e:
            print(f"Retrying (attempt {retry + 1}) - {str(e)}")
        except Exception as e:
            print(f"Failed to scrape and save article {idx + 1}: {str(e)}")
        finally:
            await browser.close()

    print(f"Failed to scrape and save article {idx + 1} after {max_retries} retries.")

# Prompt the user for a search query
search_query = input("Enter your search query: ")

# Get search results from Google News
search_results = search(query=search_query, tld='com', lang='en', num=10, stop=10, pause=2.0, extra_params={'tbm': 'nws'})

# Run the scraping function for each article link in parallel
async def main():
    tasks = []
    for idx, link in enumerate(search_results):
        print(f"Scraping article {idx + 1}...")
        tasks.append(scrape_and_save_article(link, idx))
    await asyncio.gather(*tasks)

# Run the scraping tasks asynchronously
asyncio.get_event_loop().run_until_complete(main())

print("Scraping completed.")
