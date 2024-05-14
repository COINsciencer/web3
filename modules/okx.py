import asyncio
import base64
import hmac
import random
import time
from typing import Union
import ccxt
import requests
from modules.account import Account
from config import RPC
from loguru import logger
import datetime

from utils.gas_checker import check_gas


class OKX(Account):
    def __init__(
        self,
        account_id: int,
        private_key: str,
        chain: str,
        credentials: dict,
    ) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain=chain)

        self.credentials = credentials
        try:
            self.okx_network_name = RPC[chain]["okx_network_name"]
        except KeyError as e:
            raise ValueError(f"OKX doesn't support {chain} network")

        if self.okx_network_name is None:
            raise ValueError(f"Couldn't get the okx network name for {chain}")

        self.client = ccxt.okx(
            config={
                "apiKey": self.credentials["apikey"],
                "secret": self.credentials["apisecret"],
                "password": self.credentials["passphrase"],
                "enableRateLimit": True,
            }
        )

    async def wait_for_withdrawal(self, txid):
        logger.info(
            f"[{self.account_id}][{self.address}] Waiting for OKX withdrawal to complete| txid: {txid}"
        )
        while True:
            # fetch recent withdrawals
            withdrawal = self.client.fetch_withdrawal(id=txid)

            if withdrawal["status"] == "ok":
                return
            elif withdrawal["status"] == "failed":
                raise ValueError(
                    f"[{self.account_id}][{self.address}] OKX Withdraw Failed | response: {withdrawal}"
                )
            elif withdrawal["status"] == "canceled":
                raise ValueError(
                    f"[{self.account_id}][{self.address}] OKX Withdraw Canceled | response: {withdrawal}"
                )
            elif withdrawal["status"] == "pending":
                logger.debug(
                    f"[{self.account_id}][{self.address}] OKX Withdraw Pending | response: {withdrawal}"
                )
            else:
                raise ValueError(
                    f"[{self.account_id}][{self.address}] OKX Withdraw Unknown Status | response: {withdrawal}"
                )

            # wait before checking again
            await asyncio.sleep(60)

    @check_gas
    async def withdraw(
        self, min_amount, max_amount, token, transfer_from_subaccounts=False
    ):
        amount_to_withdraw = round(random.uniform(min_amount, max_amount), 6)

        logger.info(
            f"[{self.account_id}][{self.address}] Withdrawing from OKX | {amount_to_withdraw} ETH"
        )

        if transfer_from_subaccounts:
            await self.transfer_from_subaccounts()

        try:
            chainName = token + "-" + self.okx_network_name
            fee = self.get_withdrawal_fee(token, chainName)

            response = self.client.withdraw(
                token,
                amount_to_withdraw,
                self.address,
                params={
                    "toAddr": self.address,
                    "chainName": chainName,
                    "dest": 4,
                    "fee": fee,
                    "pwd": "-",
                    "amt": amount_to_withdraw,
                    "network": self.okx_network_name,
                },
            )

            await self.wait_for_withdrawal(response["info"]["wdId"])

            logger.info(
                f"[{self.account_id}][{self.address}] OKX Withdrawed successfully | {amount_to_withdraw} {token}"
            )
        except Exception as error:
            logger.error(
                f"[{self.account_id}][{self.address}] Couldn't perform OKX Withdraw | {amount_to_withdraw} {token}: {error}"
            )
            raise error

        return True

    def get_withdrawal_fee(self, token, chainName):
        currencies = self.client.fetch_currencies()
        for currency in currencies:
            if currency == token:
                currency_info = currencies[currency]
                network_info = currency_info.get("networks", None)
                if network_info:
                    for cur_network in network_info:
                        network_data = network_info[cur_network]
                        network_id = network_data["id"]
                        if network_id == chainName:
                            withdrawal_fee = currency_info["networks"][cur_network][
                                "fee"
                            ]
                            if withdrawal_fee == 0:
                                return 0
                            else:
                                return withdrawal_fee
        raise ValueError(
            f"Couldn't get the withdrawal fee for {token=} and {chainName=}"
        )

    async def deposit(self, address, min_amount_left, max_amount_left):
        """Deposit funds from wallet to okx. Only ETH token supported"""

        amount_leave_on_wallet = round(
            random.uniform(min_amount_left, max_amount_left), 6
        )

        balance = await self.w3.eth.get_balance(self.address)

        amount = int(balance - amount_leave_on_wallet * 10**18)
        logger.info(
            f"[{self.account_id}][{self.address}] Depositing to OKX | {amount / 10**18} ETH"
        )

        amount -= self.w3.to_wei(0.00005, "ether")  # in case of inaccuracy

        estimated_gas = await self.w3.eth.estimate_gas(
            {
                "from": self.address,
                "to": self.w3.to_checksum_address(address),
                "value": amount,
            }
        )
        estimated_gas_price = await self.w3.eth.gas_price
        estimated_fee = estimated_gas * estimated_gas_price

        value = amount - estimated_fee

        tx = {
            "chainId": await self.w3.eth.chain_id,
            "to": self.w3.to_checksum_address(address),
            "nonce": await self.w3.eth.get_transaction_count(self.address),
            "gas": estimated_gas,
            "gasPrice": await self.w3.eth.gas_price,
            "value": value,
        }

        try:
            signed_tx = await self.sign(tx)
            tx_hash = await self.send_raw_transaction(signed_txn=signed_tx)

            logger.info(
                f"[{self.account_id}][{self.address}] OKX Deposit | {amount / 10**18} ETH | TX HASH: {self.explorer}{tx_hash.hex()}"
            )

            await self.wait_until_tx_finished(tx_hash.hex())

            logger.info(
                f"[{self.account_id}][{self.address}] OKX Deposited successfully | {amount / 10**18} ETH"
            )
        except Exception as e:
            logger.error(f"Deposit transaction on L1 network failed | error: {e}")
            raise e

        return True

    async def transfer_from_subaccounts(self):
        logger.info(
            f"[{self.account_id}][{self.address}] Transfering ETH from subaccounts"
        )

        try:
            _, _, headers = self.build_request(
                request_path=f"/api/v5/users/subaccount/list", meth="GET"
            )
            list_sub = requests.get(
                "https://www.okx.cab/api/v5/users/subaccount/list",
                timeout=10,
                headers=headers,
            )
            list_sub = list_sub.json()

            for sub_data in list_sub["data"]:
                name_sub = sub_data["subAcct"]

                _, _, headers = self.build_request(
                    request_path=f"/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy=ETH",
                    meth="GET",
                )

                sub_balance = requests.get(
                    f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy=ETH",
                    timeout=10,
                    headers=headers,
                )
                sub_balance = sub_balance.json()
                sub_balance = sub_balance["data"][0]["bal"]

                logger.info(
                    f"[{self.account_id}][{self.address}]{name_sub} | sub_balance : {sub_balance} ETH"
                )

                body = {
                    "ccy": "ETH",
                    "amt": str(sub_balance),
                    "from": 6,
                    "to": 6,
                    "type": "2",
                    "subAcct": name_sub,
                }
                _, _, headers = self.build_request(
                    request_path=f"/api/v5/asset/transfer", body=str(body), meth="POST"
                )
                a = requests.post(
                    "https://www.okx.cab/api/v5/asset/transfer",
                    data=str(body),
                    timeout=10,
                    headers=headers,
                )
                a = a.json()
                print(a)
                await asyncio.sleep(1)

        except Exception as error:
            logger.error(
                f"[{self.account_id}][{self.address}] Transfer ETH from subaccounts Error: {error}. list_sub : {list_sub}"
            )

    def build_request(
        self, request_path="/api/v5/account/balance?ccy=USDT", body="", meth="GET"
    ):
        def signature(
            timestamp: str,
            method: str,
            request_path: str,
            secret_key: str,
            body: str = "",
        ) -> str:
            if not body:
                body = ""

            message = timestamp + method.upper() + request_path + body
            mac = hmac.new(
                bytes(secret_key, encoding="utf-8"),
                bytes(message, encoding="utf-8"),
                digestmod="sha256",
            )
            d = mac.digest()
            return base64.b64encode(d).decode("utf-8")

        try:
            dt_now = datetime.datetime.utcnow()
            ms = str(dt_now.microsecond).zfill(6)[:3]
            timestamp = f"{dt_now:%Y-%m-%dT%H:%M:%S}.{ms}Z"

            base_url = "https://www.okex.com"
            headers = {
                "Content-Type": "application/json",
                "OK-ACCESS-KEY": self.credentials["apikey"],
                "OK-ACCESS-SIGN": signature(
                    timestamp, meth, request_path, self.credentials["apisecret"], body
                ),
                "OK-ACCESS-TIMESTAMP": timestamp,
                "OK-ACCESS-PASSPHRASE": self.credentials["passphrase"],
                "x-simulated-trading": "0",
            }
        except Exception as ex:
            logger.error(
                f"[{self.account_id}][{self.address}] Building request failed error: {ex}"
            )
        return base_url, request_path, headers
