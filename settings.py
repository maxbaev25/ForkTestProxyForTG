import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
BOT_URL = f"https://api.telegram.org/bot{TOKEN}/getMe"
PROXY_LIST_URL = os.getenv("PROXY_LIST_URL")
TIMEOUT = int(os.getenv("TIMEOUT"))
CONCURRENCY = int(os.getenv("CONCURRENCY"))
