from dotenv import load_dotenv

load_dotenv()

import asyncio
from typing import Annotated
from typer import Typer, Option, Argument
from .httpx_service import main

app = Typer()


@app.command(
    short_help="Allows to get working proxy list",
    help="Allows to get working proxy list on your Telegram bot from proxy list URL",
)
def main_cmd(
        proxy_list_url: Annotated[str, Argument(
            help="URL of the proxy list source"
        )],
        token: Annotated[str, Argument(
            help="Telegram bot token"
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
        concurrency: Annotated[int, Option(
            "-c", "--concurrency", help="Concurrency of requests"
        )] = 100,
        timeout: Annotated[int, Option(
            "--timeout", help="Timeout of every request in seconds"
        )] = 5,
        path: Annotated[str, Option(
            "-p", "--path", help="Filepath where to save working proxies list (default: current directory)"
        )] = ".",
):
    bot_url = f"https://api.telegram.org/bot{token}/getMe"
    asyncio.run(main(
        proxy_list_url=proxy_list_url, take=take, limit=limit, top=top,
        bot_url=bot_url, concurrency=concurrency, timeout=timeout, file_path=path))


def main_func():
    app()
