/// not working 
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse
from pyppeteer import launch
from pyppeteer_stealth import stealth
from fake_useragent import UserAgent
from faker import Faker
import random
from ip2geotools.databases.noncommercial import DbIpCity
import aiohttp
from aiohttp_proxy import ProxyConnector
import requests
import pyppeteer.errors
import re
import faulthandler
from functools import wraps
import argparse
import backoff

# Setup logging
log_file = 'app.log'
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configure file logger
file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)  # 10 MB max file size, 5 backup files
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Configure console logger
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.ERROR)

# Create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Enable faulthandler
faulthandler.enable()

languages = [
    "en-US", "fr-FR", "de-DE", "es-ES", "it-IT", "ja-JP", "zh-CN", "pt-BR", "ru-RU", "ar-SA",
]

resolutions = [
    (1920, 1080), (1366, 768), (1280, 720),
]

def validate_url(url):
    parsed_url = urlparse(url)
    is_valid = all([parsed_url.scheme, parsed_url.netloc])
    logger.info(f"URL validation: {url} - {'Valid' if is_valid else 'Invalid'}")
    return is_valid

def parse_proxy(proxy_entry):
    pattern = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)(?::[A-Za-z]{2})?')
    match = pattern.match(proxy_entry)
    if match:
        ip = match.group(1)
        port = match.group(2)
        country = match.group(3) if match.lastindex == 3 else None
        return ip, port, country
    return None

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
def scrape_proxies(url):
    proxies = []
    try:
        response = requests.get(url, timeout=10)
        logger.debug(f"Scraping proxies from {url}. Status code: {response.status_code}")
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            for line in lines:
                parsed_proxy = parse_proxy(line.strip())
                if parsed_proxy:
                    ip, port, country = parsed_proxy
                    proxy = f"{ip}:{port}"
                    if country:
                        proxy += f":{country}"
                    proxies.append(proxy)
            logger.debug(f"Scraped {len(proxies)} proxies from {url}")
        else:
            logger.warning(f"Failed to scrape proxies from {url}. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping proxies from {url}: {str(e)}")
    return proxies

async def refresh_proxies(proxy_sources, known_good_proxies, proxy_refresh_interval):
    while True:
        proxies = []
        for source in proxy_sources:
            source_proxies = scrape_proxies(source)
            proxies.extend(source_proxies)
            logger.debug(f"Scraped {len(source_proxies)} proxies from {source}")

        if proxies:
            logger.info(f"Refreshing proxy list. Total proxies: {len(proxies)}")
            known_good_proxies.clear()
            known_good_proxies.extend(proxies)
        else:
            logger.warning("No proxies found during refresh.")

        await asyncio.sleep(proxy_refresh_interval)

