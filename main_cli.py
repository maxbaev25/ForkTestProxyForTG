import os

from dotenv import load_dotenv

load_dotenv()

import asyncio
from datetime import datetime, timedelta
from typing import Annotated, Optional
import typer
from typer import Typer, Option, Argument
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from httpx_service import main
from settings import *

app = Typer()


@app.command(
    short_help="Allows to get working proxy list",
    help="Allows to get working proxy list on your Telegram bot from proxy list URL",
)
def main_cmd(
        proxy_list_url: Annotated[str, Argument(
            help="URL of the proxy list source"
        )],
        take: Annotated[int, Option(
            "-t", "--take", help="Number of proxies to fetch from the source for testing (default: all)"
        )] = None,
        limit: Annotated[int, Option(
            "-l", "--limit",
            help="Maximum number of working proxies to keep in the final list (default: all working)"
        )] = None,
        top: Annotated[bool, Option(
            "--top", help="Sort working proxies by response time (fastest first). Default: no sorting"
        )] = False,
):

    asyncio.run(main(
        proxy_list_url=proxy_list_url, take=take, limit=limit, top=top,
        bot_url=BOT_URL, concurrency=CONCURRENCY, timeout=TIMEOUT))

if __name__ == '__main__':
    app()
