from loguru import logger

from settings import BRIDGE_FEES
from utils.gas_checker import check_gas
from utils.helpers import retry
from .account import Account

from config import (
    BRIDGE_CONTRACTS,
    DEPOSIT_ABI,
    WITHDRAW_ABI,
    ORACLE_ABI,
    SCROLL_TOKENS,
    WETH_ABI,
)


class Scroll(Account):
    def __init__(self, account_id: int, private_key: str, chain: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain=chain)

    @retry
    async def deposit(
        self,
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
                fee_cost_wei=self.w3.to_wei(BRIDGE_FEES["native"]["in"], "ether"),
            )

            dst_account = Account(
                account_id=self.account_id,
                private_key=self.private_key,
                chain="scroll",
            )
            cur_dst_balance_wei = await dst_account.w3.eth.get_balance(
                dst_account.address
            )

            logger.info(
                f"[{self.account_id}][{self.address}] Bridge to Scroll | {amount} ETH"
            )

            contract = self.get_contract(BRIDGE_CONTRACTS["deposit"], DEPOSIT_ABI)

            fee = self.w3.to_wei(0.0002, "ether")

            tx_data = await self.get_tx_data(amount_wei + fee, False)

            transaction = await contract.functions.depositETH(
                amount_wei,
                168000,
            ).build_transaction(tx_data)

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())

            await self.wait_for_balance_increase(
                balance_wei=cur_dst_balance_wei,
                increase_amount_wei=tx_data["value"],
                chain="scroll",
                fee_inaccuracy=0.003,
            )
        except Exception as e:
            logger.error(
                f"[{self.account_id}][{self.address}] Bridge to Scroll Error | {e}"
            )
            raise e

        return True

    @retry
    async def withdraw(
        self,
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
                fee_cost_wei=self.w3.to_wei(BRIDGE_FEES["native"]["out"], "ether"),
            )

            logger.info(
                f"[{self.account_id}][{self.address}] Bridge from Scroll | {amount} ETH"
            )

            dst_account = Account(
                account_id=self.account_id,
                private_key=self.private_key,
                chain="ethereum",
            )
            cur_dst_balance_wei = await dst_account.w3.eth.get_balance(
                dst_account.address
            )

            contract = self.get_contract(BRIDGE_CONTRACTS["withdraw"], WITHDRAW_ABI)

            tx_data = await self.get_tx_data(amount_wei)

            transaction = await contract.functions.withdrawETH(
                amount_wei, 0
            ).build_transaction(tx_data)

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())

            await self.wait_for_balance_increase(
                balance_wei=cur_dst_balance_wei,
                increase_amount_wei=tx_data["value"],
                chain="ethereum",
            )
        except Exception as e:
            logger.error(
                f"[{self.account_id}][{self.address}] Bridge from Scroll Error | {e}"
            )
            raise e

        return True

    @retry
    async def wrap_eth(
        self,
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
            )

            weth_contract = self.get_contract(SCROLL_TOKENS["WETH"], WETH_ABI)

            logger.info(f"[{self.account_id}][{self.address}] Wrap {amount} ETH")

            tx_data = await self.get_tx_data(amount_wei)

            transaction = await weth_contract.functions.deposit().build_transaction(
                tx_data
            )

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())
        except Exception as e:
            logger.error(f"[{self.account_id}][{self.address}] Wrap Error | {e}")
            raise e

        return True

    @retry
    async def unwrap_eth(
        self,
        min_amount: float,
        max_amount: float,
        decimal: int,
        all_amount: bool,
        min_percent: int,
        max_percent: int,
    ):
        try:
            amount_wei, amount, balance = await self.get_amount(
                "WETH",
                min_amount,
                max_amount,
                decimal,
                all_amount,
                min_percent,
                max_percent,
            )

            weth_contract = self.get_contract(SCROLL_TOKENS["WETH"], WETH_ABI)

            logger.info(f"[{self.account_id}][{self.address}] Unwrap {amount} ETH")

            tx_data = await self.get_tx_data()

            transaction = await weth_contract.functions.withdraw(
                amount_wei
            ).build_transaction(tx_data)

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())
        except Exception as e:
            logger.error(f"[{self.account_id}][{self.address}] Unwrap Error | {e}")
            raise e

        return True
