import asyncio
import random

from loguru import logger


async def sleep(account_id, address, sleep_from: int, sleep_to: int):
    sleep_time = random.randint(sleep_from, sleep_to)
    logger.info(f"[{account_id}][{address}] Sleeping for {sleep_time} seconds")
    await asyncio.sleep(sleep_time)
