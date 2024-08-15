# Substack User Data Script

This Python script allows you to fetch and display information about a Substack user, including their user ID, the newsletters they read, the number of posts they've liked, and the number of notes/comments they've made.

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/substack-user-data.git
   cd substack-user-data
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project directory with the following content:
   ```
   USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36
   ```

## Usage

Run the script using Python:

```
python substack_user_data.py
```

When prompted, enter a valid Substack username. The script will then fetch and display information about the user's profile.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
