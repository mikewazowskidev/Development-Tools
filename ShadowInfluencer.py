import asyncio
import random
import logging
import argparse
import requests
from pyppeteer import launch
from urllib.parse import urlparse
from fake_useragent import UserAgent
from faker import Faker

# Adjust the logging level
logging.basicConfig(filename='siteviewer.log', level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def siteviewer_log(message, level="info", proxy=None):
    """ Custom logging function for detailed logging. """
    log_message = f"{message}"
    if proxy:
        log_message += f" (Proxy: {proxy})"
    
    if level.lower() == "info":
        logging.info(log_message)
    elif level.lower() == "error":
        logging.error(log_message)
    elif level.lower() == "warning":
        logging.warning(log_message)
    else:
        logging.debug(log_message)

def generate_referrers(num_referrers):
    """ Generate random referrers using Faker. """
    fake = Faker()
    return [fake.url() for _ in range(num_referrers)]

def generate_resolutions(num_resolutions):
    """ Generate random screen resolutions using Faker. """
    fake = Faker()
    return [(fake.random_int(min=800, max=1920), fake.random_int(min=600, max=1080)) for _ in range(num_resolutions)]

def validate_url(url):
    """ Validate the format of the URL. """
    parsed_url = urlparse(url)
    return all([parsed_url.scheme, parsed_url.netloc])

def scrape_proxies_from_urls(urls):
    """ Scrape proxies from multiple URLs with error handling. """
    proxies = []
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            proxies.extend(response.text.split('\n'))
        except requests.RequestException as e:
            siteviewer_log(f"Error scraping proxies from {url}: {e}", "error")
    return [proxy.strip() for proxy in proxies if proxy.strip()]

async def safe_request(url, page, proxy, request_number, referrers, resolutions, max_retries=3):
    """ Perform a safe web request with Pyppeteer and rotate attributes. """
    retries = 0
    while retries < max_retries:
        try:
            ua = UserAgent()
            user_agent = ua.random
            referrer = random.choice(referrers)
            resolution = random.choice(resolutions)

            fake = Faker()
            language = fake.language_code()
            accept_language = f"{language},{language[:2]};q=0.9"

            await page.setUserAgent(user_agent)
            await page.setExtraHTTPHeaders({'Referer': referrer, 'Accept-Language': accept_language})
            await page.setViewport({'width': resolution[0], 'height': resolution[1]})

            await page.goto(url)

            # Generic button selector
            button_selector = "button, a[href]"
            await page.waitForSelector(button_selector)
            await page.click(button_selector)

            siteviewer_log(f"Request {request_number}: Success", proxy=proxy)

            return True

        except Exception as e:
            retries += 1
            await asyncio.sleep(2 ** retries)
            siteviewer_log(f"Request {request_number}: Retry {retries} after error {e}", "error", proxy=proxy)

            if retries >= max_retries:
                return False

def parse_args():
    """ Parse runtime arguments. """
    parser = argparse.ArgumentParser(description='Web Scraping Tool with Pyppeteer')
    parser.add_argument('--batch-size', type=int, default=50, help='Number of requests per batch')
    parser.add_argument('--sleep-interval', type=float, default=20.0, help='Sleep interval between batches')
    return parser.parse_args()

async def main():
    args = parse_args()
    proxy_list_urls = [
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/main/https.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt"
    ]
    proxies = scrape_proxies_from_urls(proxy_list_urls)

    referrers = generate_referrers(50)  # Generate 50 random referrers
    resolutions = generate_resolutions(20)  # Generate 20 random screen resolutions

    browser = await launch(headless=True)

    total_requests = 0
    total_successful = 0

    while True:
        substack_url = input("Enter the Substack URL: ")
        if not validate_url(substack_url):
            siteviewer_log("Invalid URL entered.", "error")
            continue

        batch_size = args.batch_size

        for i in range(batch_size):
            try:
                page = await browser.newPage()
                proxy = random.choice(proxies)
                request_number = total_requests + i + 1

                success = await safe_request(substack_url, page, proxy, request_number, referrers, resolutions, max_retries=3)
                if success:
                    total_successful += 1
            except Exception as e:
                siteviewer_log(f"Error during page operation: {e}", "error")
            finally:
                await page.close()

        total_requests += batch_size
        siteviewer_log(f"Batch completed. Total requests made: {total_requests}. Total successful: {total_successful}")

        await asyncio.sleep(args.sleep_interval)

        if input("Continue with the next batch? (yes/no): ").lower() != 'yes':
            break

    await browser.close()
    siteviewer_log("Script execution completed. Browser closed.")

if __name__ == "__main__":
    asyncio.run(main())
