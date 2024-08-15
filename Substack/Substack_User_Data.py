import os
import re
from typing import Dict, List, Any
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
HEADERS = {
    "User-Agent": os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36")
}

# Create a session
session = requests.Session()
session.headers.update(HEADERS)

def validate_username(username: str) -> bool:
    """
    Validate the Substack username.

    Args:
        username (str): The username to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', username))

def get_user_data(username: str) -> Dict[str, Any]:
    """
    Get user ID and reads from a Substack user's profile.

    Args:
        username (str): The username of the Substack user.

    Returns:
        Dict[str, Any]: A dictionary containing user_id and reads.

    Raises:
        requests.RequestException: If there's an error with the request.
        KeyError: If the response doesn't contain the expected data.
    """
    endpoint = f"https://substack.com/api/v1/user/{username}/public_profile"
    try:
        r = session.get(endpoint, timeout=30)
        r.raise_for_status()
        user_data = r.json()
        
        reads = [
            {
                "publication_id": i["publication"]["id"],
                "publication_name": i["publication"]["name"],
                "subscription_status": i["membership_state"],
            }
            for i in user_data["subscriptions"]
        ]
        
        return {
            "user_id": user_data["id"],
            "reads": reads
        }
    except requests.RequestException as e:
        raise requests.RequestException(f"Error fetching user data: {e}")
    except KeyError as e:
        raise KeyError(f"Expected data not found in response: {e}")

def get_user_likes(user_id: int) -> List[Dict[str, Any]]:
    """
    Get liked posts from a user's profile.

    Args:
        user_id (int): The user ID of the Substack user.

    Returns:
        List[Dict[str, Any]]: A list of liked posts.

    Raises:
        requests.RequestException: If there's an error with the request.
        KeyError: If the response doesn't contain the expected data.
    """
    endpoint = f"https://substack.com/api/v1/reader/feed/profile/{user_id}?types%5B%5D=like"
    try:
        r = session.get(endpoint, timeout=30)
        r.raise_for_status()
        return r.json()["items"]
    except requests.RequestException as e:
        raise requests.RequestException(f"Error fetching user likes: {e}")
    except KeyError as e:
        raise KeyError(f"Likes data not found in response: {e}")

def get_user_notes(user_id: int) -> List[Dict[str, Any]]:
    """
    Get notes and comments posted by a user.

    Args:
        user_id (int): The user ID of the Substack user.

    Returns:
        List[Dict[str, Any]]: A list of notes and comments.

    Raises:
        requests.RequestException: If there's an error with the request.
        KeyError: If the response doesn't contain the expected data.
    """
    endpoint = f"https://substack.com/api/v1/reader/feed/profile/{user_id}"
    try:
        r = session.get(endpoint, timeout=30)
        r.raise_for_status()
        return r.json()["items"]
    except requests.RequestException as e:
        raise requests.RequestException(f"Error fetching user notes: {e}")
    except KeyError as e:
        raise KeyError(f"Notes data not found in response: {e}")

def main():
    while True:
        username = input("Enter a Substack username: ")
        if validate_username(username):
            break
        print("Invalid username. Please use only letters, numbers, underscores, and hyphens.")
    
    try:
        user_data = get_user_data(username)
        user_id = user_data["user_id"]
        reads = user_data["reads"]

        print(f"User ID: {user_id}")

        print("\nUser Reads:")
        for read in reads:
            print(f"- {read['publication_name']} (Status: {read['subscription_status']})")

        likes = get_user_likes(user_id)
        print(f"\nUser Likes: {len(likes)} posts")

        notes = get_user_notes(user_id)
        print(f"User Notes and Comments: {len(notes)} items")

    except requests.RequestException as e:
        print(f"An error occurred while fetching data: {e}")
    except KeyError as e:
        print(f"Error: Unable to retrieve data. The user might not exist or the API response format has changed: {e}")

if __name__ == "__main__":
    main()
