import asyncio
import logging
from operator import itemgetter
import time
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def process_txt_proxies_list(r: httpx.Response, take: int = None) -> list[str]:
    result = []
    for i, line in enumerate(r.text.splitlines()):
        p = line.strip()
        if not p or p.startswith("#"):
            continue

        if not p.startswith("http"):
            p = "http://" + p
        result.append(p)
        if take is not None and i >= take:
            break
    return result


def process_json_proxies_list(r: httpx.Response, take: int = None) -> list[str]:
    data = r.json()
    items = _extract_items(data=data)
    proxies = []
    for item in items:
        if take is not None and len(proxies) >= take:
            break
        if isinstance(item, dict):
            proxy = _extract_proxy(item)
            if proxy:
                proxies.append(proxy)
    return proxies


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


async def load_proxies(proxy_list_url: str, take: int = None) -> list[str]:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(proxy_list_url)
        r.raise_for_status()

    if proxy_list_url.endswith(".txt"):
        return process_txt_proxies_list(r=r, take=take)
    elif proxy_list_url.endswith(".json"):
        return process_json_proxies_list(r=r, take=take)
    else:
        logger.critical("VALUE ERROR: Invalid proxy list file extension is not supported!")
        raise ValueError(f"Разрешение вашего файла с прокси не поддерживается текущим проектом!\n"
                         f"Попробуйте найти файлы с разрешениями .json/.txt и попробуйте снова.")


def make_client(proxy, timeout):
    return httpx.AsyncClient(
        proxy=proxy,
        timeout=timeout,
        verify=False,
    )


async def check(proxy: str, idx: int, timeout: int, bot_url: str) -> tuple[str, float] | None:
    started = time.perf_counter()

    try:
        async with make_client(proxy, timeout) as client:
            response = await client.get(bot_url)

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


async def run(
        bot_url: str,
        concurrency: int,
        timeout: int,
        proxies: list[str],
        limit: int = None
) -> list[tuple[str, float]]:
    sem = asyncio.Semaphore(concurrency)

    total = len(proxies)
    done = 0
    ok_num = 0
    ok = []

    t0 = time.perf_counter()

    async def worker(i, p):
        async with sem:
            return await check(p, i, timeout, bot_url)

    tasks = [
        asyncio.create_task(worker(i, p))
        for i, p in enumerate(proxies, 1)
    ]

    for t in asyncio.as_completed(tasks):
        res = await t
        done += 1

        if res:
            ok.append(res)
            ok_num += 1
            if limit is not None and ok_num >= limit:
                break

        if done % 20 == 0 or done == total:
            dt = time.perf_counter() - t0
            speed = done / dt if dt else 0

            logger.info(f"[progress] {done}/{total} {done / total * 100:.1f}% ok={len(ok)} {speed:.1f}/sec")

    return ok


async def main(
        bot_url: str,
        proxy_list_url: str,
        take: int = None,
        limit: int = None,
        top: bool = False,
        timeout: int = 5,
        concurrency: int = 100,
):
    proxies = await load_proxies(proxy_list_url=proxy_list_url, take=take)

    logger.info(f"loaded: {len(proxies)}")

    res = await run(proxies=proxies, limit=limit, concurrency=concurrency, timeout=timeout, bot_url=bot_url)
    if top:
        res = sorted(res, key=itemgetter(1))
    with open("../../working_proxies.txt", "w", encoding="utf-8") as f:
        f.writelines(f"{p}\n" for p, _ in res)

    logger.info(f"working: {len(res)}")
