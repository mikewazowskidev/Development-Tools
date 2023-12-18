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

                # Process and save users after each page
                users_with_details = self.fetch_and_parse_user_details(users)
                self.save_users_incrementally(users_with_details)

                # Reset users list for the next page
                users = []

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
        for user in users:
            profile_url = user['html_url']
            logger.info(f"Processing user: {profile_url}")

            try:
                response = requests.get(profile_url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # Fetching follower count
                follower_link = soup.select_one('li.vcard-detail:nth-child(2) > a:nth-child(2)')
                if follower_link:
                    follower_count = follower_link.text.strip()
                    user['follower_count'] = follower_count
                else:
                    user['follower_count'] = 'N/A'

                # Fetching email address
                email_link = soup.select_one('a[href^="mailto:"]')
                if email_link:
                    email_address = email_link.get('href').replace('mailto:', '')
                    user['email_address'] = email_address
                else:
                    user['email_address'] = 'N/A'

                # Fetching vCard data
                vcard = soup.select_one('.vcard-details')
                if vcard:
                    user['name'] = vcard.select_one('.p-name').text.strip() if vcard.select_one('.p-name') else 'N/A'
                    user['company'] = vcard.select_one('.p-org').text.strip() if vcard.select_one('.p-org') else 'N/A'
                    user['location'] = vcard.select_one('.p-label').text.strip() if vcard.select_one('.p-label') else 'N/A'
                    user['join_date'] = soup.select_one('.join-date').text.strip() if soup.select_one('.join-date') else 'N/A'

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching user details for {profile_url}: {e}")
                # Marking error in each field in case of an exception
                user['follower_count'] = 'Error'
                user['email_address'] = 'Error'
                user['name'] = 'Error'
                user['company'] = 'Error'
                user['location'] = 'Error'
                user['join_date'] = 'Error'

            self.fetch_latest_commits(user)
            time.sleep(self.delay)

        return users

    def fetch_latest_commits(self, user):
        repos_url = f"https://api.github.com/users/{user['login']}/repos"
        try:
            response = requests.get(repos_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            repos = response.json()

            user['latest_commits'] = []
            for repo in repos:
                commits_url = f"https://api.github.com/repos/{user['login']}/{repo['name']}/commits"
                commit_response = requests.get(commits_url, headers=self.headers, timeout=10)
                commit_response.raise_for_status()
                commits = commit_response.json()
                if commits:
                    latest_commit = commits[0]  # assuming the first commit is the latest
                    user['latest_commits'].append({
                        'repo_name': repo['name'],
                        'commit_url': latest_commit['html_url'],
                        'commit_message': latest_commit['commit']['message']
                    })

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching repository details for {user['login']}: {e}")

    def save_users_incrementally(self, users):
        file_path = os.path.join(self.output_dir, 'github_users.json')
        # Check if file exists and read existing data if it does
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_data.extend(users)
        else:
            existing_data = users

        # Save the updated data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

        logger.info(f"Saved incremental data to {file_path}")

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
    # No need to call fetch_and_parse_user_details or save_users here as it's done incrementally
