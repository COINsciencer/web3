from typing import Dict

import aiohttp
from loguru import logger
from config import XYSWAP_CONTRACT, SCROLL_TOKENS
from utils.gas_checker import check_gas
from utils.helpers import retry
from .account import Account


class XYSwap(Account):
    def __init__(self, account_id: int, private_key: str) -> None:
        super().__init__(
            account_id=account_id,
            private_key=private_key,
            chain="scroll",
        )

    async def get_quote(
        self, from_token: str, to_token: str, amount: int, slippage: float
    ):
        url = "https://aggregator-api.xy.finance/v1/quote"

        params = {
            "srcChainId": await self.w3.eth.chain_id,
            "srcQuoteTokenAddress": self.w3.to_checksum_address(from_token),
            "srcQuoteTokenAmount": amount,
            "dstChainId": await self.w3.eth.chain_id,
            "dstQuoteTokenAddress": self.w3.to_checksum_address(to_token),
            "slippage": slippage,
        }

        async with aiohttp.ClientSession() as session:
            response = await session.get(url=url, params=params)

            transaction_data = await response.json()

            return transaction_data

    async def build_transaction(
        self,
        from_token: str,
        to_token: str,
        amount: int,
        slippage: float,
        swap_provider: str,
    ):
        url = "https://aggregator-api.xy.finance/v1/buildTx"

        params = {
            "srcChainId": await self.w3.eth.chain_id,
            "srcQuoteTokenAddress": self.w3.to_checksum_address(from_token),
            "srcQuoteTokenAmount": amount,
            "dstChainId": await self.w3.eth.chain_id,
            "dstQuoteTokenAddress": self.w3.to_checksum_address(to_token),
            "slippage": slippage,
            "receiver": self.address,
            "srcSwapProvider": swap_provider,
        }

        if XYSWAP_CONTRACT["use_ref"]:
            params.update(
                {
                    "affiliate": self.w3.to_checksum_address(
                        "0x00000D01B969922762a63F3cfD8ec9545DE4d513"
                    ),
                    "commissionRate": 10000,
                }
            )

        async with aiohttp.ClientSession() as session:
            response = await session.get(url=url, params=params)

            transaction_data = await response.json()

            return transaction_data

    @retry
    async def swap(
        self,
        from_token: str,
        to_token: str,
        min_amount: float,
        max_amount: float,
        decimal: int,
        slippage: int,
        all_amount: bool,
        min_percent: int,
        max_percent: int,
    ):
        try:
            amount_wei, amount, balance = await self.get_amount(
                from_token,
                min_amount,
                max_amount,
                decimal,
                all_amount,
                min_percent,
                max_percent,
            )

            logger.info(
                f"[{self.account_id}][{self.address}] Swap on XYSwap – {from_token} -> {to_token} | {amount} {from_token}"
            )

            from_token = (
                "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
                if from_token == "ETH"
                else SCROLL_TOKENS[from_token]
            )
            to_token = (
                "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
                if to_token == "ETH"
                else SCROLL_TOKENS[to_token]
            )

            quote = await self.get_quote(from_token, to_token, amount_wei, slippage)
            print(f"{quote=}")
            swap_provider = quote["routes"][0]["srcSwapDescription"]["provider"]

            transaction_data = await self.build_transaction(
                from_token, to_token, amount_wei, slippage, swap_provider
            )
            if transaction_data["success"] is False:
                raise Exception(f"Failed to build transaction | {transaction_data}")

            if from_token != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
                await self.approve(amount_wei, from_token, XYSWAP_CONTRACT["router"])

            tx_data = await self.get_tx_data()
            tx_data.update(
                {
                    "to": self.w3.to_checksum_address(transaction_data["tx"]["to"]),
                    "data": transaction_data["tx"]["data"],
                    "value": transaction_data["tx"]["value"],
                    "nonce": await self.w3.eth.get_transaction_count(self.address),
                }
            )

            signed_txn = await self.sign(tx_data)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())
        except Exception as e:
            logger.error(
                f"[{self.account_id}][{self.address}] Swap on XYSwap Error | {e}"
            )
            raise e

        return True
