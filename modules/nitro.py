import aiohttp
from loguru import logger
from utils.gas_checker import check_gas
from utils.helpers import retry
from .account import Account
from settings import BRIDGE_FEES


class Nitro(Account):
    def __init__(self, account_id: int, private_key: str, chain: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain=chain)

        self.chain_ids = {
            "ethereum": "1",
            "arbitrum": "42161",
            "optimism": "10",
            "zksync": "324",
            "scroll": "534352",
            "base": "8453",
            "linea": "59144",
        }

    async def get_quote(self, amount: int, destination_chain: str):
        url = "https://api-beta.pathfinder.routerprotocol.com/api/v2/quote"

        params = {
            "fromTokenAddress": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
            "toTokenAddress": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
            "amount": amount,
            "fromTokenChainId": self.chain_ids[self.chain],
            "toTokenChainId": self.chain_ids[destination_chain],
            "partnerId": 1,
        }

        async with aiohttp.ClientSession() as session:
            response = await session.get(url=url, params=params)

            transaction_data = await response.json()

            return transaction_data

    async def build_transaction(self, params: dict):
        url = "https://api-beta.pathfinder.routerprotocol.com/api/v2/transaction"

        async with aiohttp.ClientSession() as session:
            response = await session.post(url=url, json=params)

            transaction_data = await response.json()

            return transaction_data

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
                fee_cost_wei=self.w3.to_wei(BRIDGE_FEES["nitro"], "ether"),
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
                f"[{self.account_id}][{self.address}] Bridge Nitro – {self.chain.title()} -> "
                + f"{to_chain.title()} | {amount} ETH"
            )

            quote = await self.get_quote(amount_wei, to_chain)
            quote.update(
                {"senderAddress": self.address, "receiverAddress": self.address}
            )

            transaction_data = await self.build_transaction(quote)

            tx_data = await self.get_tx_data()
            tx_data.update(
                {
                    "from": self.w3.to_checksum_address(
                        transaction_data["txn"]["from"]
                    ),
                    "to": self.w3.to_checksum_address(transaction_data["txn"]["to"]),
                    "value": int(transaction_data["txn"]["value"], 16),
                    "data": transaction_data["txn"]["data"],
                }
            )

            signed_txn = await self.sign(tx_data)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())

            await self.wait_for_balance_increase(
                balance_wei=cur_dst_balance_wei,
                increase_amount_wei=tx_data["value"],
                chain=to_chain,
            )
        except Exception as e:
            logger.error(
                f"[{self.account_id}][{self.address}] Bridge Nitro Error | {e}"
            )
            raise e
        return True
