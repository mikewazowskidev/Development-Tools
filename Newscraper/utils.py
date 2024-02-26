# utils.py
import os
from fake_useragent import UserAgent

def get_user_agent():
    user_agent = UserAgent()
    return user_agent.random

def create_output_directory(directory_name):
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)

