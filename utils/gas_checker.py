import asyncio
import threading
import time
import random

from web3 import AsyncWeb3, Web3
from web3.middleware import async_geth_poa_middleware
from config import RPC
from settings import CHECK_GWEI, MAX_GWEI
from loguru import logger


last_check = None
last_gas = None
lock = asyncio.Lock()


def get_gas():
    try:
        w3 = Web3(
            Web3.HTTPProvider(random.choice(RPC["ethereum"]["rpc"])),
            # middlewares=[async_geth_poa_middleware],
        )
        gas_price = w3.eth.gas_price
        gwei = w3.from_wei(gas_price, "gwei")

        return gwei
    except Exception as error:
        logger.error(error)

    return float("inf")


async def wait_gas():
    global last_check, last_gas

    if not CHECK_GWEI:
        return

    while True:
        async with lock:
            if last_check is not None and time.time() - last_check < 60:
                if last_gas <= MAX_GWEI:
                    return
                continue

            gas = get_gas()

            last_check = time.time()
            last_gas = gas

        if last_gas <= MAX_GWEI:
            return

        logger.info(f"Current GWEI: {gas} > {MAX_GWEI}")
        await asyncio.sleep(60)


def check_gas(func):
    async def _wrapper(*args, **kwargs):
        if CHECK_GWEI:
            await wait_gas()
        return await func(*args, **kwargs)

    return _wrapper
