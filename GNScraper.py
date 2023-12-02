import os
import asyncio
from googlesearch import search
from pyppeteer import launch
from pyppeteer.errors import NetworkError, PageError
import websockets.exceptions
from datetime import datetime

# User agent to mimic Google bot
user_agent = (
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
)

# Create a directory to save the articles
output_directory = "Saved_Articles"
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Function to scrape and save an article with retries
async def scrape_and_save_article(link, idx, search_query, max_retries=3):
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

            # Extract the article title from the page
            title_element = await page.querySelector("your-title-selector")  # Replace with the actual selector
            if title_element:
                article_title = await title_element.evaluate('(element) => element.textContent')
                # Remove invalid characters from the title to create a valid filename
                valid_title = ''.join(char for char in article_title if char.isalnum() or char.isspace())
            else:
                valid_title = "UnknownTitle"

            # Create a filename with a timestamp, search query, and the article index
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = os.path.join(output_directory, f"{timestamp}_{search_query}_{valid_title}_{idx + 1}.html")

            # Save the entire HTML content to the custom-named file
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(page_content)

            print(f"Article {idx + 1} saved: {file_name}")
            return  # Successfully scraped, exit retry loop
        except (NetworkError, PageError, websockets.exceptions.ConnectionClosedError) as e:
            print(f"Retrying (attempt {retry + 1}) - {str(e)}")
            # Add a delay before the next retry
            await asyncio.sleep(5)  # Adjust the delay time as needed
        except Exception as e:
            print(f"Failed to scrape and save article {idx + 1}: {str(e)}")
        finally:
            try:
                await browser.close()
            except Exception as e:
                print(f"Error closing browser: {str(e)}")

    print(f"Failed to scrape and save article {idx + 1} after {max_retries} retries.")

# Function to perform the scraping process
async def scrape_articles(search_query):
    # Get search results from Google News
    search_results = search(query=search_query, tld='com', lang='en', num=10, stop=10, pause=2.0, extra_params={'tbm': 'nws'})

    # Run the scraping function for each article link in parallel
    tasks = []
    for idx, link in enumerate(search_results):
        print(f"Scraping article {idx + 1}...")
        tasks.append(scrape_and_save_article(link, idx, search_query))
    await asyncio.gather(*tasks)

# Main loop for user interaction
while True:
    search_query = input("Enter your search query (or 'exit' to quit): ")
    
    if search_query.lower() == 'exit':
        break  # Exit the loop if the user enters 'exit'
    
    # Perform scraping for the entered search query
    asyncio.get_event_loop().run_until_complete(scrape_articles(search_query))

print("Scraping completed.")
