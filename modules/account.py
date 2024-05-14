import asyncio
import time
import random
from typing import Optional, Union, Type, Any

from hexbytes import HexBytes
from loguru import logger
from web3 import AsyncWeb3, Web3
from eth_account import Account as EthereumAccount
from web3.contract import Contract
from web3.exceptions import TransactionNotFound
from web3.middleware import async_geth_poa_middleware

from config import RPC, ERC20_ABI, SCROLL_TOKENS, SCROLL_FEE_INACCURACY
from settings import (
    GAS_MULTIPLIER,
    MAX_ALL_AMOUNT_ETH_PERCENT,
    MAX_PRIORITY_FEE,
    MIN_ALL_AMOUNT_ETH_PERCENT,
)
from utils.helpers import retry
from utils.sleeping import sleep


class Account:
    def __init__(self, account_id: int, private_key: str, chain: str) -> None:
        self.account_id = account_id
        self.private_key = private_key
        self.chain = chain
        self.explorer = RPC[chain]["explorer"]
        self.token = RPC[chain]["token"]

        self.w3 = AsyncWeb3(
            AsyncWeb3.AsyncHTTPProvider(random.choice(RPC[chain]["rpc"])),
            middlewares=[async_geth_poa_middleware],
        )

        self.account = EthereumAccount.from_key(private_key)
        self.address = self.account.address

    async def get_tx_data(self, value: int = 0, gas_price: bool = True):
        tx = {
            "chainId": await self.w3.eth.chain_id,
            "from": self.address,
            "value": value,
            "nonce": await self.w3.eth.get_transaction_count(self.address),
        }

        if gas_price:
            tx.update({"gasPrice": await self.w3.eth.gas_price})

        return tx

    def get_contract(
        self, contract_address: str, abi=None
    ) -> Union[Type[Contract], Contract]:
        contract_address = self.w3.to_checksum_address(contract_address)

        if abi is None:
            abi = ERC20_ABI

        contract = self.w3.eth.contract(address=contract_address, abi=abi)

        return contract

    @retry
    async def get_balances(self, tokens=SCROLL_TOKENS) -> dict:
        balances = {}

        for symbol, contract in tokens.items():
            await asyncio.sleep(0.3)
            if symbol == "ETH":
                balances[symbol] = await self.get_balance()
            else:
                balances[symbol] = await self.get_balance(contract)

        return balances

    @retry
    async def get_balance(self, contract_address: Optional[str] = None) -> dict:
        if contract_address is None:
            balance_wei = await self.w3.eth.get_balance(self.address)
            balance = AsyncWeb3.from_wei(balance_wei, "ether")

            return {
                "balance_wei": balance_wei,
                "balance": balance,
                "symbol": "ETH",
                "decimal": 18,
            }
        contract_address = AsyncWeb3.to_checksum_address(contract_address)
        contract = self.get_contract(contract_address)

        symbol = await contract.functions.symbol().call()
        await asyncio.sleep(0.1)
        decimal = await contract.functions.decimals().call()
        await asyncio.sleep(0.1)
        balance_wei = await contract.functions.balanceOf(self.address).call()

        balance = balance_wei / 10**decimal

        return {
            "balance_wei": balance_wei,
            "balance": balance,
            "symbol": symbol,
            "decimal": decimal,
        }

    @retry
    async def get_amount(
        self,
        from_token: str,
        min_amount: float,
        max_amount: float,
        decimal: int,
        all_amount: bool,
        min_percent: int = MIN_ALL_AMOUNT_ETH_PERCENT,
        max_percent: int = MAX_ALL_AMOUNT_ETH_PERCENT,
        fee_cost_wei: float = 0,
        additinal_fees: Optional[list] = None,
    ):
        random_amount = round(random.uniform(min_amount, max_amount), decimal)

        if from_token == "ETH":
            balance = await self.w3.eth.get_balance(self.address)

            if fee_cost_wei:
                add_fee = 0
                if additinal_fees is not None:
                    for fee in additinal_fees:
                        add_fee += fee
                value = (
                    balance
                    - fee_cost_wei
                    - Web3.to_wei(add_fee + SCROLL_FEE_INACCURACY, "ether")
                )
            else:
                value = (
                    balance
                    * random.uniform(
                        min_percent,
                        max_percent,
                    )
                    / 100
                )

            if value < 1:
                logger.error(
                    f"[{self.account_id}][{self.address}] Insufficient funds! | {value}"
                )
                raise Exception("Insufficient funds!")

            amount_wei = (
                int(value) if all_amount else Web3.to_wei(random_amount, "ether")
            )
            amount = Web3.from_wei(int(value), "ether") if all_amount else random_amount
        else:
            balance = await self.get_balance(SCROLL_TOKENS[from_token])
            amount_wei = (
                balance["balance_wei"]
                if all_amount
                else int(random_amount * 10 ** balance["decimal"])
            )
            amount = balance["balance"] if all_amount else random_amount
            balance = balance["balance_wei"]

        return amount_wei, amount, balance

    @retry
    async def check_allowance(self, token_address: str, contract_address: str) -> int:
        token_address = self.w3.to_checksum_address(token_address)
        contract_address = self.w3.to_checksum_address(contract_address)

        contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
        amount_approved = await contract.functions.allowance(
            self.address, contract_address
        ).call()

        return amount_approved

    @retry
    async def approve(
        self, amount: float, token_address: str, contract_address: str
    ) -> None:
        token_address = self.w3.to_checksum_address(token_address)
        contract_address = self.w3.to_checksum_address(contract_address)

        contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)

        allowance_amount = await self.check_allowance(token_address, contract_address)

        if amount > allowance_amount or amount == 0:
            logger.success(f"[{self.account_id}][{self.address}] Make approve")

            approve_amount = 2**128 if amount > allowance_amount else 0

            tx_data = await self.get_tx_data()

            transaction = await contract.functions.approve(
                contract_address, approve_amount
            ).build_transaction(tx_data)

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())

            await sleep(
                account_id=self.account_id,
                address=self.address,
                sleep_from=5,
                sleep_to=20,
            )

    @retry
    async def wait_for_balance_increase(
        self,
        balance_wei: float,
        increase_amount_wei: float,
        chain="scroll",
        timeout=24 * 60 * 60 + 30,
        fee_inaccuracy=0.0015,
        sleep=60,
    ):
        logger.info(
            f"[{self.account_id}][{self.address}] Waiting for balance increase from {balance_wei / 10 ** 18} to {(balance_wei + increase_amount_wei) / 10 ** 18} on {chain} for {timeout} seconds"
        )
        start_time = time.time()

        account = self
        if chain != self.chain:
            account = Account(
                account_id=self.account_id,
                private_key=self.private_key,
                chain=chain,
            )

        while True:
            if time.time() - start_time > timeout:
                logger.error(
                    f"[{self.account_id}][{self.address}] Timeout {timeout} seconds reached"
                )
                return False

            new_balance = (await account.get_balance())["balance_wei"]
            if new_balance >= balance_wei + increase_amount_wei - AsyncWeb3.to_wei(
                fee_inaccuracy, "ether"
            ):
                logger.success(
                    f"[{self.account_id}][{self.address}] Balance increased from {balance_wei / 10 ** 18} to {new_balance / 10 ** 18}"
                )
                return True

            await asyncio.sleep(sleep)

    @retry
    async def wait_until_tx_finished(self, hash: str, max_wait_time=1000) -> None:
        start_time = time.time()
        while True:
            try:
                receipts = await self.w3.eth.get_transaction_receipt(hash)
                status = receipts.get("status")
                if status == 1:
                    logger.success(
                        f"[{self.account_id}][{self.address}] {self.explorer}{hash} successfully!"
                    )
                    return
                elif status is None:
                    await asyncio.sleep(0.3)
                else:
                    logger.error(
                        f"[{self.account_id}][{self.address}] {self.explorer}{hash} transaction failed!"
                    )
                    raise Exception(f"Transaction failed! {self.explorer}{hash}")
            except TransactionNotFound:
                if time.time() - start_time > max_wait_time:
                    logger.error(
                        f"[{self.account_id}][{self.address}] {self.explorer}{hash} transaction not found!"
                    )
                    raise Exception(f"Transaction not found! {self.explorer}{hash}")
                await asyncio.sleep(1)

    @retry
    async def sign(self, transaction, wait_for_gas=True) -> Any:
        from utils.gas_checker import wait_gas

        if wait_for_gas:
            await wait_gas()

        if transaction.get("gasPrice", None) is None:
            max_priority_fee_per_gas = self.w3.to_wei(
                MAX_PRIORITY_FEE["ethereum"], "gwei"
            )
            max_fee_per_gas = await self.w3.eth.gas_price

            transaction.update(
                {
                    "maxPriorityFeePerGas": max_priority_fee_per_gas,
                    "maxFeePerGas": max_fee_per_gas,
                }
            )

        gas = await self.w3.eth.estimate_gas(transaction)
        gas = int(gas * GAS_MULTIPLIER)

        transaction.update({"gas": gas})

        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)

        return signed_txn

    @retry
    async def send_raw_transaction(self, signed_txn) -> HexBytes:
        txn_hash = await self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        return txn_hash
