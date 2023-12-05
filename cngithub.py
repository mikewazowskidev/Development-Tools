import asyncio
import requests
import json
import os
import sys
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

loading_chars = ["/", "-", "\\", "|"]

def display_loading_animation(duration=2):
    end_time = time.time() + duration
    while time.time() < end_time:
        for char in loading_chars:
            sys.stdout.write(f"\r{char} Loading...")
            sys.stdout.flush()
            time.sleep(0.2)
    print()

def display_menu():
    # ASCII Art for the header
    header = """
    ░██████╗░██╗████████╗██╗░░██╗██╗░░░██╗██████╗░  ██╗░░░██╗░█████╗░░█████╗░██████╗░██████╗░
    ██╔════╝░██║╚══██╔══╝██║░░██║██║░░░██║██╔══██╗  ██║░░░██║██╔══██╗██╔══██╗██╔══██╗██╔══██╗
    ██║░░██╗░██║░░░██║░░░███████║██║░░░██║██████╦╝  ╚██╗░██╔╝██║░░╚═╝███████║██████╔╝██║░░██║
    ██║░░╚██╗██║░░░██║░░░██╔══██║██║░░░██║██╔══██╗  ░╚████╔╝░██║░░██╗██╔══██║██╔══██╗██║░░██║
    ╚██████╔╝██║░░░██║░░░██║░░██║╚██████╔╝██████╦╝  ░░╚██╔╝░░╚█████╔╝██║░░██║██║░░██║██████╔╝
    ░╚═════╝░╚═╝░░░╚═╝░░░╚═╝░░╚═╝░╚═════╝░╚═════╝░  ░░░╚═╝░░░░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░
    """

    # Menu options
    menu_options = """
    [1] Scrape GitHub Profiles
    [2] Login with Personal Access Token
    [3] Exit
    """

    print(header)
    print(menu_options)

class GithubUser:
    def __init__(self, user_data):
        self.username = user_data['login']
        self.name = user_data.get('name')
        self.profile_url = user_data['html_url']
        self.location = user_data.get('location')
        # Add more attributes as needed

async def fetch_users_from_github(query, token=None):
    url = f"https://api.github.com/search/users?q={query}&per_page=100"
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {token}' if token else None
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to fetch data: {response.status_code}")
        return []

    data = response.json()
    return data['items']

async def scrape_github_profiles_from_china(token=None):
    users_data = await fetch_users_from_github('location:China', token)
    profiles = [GithubUser(user_data) for user_data in users_data]
    return {profile.username: vars(profile) for profile in profiles}

def save_profiles_to_json(profile_links, filename="github_users_china.json"):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(profile_links, file, indent=4)

async def main():
    token = None
    while True:
        display_menu()
        choice = input("Enter your choice (1-3): ")

        if choice == '1':
            logger.info("Starting scraping process...")
            display_loading_animation(duration=5)
            try:
                profile_links = await scrape_github_profiles_from_china(token)
                save_profiles_to_json(profile_links)
                logger.info(f"Scraping completed. {len(profile_links)} profiles saved to JSON.")
            except Exception as e:
                logger.error(f"Scraping process failed: {e}")
        elif choice == '2':
            token = input("Enter your Personal Access Token: ")
            logger.info("Token set successfully.")
        elif choice == '3':
            logger.info("Exiting the program.")
            break
        else:
            logger.warning("Invalid choice. Please enter a number between 1 and 3.")

if __name__ == "__main__":
    asyncio.run(main())

