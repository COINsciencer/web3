from loguru import logger
from config import L2PASS_ABI, L2PASS_CONTRACT
from utils.gas_checker import check_gas
from utils.helpers import retry
from .account import Account


class L2Pass(Account):
    def __init__(self, account_id: int, private_key: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="scroll")

    @staticmethod
    async def get_mint_price(contract):
        price = await contract.functions.mintPrice().call()

        return price

    @retry
    async def mint(self):
        logger.info(f"[{self.account_id}][{self.address}] Mint L2Pass NFT")

        try:
            contract = self.get_contract(
                self.w3.to_checksum_address(L2PASS_CONTRACT), L2PASS_ABI
            )

            mint_price = await self.get_mint_price(contract)

            tx_data = await self.get_tx_data(mint_price)

            transaction = await contract.functions.mint(1).build_transaction(tx_data)

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())
        except Exception as e:
            logger.error(
                f"[{self.account_id}][{self.address}] Mint L2Pass NFT Error | {e}"
            )
            raise e
        return True
