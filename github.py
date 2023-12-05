import requests
import os
import json
from urllib.parse import urlencode
from tkinter.filedialog import askdirectory

class GithubScraper:
    def __init__(self, query):
        self.query = query
        self.base_url = 'https://api.github.com/search/users?'
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
        }
        self.path = askdirectory(title='Choose Directory to Save Information')

    def fetch_users(self):
        params = {'q': self.query, 'per_page': 30}  # Lower per_page due to rate limit
        users = []

        while True:
            response = requests.get(self.base_url + urlencode(params), headers=self.headers)
            if response.status_code != 200:
                print(f"Failed to fetch data: {response.status_code}")
                break

            data = response.json()
            users.extend(data['items'])
            print(f"Fetched {len(data['items'])} users")

            if 'next' not in response.links:
                break

            params['page'] = params.get('page', 1) + 1

        return users

    def save_users(self, users):
        file_path = os.path.join(self.path, 'github_users_china.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(users)} users to {file_path}")

if __name__ == '__main__':
    scraper = GithubScraper('location:China')
    users = scraper.fetch_users()
    scraper.save_users(users)

