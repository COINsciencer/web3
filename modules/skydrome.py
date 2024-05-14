import time

from loguru import logger
from web3 import Web3
from config import SKYDROME_ROUTER_ABI, SKYDROME_CONTRACTS, SCROLL_TOKENS
from utils.gas_checker import check_gas
from utils.helpers import retry
from .account import Account


class Skydrome(Account):
    def __init__(self, account_id: int, private_key: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="scroll")

        self.swap_contract = self.get_contract(
            SKYDROME_CONTRACTS["router"], SKYDROME_ROUTER_ABI
        )

    async def get_min_amount_out(
        self, from_token: str, to_token: str, amount: int, slippage: float
    ):
        min_amount_out, swap_type = await self.swap_contract.functions.getAmountOut(
            amount,
            Web3.to_checksum_address(from_token),
            Web3.to_checksum_address(to_token),
        ).call()
        return int(min_amount_out - (min_amount_out / 100 * slippage)), swap_type

    async def swap_to_token(
        self, from_token: str, to_token: str, amount: int, slippage: int
    ):
        tx_data = await self.get_tx_data(amount)

        deadline = int(time.time()) + 1000000

        min_amount_out, swap_type = await self.get_min_amount_out(
            SCROLL_TOKENS[from_token], SCROLL_TOKENS[to_token], amount, slippage
        )

        contract_txn = await self.swap_contract.functions.swapExactETHForTokens(
            min_amount_out,
            [
                [
                    Web3.to_checksum_address(SCROLL_TOKENS[from_token]),
                    Web3.to_checksum_address(SCROLL_TOKENS[to_token]),
                    swap_type,
                ]
            ],
            self.address,
            deadline,
        ).build_transaction(tx_data)

        return contract_txn

    async def swap_to_eth(
        self, from_token: str, to_token: str, amount: int, slippage: int
    ):
        token_address = Web3.to_checksum_address(SCROLL_TOKENS[from_token])

        await self.approve(amount, token_address, SKYDROME_CONTRACTS["router"])

        tx_data = await self.get_tx_data()

        deadline = int(time.time()) + 1000000

        min_amount_out, swap_type = await self.get_min_amount_out(
            SCROLL_TOKENS[from_token], SCROLL_TOKENS[to_token], amount, slippage
        )

        contract_txn = await self.swap_contract.functions.swapExactTokensForETH(
            amount,
            min_amount_out,
            [
                [
                    Web3.to_checksum_address(SCROLL_TOKENS[from_token]),
                    Web3.to_checksum_address(SCROLL_TOKENS[to_token]),
                    swap_type,
                ]
            ],
            self.address,
            deadline,
        ).build_transaction(tx_data)

        return contract_txn

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
                f"[{self.account_id}][{self.address}] Swap on Skydrome – {from_token} -> {to_token} | {amount} {from_token}"
            )

            if from_token == "ETH":
                contract_txn = await self.swap_to_token(
                    from_token, to_token, amount_wei, slippage
                )
            else:
                contract_txn = await self.swap_to_eth(
                    from_token, to_token, amount_wei, slippage
                )

            signed_txn = await self.sign(contract_txn)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())
        except Exception as e:
            logger.error(
                f"[{self.account_id}][{self.address}] Swap on Skydrome Error | {e}"
            )
            raise e

        return True
