import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import traceback
import tracemalloc

from loguru import logger

import questionary
from questionary import Choice
from datetime import datetime

from config import OKX_ADDRESSES, WALLETS
from settings import (
    ENABLE_ERROR_TRACEBACK,
    MAX_SLEEP_BEFORE_ACCOUNT_START,
    MIN_SLEEP_BEFORE_ACCOUNT_START,
    RANDOM_WALLET,
    THREADS,
)
from modules_settings import *
from utils.gas_checker import check_gas
from utils.sleeping import sleep


def get_module():
    choices = [
        Choice(f"{i}) {key}", value)
        for i, (key, value) in enumerate(
            {
                "AUTOMATION MODE": automatic,
                "Deposit to Scroll": deposit_scroll,
                "Withdraw from Scroll": withdraw_scroll,
                "OKX Withdraw": okx_withdraw,
                "OKX Deposit": okx_deposit,
                "Wrap ETH": wrap_eth,
                "Unwrap ETH": unwrap_eth,
                "Bridge Orbiter": bridge_orbiter,
                "Bridge Layerswap": bridge_layerswap,
                "Bridge Nitro": bridge_nitro,
                "Swap on Skydrome": swap_skydrome,
                "Swap on Zebra": swap_zebra,
                "Swap on SyncSwap": swap_syncswap,
                "Swap on XYSwap": swap_xyswap,
                "Deposit LayerBank": deposit_layerbank,
                "Deposit Aave": deposit_aave,
                "Withdraw LayerBank": withdraw_layerbank,
                "Withdraw Aave": withdraw_aave,
                "Mint and Bridge Zerius NFT": mint_zerius,
                "Mint L2Pass NFT": mint_l2pass,
                "Mint ZkStars NFT": mint_zkstars,
                "Create NFT collection on Omnisea": create_omnisea,
                "RubyScore Vote": rubyscore_vote,
                "Send message L2Telegraph": send_message,
                "Mint and bridge NFT L2Telegraph": bridge_nft,
                "Mint NFT on NFTS2ME": mint_nft,
                "Mint Scroll Origins NFT": nft_origins,
                "Dmail sending mail": send_mail,
                "Create gnosis safe": send_message,
                "Deploy contract": deploy_contract,
                "Exit": "exit",
            }.items(),
            start=1,
        )
    ]
    result = questionary.select(
        "Select a method to get started",
        choices=choices,
        qmark="🛠 ",
        pointer="✅ ",
    ).ask()
    if result == "exit":
        sys.exit()
    return result


@check_gas
async def run_module(module, account_id, key, okx_address):
    await module(account_id, key, okx_address)


async def run_group(module, group, group_id, start_id):
    for i, account in enumerate(group):
        if start_id != 0:
            await sleep(
                account_id=start_id + i + 1,
                address="",
                sleep_from=MIN_SLEEP_BEFORE_ACCOUNT_START,
                sleep_to=MAX_SLEEP_BEFORE_ACCOUNT_START,
            )
        try:
            await run_module(
                module=module,
                account_id=start_id + i + 1,
                key=account[0],
                okx_address=account[1],
            )
        except Exception as e:
            if ENABLE_ERROR_TRACEBACK:
                logger.error(
                    f"[group - {group_id}][account - {start_id + i + 1}] Error - {e}, Traceback:\n {traceback.format_exc()}"
                )
            else:
                logger.error(
                    f"[group - {group_id}][account - {start_id + i + 1}] Error - {e}"
                )


def _generate_groups():
    global THREADS

    data = list(zip(WALLETS, OKX_ADDRESSES))
    if RANDOM_WALLET:
        random.shuffle(data)

    if THREADS <= 0:
        THREADS = 1
    elif THREADS > len(data):
        THREADS = len(data)

    group_size = len(data) // THREADS
    remainder = len(data) % THREADS

    groups = []
    start = 0
    for i in range(THREADS):
        # Add an extra account to some groups to distribute the remainder
        end = start + group_size + (1 if i < remainder else 0)
        groups.append(data[start:end])
        start = end

    return groups


async def main(module):
    groups = _generate_groups()

    start_id = 0
    tasks = []
    for id, group in enumerate(groups):
        tasks.append(
            asyncio.create_task(
                run_group(
                    module=module,
                    group=group,
                    group_id=id,
                    start_id=start_id,
                ),
                name=f"group - {id}",
            )
        )

        start_id += len(group)

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    logger.add(
        f'logs/{datetime.now().strftime("%Y-%m-%d")}.log',
        level="DEBUG",
        colorize=False,
        backtrace=True,
        diagnose=True,
    )

    module = get_module()
    asyncio.run(main(module))
