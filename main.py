import asyncio
import logging
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
URL = f"https://api.telegram.org/bot{TOKEN}/getMe"
PROXY_LIST_URL = os.getenv("PROXY_LIST_URL")

TIMEOUT = 5
CONCURRENCY = 100

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def process_txt_proxies_list(r: httpx.Response) -> list[str]:
    result = []
    for line in r.text.splitlines():
        p = line.strip()

        if not p or p.startswith("#"):
            continue

        if not p.startswith("http"):
            p = "http://" + p
        result.append(p)
    return result


def process_json_proxies_list(r: httpx.Response) -> list[str]:
    data = r.json()
    items = _extract_items(data)
    return [_extract_proxy(item) for item in items if isinstance(item, dict) and _extract_proxy(item)]


def _extract_items(data) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        list_keys = ['data', 'proxies', 'results', 'result', 'list', 'proxy_list', 'proxies_list']
        for key in list_keys:
            if key in data and isinstance(data[key], list):
                return data[key]
        return [data]
    return []


def _extract_proxy(item: dict) -> str | None:
    if 'ip' in item and 'port' in item:
        protocol = item.get('protocol', 'http')
        return f"{protocol}://{item['ip']}:{item['port']}"
    proxy_fields = ['proxy', 'url', 'proxy_url', 'address', 'host']
    for field in proxy_fields:
        proxy = item.get(field)
        if proxy and not proxy.startswith('#'):
            if not proxy or proxy.startswith("#"):
                continue
            if not proxy.startswith("http"):
                proxy = "http://" + proxy
            return proxy

    return None


async def load_proxies() -> list[str]:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(PROXY_LIST_URL)
        r.raise_for_status()

    if PROXY_LIST_URL.endswith(".txt"):
        return process_txt_proxies_list(r=r)
    elif PROXY_LIST_URL.endswith(".json"):
        return process_json_proxies_list(r=r)
    else:
        logger.critical("VALUE ERROR: Invalid proxy list file extension is not supported!")
        raise ValueError(f"Разрешение вашего файла с прокси не поддерживается текущим проектом!\n"
                         f"Попробуйте найти файлы с разрешениями .json/.txt и попробуйте снова.")


def make_client(proxy):
    return httpx.AsyncClient(
        proxy=proxy,
        timeout=TIMEOUT,
        verify=False,
    )


async def check(proxy: str, idx: int) -> tuple[str, float] | None:
    started = time.perf_counter()

    try:
        async with make_client(proxy) as client:
            response = await client.get(URL)

        if response.status_code != 200:
            return None

        if not response.json().get("ok"):
            return None

        elapsed = time.perf_counter() - started

        logger.info(f"[{idx}] {proxy} {elapsed:.2f}s")

        return proxy, elapsed

    except (
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.ProxyError,
            httpx.ConnectError,
    ):
        return None

    except Exception as exc:
        logger.error(f"[{idx}] {exc}")
        return None


async def run(proxies: list[str]) -> list[tuple[str, float]]:
    sem = asyncio.Semaphore(CONCURRENCY)

    total = len(proxies)
    done = 0
    ok = []

    t0 = time.perf_counter()

    async def worker(i, p):
        async with sem:
            return await check(p, i)

    tasks = [
        asyncio.create_task(worker(i, p))
        for i, p in enumerate(proxies, 1)
    ]

    for t in asyncio.as_completed(tasks):
        res = await t
        done += 1

        if res:
            ok.append(res)

        if done % 20 == 0 or done == total:
            dt = time.perf_counter() - t0
            speed = done / dt if dt else 0

            logger.info(f"[progress] {done}/{total} {done / total * 100:.1f}% ok={len(ok)} {speed:.1f}/sec")

    return ok


async def main():
    proxies = await load_proxies()

    logger.info(f"loaded: {len(proxies)}")

    res = await run(proxies)
    with open("working_proxies.txt", "w", encoding="utf-8") as f:
        f.writelines(f"{p}\n" for p, _ in res)

    logger.info(f"working: {len(res)}")


if __name__ == "__main__":
    asyncio.run(main())
