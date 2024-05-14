import aiohttp
from loguru import logger

from config import NFT_ORIGINS_CONTRACT, NFT_ORIGINS_ABI
from utils.gas_checker import check_gas
from utils.helpers import retry
from .account import Account


class NftOrigins(Account):
    def __init__(self, account_id: int, private_key: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="scroll")

        self.contract = self.get_contract(NFT_ORIGINS_CONTRACT, NFT_ORIGINS_ABI)

    async def get_nft_data(self):
        url = f"https://nft.scroll.io/p/{self.address}.json"

        async with aiohttp.ClientSession() as session:
            response = await session.get(url=url)

            if response.status == 200:
                transaction_data = await response.json()

                if "metadata" in transaction_data:
                    return transaction_data["metadata"], transaction_data["proof"]

        return False, False

    @retry
    async def mint(self):
        logger.info(f"[{self.account_id}][{self.address}] Mint Scroll Origins NFT")

        try:
            metadata, proof = await self.get_nft_data()

            if not metadata or not proof:
                return logger.error(
                    f"[{self.account_id}][{self.address}] Scroll Origins NFT Not Found"
                )

            tx_data = await self.get_tx_data()

            transaction = await self.contract.functions.mint(
                self.address,
                (
                    metadata.get("deployer"),
                    metadata.get("firstDeployedContract"),
                    metadata.get("bestDeployedContract"),
                    int(metadata.get("rarityData", 0), 16),
                ),
                proof,
            ).build_transaction(tx_data)

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())
        except Exception as e:
            logger.error(
                f"[{self.account_id}][{self.address}] Mint Scroll Origins NFT Error | {e}"
            )
            raise e

        return True
