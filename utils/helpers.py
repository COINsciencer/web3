import random
import traceback
from loguru import logger
from settings import (
    ENABLE_ERROR_TRACEBACK,
    RETRIES,
    RETRY_DELAY_MIN,
    RETRY_DELAY_MAX,
)
from asyncio import sleep
from config import AUTOMATIC_MODE


def retry(func):
    async def wrapper(*args, **kwargs):
        retries = 0
        while retries <= RETRIES:
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Error | {e}")
                if str(e).startswith("520, "):
                    logger.error(
                        f"Probably an rpc error, I am not increasing the retry count"
                    )
                else:
                    retries += 1
                    if AUTOMATIC_MODE.get():
                        raise e

                if ENABLE_ERROR_TRACEBACK:
                    traceback.print_exc()

                if retries <= RETRIES:
                    logger.info(f"Retrying... {retries}/{RETRIES}")
                    await sleep(random.randint(RETRY_DELAY_MIN, RETRY_DELAY_MAX))

    return wrapper
