import aiohttp
from loguru import logger

from settings import BRIDGE_FEES
from utils.gas_checker import check_gas
from utils.helpers import retry
from .account import Account
from config import ORBITER_CONTRACT


class Orbiter(Account):
    def __init__(self, account_id: int, private_key: str, chain: str) -> None:
        super().__init__(
            account_id=account_id,
            private_key=private_key,
            chain=chain,
        )

        self.chain_ids = {
            "ethereum": "1",
            "arbitrum": "42161",
            "optimism": "10",
            "zksync": "324",
            "nova": "42170",
            "zkevm": "1101",
            "scroll": "534352",
            "base": "8453",
            "linea": "59144",
            "zora": "7777777",
        }

    @retry
    async def get_bridge_amount(self, from_chain: str, to_chain: str, amount: float):
        url = "https://openapi.orbiter.finance/explore/v3/yj6toqvwh1177e1sexfy0u1pxx5j8o47"

        data = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "orbiter_calculatedAmount",
            "params": [
                f"{self.chain_ids[from_chain]}-{self.chain_ids[to_chain]}:ETH-ETH",
                float(amount),
            ],
        }

        async with aiohttp.ClientSession() as session:
            response = await session.post(
                url=url,
                headers={"Content-Type": "application/json"},
                json=data,
            )

            response_data = await response.json()

            if response_data.get("result").get("error", None) is None:
                return int(response_data.get("result").get("_sendValue"))

            else:
                error_data = response_data.get("result").get("error")

                logger.error(
                    f"[{self.account_id}][{self.address}] Orbiter error | {error_data}"
                )

                return False

    @retry
    async def bridge(
        self,
        to_chain: str,
        min_amount: float,
        max_amount: float,
        decimal: int,
        all_amount: bool,
        min_percent: int,
        max_percent: int,
    ):
        try:
            amount_wei, amount, balance = await self.get_amount(
                "ETH",
                min_amount,
                max_amount,
                decimal,
                all_amount,
                min_percent,
                max_percent,
                fee_cost_wei=self.w3.to_wei(BRIDGE_FEES["orbiter"], "ether"),
            )

            dst_account = Account(
                account_id=self.account_id,
                private_key=self.private_key,
                chain=to_chain,
            )
            cur_dst_balance_wei = await dst_account.w3.eth.get_balance(
                dst_account.address
            )

            logger.info(
                f"[{self.account_id}][{self.address}] Bridge {self.chain} –> {to_chain} | {amount} ETH"
            )

            if ORBITER_CONTRACT == "":
                logger.error(
                    f"[{self.account_id}][{self.address}] Don't have orbiter contract"
                )
                return

            bridge_amount = await self.get_bridge_amount(self.chain, to_chain, amount)

            if bridge_amount is False:
                return

            balance = await self.w3.eth.get_balance(self.address)

            if bridge_amount > balance:
                logger.error(f"[{self.account_id}][{self.address}] Insufficient funds!")
            else:
                tx_data = await self.get_tx_data(bridge_amount)
                tx_data.update({"to": self.w3.to_checksum_address(ORBITER_CONTRACT)})

                signed_txn = await self.sign(tx_data)

                txn_hash = await self.send_raw_transaction(signed_txn)

                await self.wait_until_tx_finished(txn_hash.hex())

                await self.wait_for_balance_increase(
                    balance_wei=cur_dst_balance_wei,
                    increase_amount_wei=bridge_amount,
                    chain=to_chain,
                )
        except Exception as e:
            logger.error(
                f"[{self.account_id}][{self.address}] Bridge on Orbiter Error | {e}"
            )
            raise e

        return True
