import asyncio
import random
import logging
import argparse
import requests
from pyppeteer import launch
from urllib.parse import urlparse

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

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; U; Android 9; en-US; Redmi Note 5 Pro Build/PKQ1.180904.001) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)",
    "Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/73.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/88.0.705.50"
]

languages = [
    "en-US", "fr-FR", "de-DE", "es-ES", "it-IT", "ja-JP", "zh-CN", "pt-BR", "ru-RU", "ar-SA",
    # Add more languages as needed
]

referrers = [
    "https://www.google.com",  # Global search engine
    "https://www.bing.com",  # Microsoft's search engine
    "https://www.yahoo.com",  # Combines search and news
    "https://www.duckduckgo.com",  # Privacy-focused search engine
    "https://www.baidu.com",  # Primary search engine in China
    "https://www.yandex.ru",  # Russian search engine
    "https://www.naver.com",  # South Korean search platform
    "https://www.bing.co.uk",  # UK version of Bing
    "https://www.google.fr",  # French version of Google
    "https://www.google.de",  # German version of Google
    "https://annehelen.substack.com/",  # Cultural and political commentary
    "https://jessicareedkraus.substack.com/",  # Various topic commentary
    "https://theisolationjournals.substack.com/",  # Personal development focus
    "https://wethefifth.substack.com/",  # Political and free speech focus
    "https://mg1.substack.com",  # Specific focus unknown
    "https://www.blockedandreported.org/",  # Social and cultural issues
    "https://www.blackbirdspyplane.com/",  # Fashion and culture
    "https://newsletter.pragmaticengineer.com",  # Software engineering insights
    "https://www.semianalysis.com/",  # Tech industry analysis
    "https://blog.bytebytego.com/",  # Software engineering and problem-solving
    "https://www.computerenhance.com/",  # AI and tech advancements
    "https://www.sina.com.cn",  # Chinese news website
    "https://www.sohu.com",  # Chinese news and media
    "https://www.qq.com",  # Chinese news and social network
    "https://www.163.com",  # Chinese news website
    "https://www.ifeng.com",  # Chinese news and media
    "https://www.xinhuanet.com",  # Chinese state news agency
    "https://www.people.com.cn",  # Official CCP newspaper
    "https://www.cctv.com",  # Chinese national TV broadcaster
    "https://www.cs.com.cn",  # Chinese financial news
    "https://www.cri.cn",  # China Radio International
    "https://www.china.com.cn",  # Chinese government news portal
    "https://www.gmw.cn",  # State-run Chinese newspaper
    "https://www.substack.com",  # Platform for independent writers
    "https://www.edu.cn",  # Chinese education network
    "https://www.zju.edu.cn",  # Zhejiang University
    "https://www.tsinghua.edu.cn",  # Tsinghua University
    "https://www.pku.edu.cn",  # Peking University
    "https://www.fudan.edu.cn",  # Fudan University
    "https://www.sjtu.edu.cn",  # Shanghai Jiao Tong University
    "https://www.bnu.edu.cn",  # Beijing Normal University
    "https://www.theguardian.com",  # International news and media
    "https://www.nytimes.com",  # American news
    "https://www.bbc.com",  # UK and international news
    "https://www.aljazeera.com",  # Middle East-focused news
    "https://www.rt.com",  # Russian international news network
    "https://www.nhk.or.jp",  # Japanese public broadcasting
    "https://www.lemonde.fr",  # French news
    "https://www.dw.com",  # German news and analysis
    "https://www.reuters.com",  # International news agency
    "https://www.apnews.com",  # Associated Press news agency
    "https://www.economist.com",  # International news and business
    "https://www.ft.com",  # Financial Times
    "https://www.bloomberg.com",  # Business and markets news
    "https://www.wsj.com",  # Wall Street Journal
    "https://www.cnbc.com",  # Business and financial news
    "https://www.talkingpointsmemo.substack.com",  # Political analysis
    "https://www.nationalreview.com",  # Conservative news and commentary
    "https://www.vox.com",  # General news with explanatory journalism
    "https://www.wired.com",  # Technology and science news
]

resolutions = [
    (1920, 1080), (1366, 768), (1280, 720),
    # Add more resolutions as needed
]

def validate_url(url):
    """ Validate the format of the URL. """
    parsed_url = urlparse(url)
    return all([parsed_url.scheme, parsed_url.netloc])

def scrape_proxies_from_url(url):
    """ Scrape proxies directly from a given URL with error handling. """
    try:
        response = requests.get(url)
        response.raise_for_status()
        proxies = response.text.split('\n')
        return [proxy.strip() for proxy in proxies if proxy.strip()]
    except requests.RequestException as e:
        siteviewer_log(f"Error scraping proxies: {e}", "error")
        return []

async def safe_request(url, page, proxy, request_number, max_retries=3):
    """ Perform a safe web request with Pyppeteer and rotate attributes. """
    retries = 0
    while retries < max_retries:
        try:
            user_agent = random.choice(user_agents)
            language = random.choice(languages)
            referrer = random.choice(referrers)
            resolution = random.choice(resolutions)

            await page.setUserAgent(user_agent)
            await page.setExtraHTTPHeaders({'Accept-Language': language, 'Referer': referrer})
            await page.setViewport({'width': resolution[0], 'height': resolution[1]})

            await page.goto(url)

            # Generic button selector
            button_selector = "button, a[href]"
            await page.waitForSelector(button_selector)
            await page.click(button_selector)

            siteviewer_log(f"Request {request_number}: Success")

            return True

        except Exception as e:
            retries += 1
            await asyncio.sleep(2 ** retries)
            siteviewer_log(f"Request {request_number}: Retry {retries} after error {e}", "error")

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
    proxy_list_url = "https://raw.githubusercontent.com/Bob-Bragg/Tools/main/httpproxies8.txt"
    proxies = scrape_proxies_from_url(proxy_list_url)

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

                success = await safe_request(substack_url, page, proxy, request_number, max_retries=3)
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
    asyncio.get_event_loop().run_until_complete(main())
