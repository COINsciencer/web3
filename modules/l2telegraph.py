import random
from typing import Dict

from loguru import logger

from utils.gas_checker import check_gas
from utils.helpers import retry
from utils.sleeping import sleep
from .account import Account
from config import (
    L2TELEGRAPH_MESSAGE_CONTRACT,
    L2TELEGRAPH_NFT_CONTRACT,
    L2TELEGRAPH_MESSAGE_ABI,
    L2TELEGRAPH_NFT_ABI,
)


class L2Telegraph(Account):
    def __init__(self, account_id: int, private_key: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="scroll")

        self.chains_id = {
            "bsc": {
                "id": 102,
                "msg": "0x2f4572C09D6bE78F9adc18FE26fB298546eEf58e",
                "nft": "0xc162cf8c4c6697ab8e613ce0cd37c0ab97ba5a60",
            },
            "optimism": {
                "id": 111,
                "msg": "0xa5B72e35E35d219c3274Cee227FbE4D317915E0C",
                "nft": "0x64e0f6164ac110b67df9a4848707ffbcb86c87a9",
            },
            "avalanche": {
                "id": 106,
                "msg": "0x811bcF49225ffE8039989a30cf5C03f60660753d",
                "nft": "0x9539c9f145d2bf0eb7ed0824fe8583cd62410d3e",
            },
            "arbitrum": {
                "id": 110,
                "msg": "0x479e97FdE57A70bcC85e861EDB71bB613600d55a",
                "nft": "0x80be0f5b780e093b3f53bd5df8d1cf09aabf690f",
            },
            "polygon": {
                "id": 109,
                "msg": "0x523d5581A0bb8BB2Bc9f23B5202894E31124eA3e",
                "nft": "0xf9e15dd2a618bf1c0cf60f544a80f8ec774c6813",
            },
            "linea": {
                "id": 183,
                "msg": "0x7599d1275831c9fc63f9a27a3c67fe0c8fc19a47",
                "nft": "0xdc60fd9d2a4ccf97f292969580874de69e6c326e",
            },
            "moonbeam": {
                "id": 126,
                "msg": "0x36a358b3Ba1FB368E35b71ea40c7f4Ab89bFd8e1",
            },
            "kava": {"id": 177, "msg": "0x3Aef52924De5638652c525569373A3D94E0b202f"},
            "telos": {"id": 199, "msg": "0xDC60fd9d2A4ccF97f292969580874De69E6c326E"},
            "klaytn": {"id": 150, "msg": "0xDC60fd9d2A4ccF97f292969580874De69E6c326E"},
            "gnosis": {"id": 145, "msg": "0xE266EedB13A69AF15c1756a241021905B1827F6A"},
            "moonriver": {
                "id": 167,
                "msg": "0x5b10ae182c297ec76fe6fe0e3da7c4797cede02d",
            },
        }

    async def get_estimate_fee(self, contract_address: str, abi: dict, chain_id: int):
        contract = self.get_contract(contract_address, abi)

        fee = await contract.functions.estimateFees(
            chain_id, self.address, "0x", False, "0x"
        ).call()

        return int(fee[0] * 1.2)

    async def get_nft_id(self, txn_hash: str):
        receipts = await self.w3.eth.get_transaction_receipt(txn_hash)

        nft_id = int(receipts["logs"][0]["topics"][-1].hex(), 0)

        return nft_id

    @retry
    async def send_message(self, use_chain: list):
        random_chain = random.choice(use_chain)

        logger.info(
            f"[{self.account_id}][{self.address}] Send message to {random_chain.title()}"
        )

        try:
            l0_fee = await self.get_estimate_fee(
                L2TELEGRAPH_MESSAGE_CONTRACT,
                L2TELEGRAPH_MESSAGE_ABI,
                self.chains_id[random_chain]["id"],
            )

            tx_data = await self.get_tx_data(self.w3.to_wei(0.0001, "ether") + l0_fee)

            contract = self.get_contract(
                L2TELEGRAPH_MESSAGE_CONTRACT, L2TELEGRAPH_MESSAGE_ABI
            )

            transaction = await contract.functions.sendMessage(
                " ",
                self.chains_id[random_chain]["id"],
                f"{self.chains_id[random_chain]['msg']}9f63dbdf90837384872828d1ed6eb424a7f7f939",
            ).build_transaction(tx_data)

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())
        except Exception as e:
            logger.error(
                f"[{self.account_id}][{self.address}] Send message Error | {e}"
            )
            raise e

        return True

    @retry
    async def mint(self):
        logger.info(f"[{self.account_id}][{self.address}] Mint NFT")

        try:
            tx_data = await self.get_tx_data(self.w3.to_wei(0.00015, "ether"))

            contract = self.get_contract(L2TELEGRAPH_NFT_CONTRACT, L2TELEGRAPH_NFT_ABI)

            transaction = await contract.functions.mint().build_transaction(tx_data)

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())

            nft_id = await self.get_nft_id(txn_hash.hex())

            return nft_id
        except Exception as e:
            logger.error(f"[{self.account_id}][{self.address}] Mint NFT Error | {e}")
            raise e

    @retry
    async def bridge(self, use_chain: list, sleep_from: int, sleep_to: int):
        random_chain = random.choice(use_chain)

        try:
            l0_fee = await self.get_estimate_fee(
                L2TELEGRAPH_MESSAGE_CONTRACT,
                L2TELEGRAPH_MESSAGE_ABI,
                self.chains_id[random_chain]["id"],
            )

            nft_id = await self.mint()

            await sleep(
                account_id=self.account_id,
                address=self.address,
                sleep_from=sleep_from,
                sleep_to=sleep_to,
            )

            tx_data = await self.get_tx_data(l0_fee)

            logger.info(
                f"[{self.account_id}][{self.address}] Bridge NFT [{nft_id}] to {random_chain.title()}"
            )

            contract = self.get_contract(L2TELEGRAPH_NFT_CONTRACT, L2TELEGRAPH_NFT_ABI)

            transaction = await contract.functions.crossChain(
                self.chains_id[random_chain]["id"],
                f"{self.chains_id[random_chain]['nft']}dc60fd9d2a4ccf97f292969580874de69e6c326e",
                nft_id,
            ).build_transaction(tx_data)

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())
        except Exception as e:
            logger.error(f"[{self.account_id}][{self.address}] Bridge NFT Error | {e}")
            raise e
        return True