def retry(max_retries, delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except (pyppeteer.errors.NetworkError, pyppeteer.errors.TimeoutError, pyppeteer.errors.PageError, pyppeteer.errors.ProtocolError) as e:
                    retries += 1
                    logger.error(f"Error - {str(e)} (Retry {retries}/{max_retries})")
                    if retries >= max_retries:
                        raise
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

@retry(max_retries=3)
async def perform_task(url, page, proxy, task_number, timeout):
    try:
        ua = UserAgent()
        user_agent = ua.random
        language = random.choice(languages)
        faker = Faker()
        referrer = faker.uri()
        resolution = random.choice(resolutions)

        logger.debug(f"Task {task_number}: Setting user agent to {user_agent}", extra={'proxy': proxy})
        await page.setUserAgent(user_agent)
        logger.debug(f"Task {task_number}: Setting Accept-Language to {language}", extra={'proxy': proxy})
        await page.setExtraHTTPHeaders({'Accept-Language': language, 'Referer': referrer})
        logger.debug(f"Task {task_number}: Setting viewport to {resolution}", extra={'proxy': proxy})
        await page.setViewport({'width': resolution[0], 'height': resolution[1]})

        logger.debug(f"Task {task_number}: Applying stealth techniques", extra={'proxy': proxy})
        await stealth(page)

        logger.debug(f"Task {task_number}: Navigating to {url}", extra={'proxy': proxy})
        try:
            if not page.isClosed():
                await page.goto(url, {'timeout': timeout * 1000, 'waitUntil': 'networkidle0'})
            else:
                logger.warning(f"Task {task_number}: Page is closed, skipping navigation", extra={'proxy': proxy})
                return False
        except pyppeteer.errors.TimeoutError:
            logger.warning(f"Task {task_number}: Timeout error occurred while navigating to {url}", extra={'proxy': proxy})
            return False
        except pyppeteer.errors.PageError as e:
            logger.error(f"Task {task_number}: Page navigation error - {str(e)}", extra={'proxy': proxy})
            return False
        except pyppeteer.errors.ProtocolError as e:
            logger.error(f"Task {task_number}: Protocol error - {str(e)}", extra={'proxy': proxy})
            return False
        except Exception as e:
            logger.error(f"Task {task_number}: Unexpected error occurred - {str(e)}", extra={'proxy': proxy})
            return False

        if proxy:
            proxy_parts = proxy.split(':')
            ip = proxy_parts[0]
            city = None
            country = None
            if len(proxy_parts) >= 3:
                country = proxy_parts[2]
                try:
                    ip_info = DbIpCity.get(ip, api_key='free')
                    city = ip_info.city
                except Exception as e:
                    logger.warning(f"Error retrieving city information: {str(e)}", extra={'proxy': proxy})
        else:
            ip = city = country = None

        logger.info(f"Task {task_number}: Successfully completed", extra={'proxy': proxy, 'city': city, 'country': country})
        return True
    except (asyncio.TimeoutError, asyncio.CancelledError):
        logger.warning(f"Task {task_number}: Cancelled or timed out", extra={'proxy': proxy})
        return False

def parse_args():
    parser = argparse.ArgumentParser(description='Web Application with Pyppeteer')
    parser.add_argument('--url', type=str, required=True, help='Target site URL')
    return parser.parse_args()

async def main(url, config):
    proxy_sources = [
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/main/https.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt"
    ]

    total_tasks = 0
    total_successful = 0

    if validate_url(url):
        try:
            timeout = aiohttp.ClientTimeout(total=config['timeout'])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    browser = await launch(headless=True, args=['--no-sandbox'])
                except pyppeteer.errors.NetworkError as e:
                    logger.error(f"Error launching browser: {str(e)}")
                    return

                try:
                    known_good_proxies = []  # List to store known good proxies

                    proxy_refresh_task = asyncio.create_task(refresh_proxies(proxy_sources, known_good_proxies, config['proxy_refresh_interval']))

                    semaphore = asyncio.Semaphore(config['max_concurrent_tasks'])

                    while True:
                        page_tasks = []
                        for _ in range(config['batch_size']):
                            proxy = random.choice(known_good_proxies) if known_good_proxies else None

                            async with semaphore:
                                try:
                                    page = await browser.newPage()
                                    await page.setRequestInterception(True)

                                    async def intercept_request(request):
                                        resource_type = request.resourceType
                                        if resource_type in ['image', 'font', 'stylesheet']:
                                            await request.abort()
                                        else:
                                            await request.continue_()

                                    page.on('request', lambda req: asyncio.ensure_future(intercept_request(req)))

                                    if proxy:
                                        connector = ProxyConnector.from_url(f"http://{proxy}")
                                        await page.setProxyConnector(connector)
                                    task_number = total_tasks + len(page_tasks) + 1
                                    page_task = asyncio.create_task(perform_task(url, page, proxy, task_number, config['timeout']))
                                    page_tasks.append(page_task)
                                except (pyppeteer.errors.NetworkError, pyppeteer.errors.PageError) as e:
                                    logger.error(f"Error during page operation: {str(e)}")

                        results = await asyncio.gather(*page_tasks, return_exceptions=True)

                        successful_tasks = sum(1 for result in results if isinstance(result, bool) and result)
                        total_successful += successful_tasks
                        total_tasks += len(page_tasks)

                        logger.info(f"Batch completed. Total tasks performed: {total_tasks}. Total successful: {total_successful}")
                        await asyncio.sleep(config['sleep_interval'])

                except (asyncio.CancelledError, pyppeteer.errors.NetworkError) as e:
                    logger.error(f"Script execution cancelled or network error occurred: {str(e)}")
                finally:
                    proxy_refresh_task.cancel()
                    await proxy_refresh_task
                    logger.info("Closing browser...")
                    if not browser.isClosed():
                        await browser.close()
                    logger.info("Browser closed.")
        except (asyncio.CancelledError, aiohttp.ClientError) as e:
            logger.error(f"Script execution cancelled or client error occurred: {str(e)}")
    else:
        logger.error(f"Invalid URL: {url}")

if __name__ == "__main__":
    try:
        args = parse_args()
        config = {
            "batch_size": 50,
            "sleep_interval": 20.0,
            "timeout": 60.0,  # Increased timeout value
            "max_concurrent_tasks": 10,
            "proxy_refresh_interval": 1800
        }

        asyncio.run(main(args.url, config))
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
