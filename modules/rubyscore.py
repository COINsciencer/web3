from loguru import logger

from config import RUBYSCORE_VOTE_CONTRACT, RUBYSCORE_VOTE_ABI
from utils.gas_checker import check_gas
from utils.helpers import retry
from .account import Account


class RubyScore(Account):
    def __init__(self, account_id: int, private_key: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="scroll")

        self.contract = self.get_contract(RUBYSCORE_VOTE_CONTRACT, RUBYSCORE_VOTE_ABI)

    @retry
    async def vote(self):
        logger.info(f"[{self.account_id}][{self.address}] RubyScore Voting")

        try:
            tx_data = await self.get_tx_data()

            transaction = await self.contract.functions.vote().build_transaction(
                tx_data
            )

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())
        except Exception as e:
            logger.error(
                f"[{self.account_id}][{self.address}] RubyScore Voting Error | {e}"
            )
            raise e

        return True
