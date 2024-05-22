import asyncio
import random
import logging
import argparse
import requests
from pyppeteer import launch, errors
from urllib.parse import urlparse
from fake_useragent import UserAgent
from faker import Faker
from tqdm import tqdm
import readline
import atexit
import os

# Adjust the logging level
logging.basicConfig(filename='siteviewer.log', level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

HISTORY_FILE = '.siteviewer_history'
MAX_HISTORY_LENGTH = 100

# Setup auto-completion and history
def setup_readline():
    if os.path.exists(HISTORY_FILE):
        readline.read_history_file(HISTORY_FILE)
    readline.set_history_length(MAX_HISTORY_LENGTH)
    atexit.register(readline.write_history_file, HISTORY_FILE)
    readline.parse_and_bind("tab: complete")

setup_readline()

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
    proxies = set()
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            proxies.update(response.text.split('\n'))
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

            await page.goto(url, {'waitUntil': 'networkidle2'})

            # Generic button selector
            button_selector = "button, a[href]"
            await page.waitForSelector(button_selector)
            await page.click(button_selector)

            siteviewer_log(f"Request {request_number}: Success", proxy=proxy)
            return True

        except asyncio.TimeoutError as e:
            siteviewer_log(f"Request {request_number}: Timeout error - {str(e)}", "error", proxy=proxy)
        except errors.NetworkError as e:
            siteviewer_log(f"Request {request_number}: Network error - {str(e)}", "error", proxy=proxy)
        except Exception as e:
            siteviewer_log(f"Request {request_number}: Unexpected error - {str(e)}", "error", proxy=proxy)
        
        retries += 1
        await asyncio.sleep(2 ** retries)

    return False

async def main_task(substack_url, batch_size, referrers, resolutions, proxies):
    """ Main task for running the web scraping process in batches. """
    browser = await launch(headless=True, args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])

    total_requests = 0
    total_successful = 0

    try:
        tasks = []
        semaphore = asyncio.Semaphore(10)  # Limit concurrent requests

        async def bound_request(i):
            async with semaphore:
                page = await browser.newPage()
                proxy = random.choice(proxies)
                request_number = total_requests + i + 1

                try:
                    success = await safe_request(substack_url, page, proxy, request_number, referrers, resolutions, max_retries=3)
                    if success:
                        return True
                except Exception as e:
                    siteviewer_log(f"Error during page operation: {e}", "error")
                finally:
                    await page.close()

        with tqdm(total=batch_size, unit='request', desc='Progress') as progress_bar:
            for i in range(batch_size):
                tasks.append(bound_request(i))

            for f in asyncio.as_completed(tasks):
                result = await f
                if result:
                    total_successful += 1
                total_requests += 1
                progress_bar.update(1)

        siteviewer_log(f"Batch completed. Total requests made: {total_requests}. Total successful: {total_successful}")

    finally:
        await browser.close()
        siteviewer_log("Browser closed.")

    return total_requests, total_successful

def parse_args():
    """ Parse runtime arguments. """
    parser = argparse.ArgumentParser(description='Web Scraping Tool with Pyppeteer')
    parser.add_argument('--batch-size', type=int, default=50, help='Number of requests per batch')
    parser.add_argument('--sleep-interval', type=float, default=20.0, help='Sleep interval between batches')
    return parser.parse_args()

def run_main():
    """ Run the main function with proper event loop management. """
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

    while True:
        substack_url = input("Enter the Substack URL: ")
        if not validate_url(substack_url):
            siteviewer_log("Invalid URL entered.", "error")
            continue

        try:
            total_requests, total_successful = asyncio.run(main_task(substack_url, args.batch_size, referrers, resolutions, proxies))
            siteviewer_log(f"Total requests made: {total_requests}. Total successful: {total_successful}")
        except RuntimeError as e:
            if str(e) == "This event loop is already running":
                loop = asyncio.get_event_loop()
                total_requests, total_successful = loop.run_until_complete(main_task(substack_url, args.batch_size, referrers, resolutions, proxies))
                siteviewer_log(f"Total requests made: {total_requests}. Total successful: {total_successful}")
            else:
                raise

        if input("Continue with the next batch? (yes/no): ").lower() != 'yes':
            break

if __name__ == "__main__":
    run_main()
