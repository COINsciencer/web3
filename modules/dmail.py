import random
from hashlib import sha256

from loguru import logger
from config import DMAIL_CONTRACT, DMAIL_ABI
from utils.gas_checker import check_gas
from utils.helpers import retry
from .account import Account


class Dmail(Account):
    def __init__(self, account_id: int, private_key: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="scroll")

        self.contract = self.get_contract(DMAIL_CONTRACT, DMAIL_ABI)

    @retry
    async def send_mail(self):
        logger.info(f"[{self.account_id}][{self.address}] Send email")

        email = sha256(str(1e11 * random.random()).encode()).hexdigest()
        theme = sha256(str(1e11 * random.random()).encode()).hexdigest()

        try:
            data = self.contract.encodeABI("send_mail", args=(email, theme))

            tx_data = await self.get_tx_data()
            tx_data.update(
                {
                    "data": data,
                    "to": self.w3.to_checksum_address(DMAIL_CONTRACT),
                    "gasPrice": await self.w3.eth.gas_price,
                }
            )

            signed_txn = await self.sign(tx_data)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())
        except Exception as e:
            logger.error(f"[{self.account_id}][{self.address}] Send email Error | {e}")
            raise e

        return True
