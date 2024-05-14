from loguru import logger
from config import LAYERBANK_CONTRACT, LAYERBANK_WETH_CONTRACT, LAYERBANK_ABI
from utils.gas_checker import check_gas
from utils.helpers import retry
from utils.sleeping import sleep
from .account import Account


class LayerBank(Account):
    def __init__(self, account_id: int, private_key: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="scroll")

        self.contract = self.get_contract(LAYERBANK_CONTRACT, LAYERBANK_ABI)

    async def get_deposit_amount(self):
        weth_contract = self.get_contract(LAYERBANK_WETH_CONTRACT)

        amount = await weth_contract.functions.balanceOf(self.address).call()

        return amount

    @retry
    async def deposit(
        self,
        min_amount: float,
        max_amount: float,
        decimal: int,
        sleep_from: int,
        sleep_to: int,
        make_withdraw: bool,
        all_amount: bool,
        min_percent: int,
        max_percent: int,
    ) -> None:
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

            logger.info(
                f"[{self.account_id}][{self.address}] Make deposit on LayerBank | {amount} ETH"
            )

            tx_data = await self.get_tx_data(amount_wei)

            transaction = await self.contract.functions.supply(
                self.w3.to_checksum_address(LAYERBANK_WETH_CONTRACT),
                amount_wei,
            ).build_transaction(tx_data)

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())

            if make_withdraw:
                await sleep(
                    account_id=self.account_id,
                    address=self.address,
                    sleep_from=sleep_from,
                    sleep_to=sleep_to,
                )

                await self.withdraw()
        except Exception as e:
            logger.error(
                f"[{self.account_id}][{self.address}] Make deposit on LayerBank Error | {e}"
            )
            raise e

        return True

    @retry
    async def withdraw(self) -> None:
        try:
            amount = await self.get_deposit_amount()

            if amount > 0:
                logger.info(
                    f"[{self.account_id}][{self.address}] Make withdraw from LayerBank | "
                    + f"{self.w3.from_wei(amount, 'ether')} ETH"
                )

                await self.approve(amount, LAYERBANK_WETH_CONTRACT, LAYERBANK_CONTRACT)

                tx_data = await self.get_tx_data()

                transaction = await self.contract.functions.redeemUnderlying(
                    self.w3.to_checksum_address(LAYERBANK_WETH_CONTRACT),
                    amount,
                ).build_transaction(tx_data)

                signed_txn = await self.sign(transaction)

                txn_hash = await self.send_raw_transaction(signed_txn)

                await self.wait_until_tx_finished(txn_hash.hex())
            else:
                logger.error(f"[{self.account_id}][{self.address}] Deposit not found")
        except Exception as e:
            logger.error(
                f"[{self.account_id}][{self.address}] Make withdraw from LayerBank Error | {e}"
            )
            raise e

        return True
