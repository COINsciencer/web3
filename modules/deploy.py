from loguru import logger
import random
from utils.helpers import retry
from config import DEPLOYER_ABI
from .account import Account


class Deployer(Account):
    def __init__(self, account_id: int, private_key: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="scroll")

    @retry
    async def deploy_token(self, contracts: list[str]):
        logger.info(f"[{self.account_id}][{self.address}] Deploy contract")

        try:
            path = random.choice(contracts)
            with open(path, "r") as file:
                bytecode = file.read()

            tx_data = await self.get_tx_data()

            contract = self.w3.eth.contract(abi=DEPLOYER_ABI, bytecode=bytecode)

            transaction = await contract.constructor().build_transaction(tx_data)

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())
        except Exception as e:
            logger.error(
                f"[{self.account_id}][{self.address}] Deploy contract Error | {e}"
            )
            raise e

        return True
