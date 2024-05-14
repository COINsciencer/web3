import random
from typing import List

from loguru import logger
from config import NFTS2ME_ABI
from utils.helpers import retry
from .account import Account


class Minter(Account):
    def __init__(self, account_id: int, private_key: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="scroll")

    @retry
    async def mint_nft(self, contracts: dict):
        try:
            item = random.choice(list(contracts.items()))
            logger.info(
                f"[{self.account_id}][{self.address}] Mint NFT on NFTS2ME with contract - {item[0]} and price - {item[1]}ETH"
            )
            contract = self.get_contract(item[0], NFTS2ME_ABI)

            tx_data = await self.get_tx_data(self.w3.to_wei(item[1], "ether"))

            transaction = await contract.functions.mint(1).build_transaction(tx_data)
            transaction["gas"] = int(transaction["gas"] * 1.2)

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())
        except Exception as e:
            logger.error(
                f"[{self.account_id}][{self.address}] Mint NFT on NFTS2ME Error | {e}"
            )
            raise e

        return True
