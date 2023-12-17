import requests
import os
import json
import time
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from tkinter.filedialog import askdirectory
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GithubScraper:
    def __init__(self, query, output_dir, api_key, rate_limit_threshold=10, delay=5):
        self.query = query
        self.base_url = 'https://api.github.com/search/users?'
        self.api_key = api_key
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {self.api_key}'
        }
        self.output_dir = output_dir
        self.rate_limit_threshold = rate_limit_threshold
        self.delay = delay

    def fetch_users(self):
        params = {'q': self.query, 'per_page': 30}
        users = []

        while True:
            logger.info(f"Fetching page: {params.get('page', 1)}")
            try:
                response = requests.get(self.base_url + urlencode(params), headers=self.headers, timeout=10)
                response.raise_for_status()
                self.check_rate_limit(response)
                data = response.json()
                users.extend(data['items'])
                logger.info(f"Fetched {len(data['items'])} users")

                if 'next' not in response.links:
                    break

                params['page'] = params.get('page', 1) + 1
                time.sleep(self.delay)

            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                break
            except requests.exceptions.Timeout as e:
                logger.error(f"Request timed out: {e}")
                break
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching data: {e}")
                break

        return users

    def fetch_and_parse_user_details(self, users):
        for index, user in enumerate(users):
            profile_url = user['html_url']
            logger.info(f"Processing user {index + 1}/{len(users)}: {profile_url}")
            try:
                response = requests.get(profile_url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                follower_link = soup.select_one('li.vcard-detail:nth-child(2) > a:nth-child(2)')
                if follower_link:
                    follower_count = follower_link.text.strip()
                    user['follower_count'] = follower_count
                else:
                    user['follower_count'] = 'N/A'

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching user details for {profile_url}: {e}")
                user['follower_count'] = 'Error'

            time.sleep(self.delay)
        return users

    def save_users(self, users):
        file_path = os.path.join(self.output_dir, 'github_users.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
        logger.info(f"Saved {len(users)} users to {file_path}")

    def check_rate_limit(self, response):
        rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        if rate_limit_remaining < self.rate_limit_threshold:
            sleep_time = 60  # in seconds
            logger.info(f"Approaching rate limit. Sleeping for {sleep_time} seconds.")
            time.sleep(sleep_time)

def parse_arguments():
    parser = argparse.ArgumentParser(description='GitHub Scraper')
    parser.add_argument('query', help='GitHub search query')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arguments()
    api_key = input("Enter your GitHub API key: ")
    output_dir = askdirectory(title='Choose Directory to Save Information')
    scraper = GithubScraper(args.query, output_dir, api_key)
    users = scraper.fetch_users()
    users_with_details = scraper.fetch_and_parse_user_details(users)
    scraper.save_users(users_with_details)

