import asyncio
from dotenv import load_dotenv

load_dotenv()

from httpx_service import main
from settings import *

if __name__ == "__main__":
    asyncio.run(main(
        proxy_list_url=PROXY_LIST_URL,
        timeout=TIMEOUT,
        concurrency=CONCURRENCY,
        bot_url=BOT_URL
    ))
