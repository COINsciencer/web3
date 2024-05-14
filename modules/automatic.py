import enum
import random
from copy import deepcopy
import traceback

from loguru import logger
from web3 import Web3
from config import SCROLL_TOKENS
from modules import *
from settings import (
    ENABLE_ERROR_TRACEBACK,
    RETRIES,
    RETRY_DELAY_MAX,
    RETRY_DELAY_MIN,
    SLEEP_MAX,
    SLEEP_MIN,
)
from utils.sleeping import sleep


class AutomaticModules(str, enum.Enum):
    swaps = "swaps"
    wrap_unwrap_eth = "wrap_unwrap_eth"
    send_email = "send_email"
    mint_l2pass = "mint_l2pass"
    mint_bridge_l2_telegraph = "mint_l2_telegraph"
    l2telegraph_send_message = "l2telegraph_send_message"
    create_gnosis_safe = "create_gnosis_safe"
    create_omnisea_collection = "create_omnisea_collection"
    aave = "aave"
    layerbank = "layerbank"
    mint_nfts2me = "mint_nfts2me"
    mint_zerius = "mint_zerius"
    mint_zkstars = "mint_zkstars"
    rubyscore_vote = "rubyscore_vote"
    deploy_contract = "deploy_contract"
    bridge_in = "bridge_in"
    bridge_out = "bridge_out"


class Automatic(Account):
    class ModuleEntry:
        def __init__(self, module, config):
            self.module_name = module
            self.config = config

    def __init__(
        self,
        account_id,
        private_key,
        okx_address,
        modules: list,
        config: dict,
        modules_config: dict,
    ):
        """
        modules - list of modules to get config for and run
        config - dict with settings and with configs for modules
        modules_config - config for modules
        """
        super().__init__(account_id=account_id, private_key=private_key, chain="scroll")

        self.account_id = account_id
        self.private_key = private_key
        self.okx_address = okx_address
        self.config = deepcopy(config)
        self.modules_config = deepcopy(modules_config)

        self.modules_entries = []

        self.bridge_in = None
        self.brdge_out = None

        self._configure(modules)

        self.modules_mapping = {
            AutomaticModules.swaps: self.swaps,
            AutomaticModules.wrap_unwrap_eth: self.wrap_unwrap_eth,
            AutomaticModules.send_email: self.send_email,
            AutomaticModules.aave: self.aave,
            AutomaticModules.layerbank: self.layerbank,
            AutomaticModules.mint_bridge_l2_telegraph: self.mint_bridge_l2_telegraph,
            AutomaticModules.l2telegraph_send_message: self.l2telegraph_send_message,
            AutomaticModules.mint_l2pass: self.mint_l2pass,
            AutomaticModules.mint_nfts2me: self.mint_nfts2me,
            AutomaticModules.mint_zerius: self.mint_zerius,
            AutomaticModules.mint_zkstars: self.mint_zkstars,
            AutomaticModules.rubyscore_vote: self.rubyscore_vote,
            AutomaticModules.deploy_contract: self.deploy_contract,
            AutomaticModules.create_gnosis_safe: self.create_gnosis_safe,
            AutomaticModules.create_omnisea_collection: self.create_omnisea_collection,
        }

        self.made_first_transaction = False

    async def run(self):
        if self.config["okx_withdraw_enabled"]:
            await self.okx_withdraw()

        if self.config[AutomaticModules.bridge_in]["bridge_in_enabled"]:
            await self.bridge_in()

        await self.run_modules()

        if self.config["swap_all_tokens_to_eth_before_withdraw"]:
            await self.swap_all_tokens_to_eth()

        if self.config[AutomaticModules.bridge_out]["bridge_out_enabled"]:
            await self.bridge_out()

        if self.config["okx_deposit_enabled"]:
            await self.okx_deposit()

    async def run_modules(self):
        while len(self.modules_entries) > 0:
            module_entry = random.choice(self.modules_entries)

            if module_entry.module_name in self.modules_mapping:
                performed_transactions = await self.modules_mapping[
                    module_entry.module_name
                ](module_entry.config)
                self._remove_module_entries(
                    module_entry.module_name, performed_transactions
                )
            else:
                logger.error(f"Not supported module - {module_entry.module_name}")
                self._remove_module_entries(module_entry.module_name, 1, all=True)

    async def execute_func_with_retries(
        self, func, func_kwargs, module_name, max_retries=RETRIES
    ):
        done = False
        retries = 0
        while not done and retries <= max_retries:
            try:
                done = await func(**func_kwargs)
            except Exception as e:
                if ENABLE_ERROR_TRACEBACK:
                    logger.error(
                        f"[{self.account_id}][{self.address}] | {module_name} raised exception | {e}\nTraceback: {traceback.format_exc()}"
                    )
                else:
                    logger.error(
                        f"[{self.account_id}][{self.address}] | {module_name} raised exception | {e}"
                    )
                if str(e).startswith("520, "):
                    logger.error(
                        f"Probably an rpc error, I am not increasing the retry count"
                    )
                else:
                    retries += 1

            if not done:
                if retries <= max_retries:
                    logger.error(
                        f"[{self.account_id}][{self.address}] | {module_name} failed. Retrying {retries}/{max_retries}"
                    )

                    await sleep(
                        account_id=self.account_id,
                        address=self.address,
                        sleep_from=RETRY_DELAY_MIN,
                        sleep_to=RETRY_DELAY_MAX,
                    )

        return done

    async def run_module(
        self,
        module_function,
        module_name,
        module_transaction_id,
        function_kwargs,
        max_retries=None,
        fail_after_retries=False,
        module_class=None,
        class_kwargs=None,
    ):
        logger.info(
            f"[{self.account_id}][{self.address}] | Performing {module_name} #{module_transaction_id}"
        )

        max_retries = max_retries if max_retries is not None else RETRIES

        if self.made_first_transaction or self.config["sleep_at_start"]:
            await sleep(
                account_id=self.account_id,
                address=self.address,
                sleep_from=SLEEP_MIN,
                sleep_to=SLEEP_MAX,
            )

        if module_class is not None:
            if class_kwargs is None:
                class_kwargs = {
                    "account_id": self.account_id,
                    "private_key": self.private_key,
                }
            func = module_class(**class_kwargs).__getattribute__(module_function)
        else:
            func = module_function

        done = await self.execute_func_with_retries(
            func=func,
            func_kwargs=function_kwargs,
            max_retries=max_retries,
            module_name=module_name,
        )

        self.made_first_transaction = True

        if not done and fail_after_retries:
            raise ValueError(f"{module_name} failed after {max_retries} retries")

        return done or self.config["skip_if_failed"]

    async def swap_all_tokens_to_eth(self):
        config = self.config[AutomaticModules.swaps]

        logger.info(f"[{self.account_id}][{self.address}] | Swapping all tokens to ETH")

        balances = await self.get_balances(config)

        for token in balances.values():
            if (
                token["symbol"] == "ETH"
                or not token["balance"]
                > self.config[f"min_balance_{token['symbol'].lower()}"]
            ):
                continue

            src_token = token
            dst_token = balances["ETH"]
            swap_module = self.choose_swap_module(
                config=config, src_token=src_token, dst_token=dst_token
            )
            amount = self.get_amount(config=config, src_token=src_token)
            return await self.execute_func_with_retries(
                func=swap_module["class"](
                    account_id=self.account_id,
                    private_key=self.private_key,
                ).swap,
                func_kwargs={
                    "from_token": src_token["symbol"].upper(),
                    "to_token": dst_token["symbol"].upper(),
                    "min_amount": amount if amount != "all" else 0,
                    "max_amount": amount if amount != "all" else 0,
                    "decimal": src_token["decimal"],
                    "slippage": self.modules_config[swap_module["name"]]["slippage"],
                    "all_amount": amount == "all",
                    "min_percent": self.modules_config[swap_module["name"]][
                        "min_percent"
                    ],
                    "max_percent": self.modules_config[swap_module["name"]][
                        "max_percent"
                    ],
                },
                module_name="Swap all tokens to ETH",
            )

    async def deploy_contract(self, config):
        if await self.run_module(
            module_function=Deployer(
                account_id=self.account_id,
                private_key=self.private_key,
            ).deploy_token,
            module_name="Deploy Contract",
            module_transaction_id=config["performed_quantity"] + 1,
            function_kwargs={
                "contracts": self.modules_config[MODULES_NAMES.deploy_contract][
                    "contracts"
                ],
            },
        ):
            config["performed_quantity"] += 1
            return 1

        return 0

    async def rubyscore_vote(self, config):
        if await self.run_module(
            module_function=RubyScore(
                account_id=self.account_id,
                private_key=self.private_key,
            ).vote,
            module_name="RubyScore Vote",
            module_transaction_id=config["performed_quantity"] + 1,
            function_kwargs={},
        ):
            config["performed_quantity"] += 1
            return 1

        return 0

    async def send_email(self, config):
        if await self.run_module(
            module_class=Dmail,
            module_function="send_mail",
            module_name="Send Dmail",
            module_transaction_id=config["performed_quantity"] + 1,
            function_kwargs={},
        ):
            config["performed_quantity"] += 1
            return 1

        return 0

    async def run_deposit_withdraw(
        self,
        config,
        deposit_func,
        deposit_func_kwargs,
        withdraw_func,
        withdraw_func_kwargs,
        module_name,
    ):
        performed_quantity = 0

        if config.get("withdrawn", True):
            try:
                done = await self.run_module(
                    module_function=deposit_func,
                    module_name=f"{module_name} Deposit",
                    module_transaction_id=round(config["performed_quantity"] / 2) + 1,
                    function_kwargs=deposit_func_kwargs,
                    fail_after_retries=True,
                )
                performed_quantity += 1
            except Exception as e:
                if ENABLE_ERROR_TRACEBACK:
                    logger.error(
                        f"[{self.account_id}][{self.address}] | {module_name} Deposit raised exception | {e}\nTraceback: {traceback.format_exc()}"
                    )
                else:
                    logger.error(
                        f"[{self.account_id}][{self.address}] | {module_name} Deposit raised exception | {e}"
                    )

                if self.config["skip_if_failed"]:
                    config["performed_quantity"] += 2
                    return 2
                return 0

        done = await self.run_module(
            module_function=withdraw_func,
            function_kwargs=withdraw_func_kwargs,
            module_name=f"{module_name} Withdraw",
            module_transaction_id=round(config["performed_quantity"] / 2) + 1,
        )

        if done:
            performed_quantity += 1
            config["withdrawn"] = True
        else:
            config["withdrawn"] = False

        config["performed_quantity"] += performed_quantity

        return performed_quantity

    async def aave(self, config):
        return await self.run_deposit_withdraw(
            config=config,
            deposit_func=Aave(self.account_id, self.private_key).deposit,
            deposit_func_kwargs={
                "min_amount": 1,
                "max_amount": 1,
                "decimal": 6,
                "all_amount": True,
                "sleep_from": 1,
                "sleep_to": 1,
                "make_withdraw": False,
                "min_percent": self.modules_config[MODULES_NAMES.deposit_aave][
                    "min_percent"
                ],
                "max_percent": self.modules_config[MODULES_NAMES.deposit_aave][
                    "max_percent"
                ],
            },
            withdraw_func=Aave(self.account_id, self.private_key).withdraw,
            withdraw_func_kwargs={},
            module_name="Aave",
        )

    async def layerbank(self, config):
        return await self.run_deposit_withdraw(
            config=config,
            deposit_func=LayerBank(self.account_id, self.private_key).deposit,
            deposit_func_kwargs={
                "min_amount": 1,
                "max_amount": 1,
                "decimal": 6,
                "all_amount": True,
                "sleep_from": 1,
                "sleep_to": 1,
                "make_withdraw": False,
                "min_percent": self.modules_config[MODULES_NAMES.deposit_layerbank][
                    "min_percent"
                ],
                "max_percent": self.modules_config[MODULES_NAMES.deposit_layerbank][
                    "max_percent"
                ],
            },
            withdraw_func=LayerBank(self.account_id, self.private_key).withdraw,
            withdraw_func_kwargs={},
            module_name="LayerBank",
        )

    async def l2telegraph_send_message(self, config):
        if await self.run_module(
            module_function=L2Telegraph(
                account_id=self.account_id,
                private_key=self.private_key,
            ).send_message,
            module_name="L2Telegraph Send message",
            module_transaction_id=config["performed_quantity"] + 1,
            function_kwargs={
                "use_chain": self.modules_config[
                    MODULES_NAMES.send_message_l2telegraph
                ]["use_chain"]
            },
        ):
            config["performed_quantity"] += 1
            return 1

        return 0

    async def create_omnisea_collection(self, config):
        if await self.run_module(
            module_function=Omnisea(
                account_id=self.account_id,
                private_key=self.private_key,
            ).create,
            module_name="Create Omnisea Collection",
            module_transaction_id=config["performed_quantity"] + 1,
            function_kwargs={},
        ):
            config["performed_quantity"] += 1
            return 1

        return 0

    async def create_gnosis_safe(self, config):
        if await self.run_module(
            module_function=GnosisSafe(
                account_id=self.account_id,
                private_key=self.private_key,
            ).create_safe,
            module_name="Create Gnosis safe",
            module_transaction_id=config["performed_quantity"] + 1,
            function_kwargs={},
        ):
            config["performed_quantity"] += 1
            return 1

        return 0

    async def mint_bridge_l2_telegraph(self, config):
        if config["bridge"]:
            module_function = L2Telegraph(
                account_id=self.account_id,
                private_key=self.private_key,
            ).bridge
            module_name = "L2Telegraph Bridge mint"
            function_kwargs = {
                "use_chain": self.modules_config[MODULES_NAMES.mint_bridge_l2telegraph][
                    "use_chain"
                ],
                "sleep_from": SLEEP_MIN,
                "sleep_to": SLEEP_MAX,
            }
        else:
            module_function = L2Telegraph(
                account_id=self.account_id,
                private_key=self.private_key,
            ).mint
            module_name = "L2Telegraph mint"
            function_kwargs = {}

        if await self.run_module(
            module_function=module_function,
            module_name=module_name,
            module_transaction_id=config["performed_quantity"] + 1,
            function_kwargs=function_kwargs,
        ):
            config["performed_quantity"] += 1
            return 1

        return 0

    async def mint_zerius(self, config):
        if await self.run_module(
            module_function=Zerius(
                account_id=self.account_id,
                private_key=self.private_key,
            ).mint,
            module_name="Mint Zerius",
            module_transaction_id=config["performed_quantity"] + 1,
            function_kwargs={},
        ):
            config["performed_quantity"] += 1
            return 1

        return 0

    async def mint_zkstars(self, config):
        if await self.run_module(
            module_function=ZkStars(
                account_id=self.account_id,
                private_key=self.private_key,
            ).mint,
            module_name="Mint ZkStars",
            module_transaction_id=config["performed_quantity"] + 1,
            function_kwargs={
                "contracts": [
                    random.choice(
                        self.modules_config[MODULES_NAMES.mint_zkstars]["contracts"]
                    )
                ],
                "min_mint": 1,
                "max_mint": 1,
                "mint_all": False,
                "sleep_from": 1,
                "sleep_to": 1,
            },
        ):
            config["performed_quantity"] += 1
            return 1

        return 0

    async def mint_nfts2me(self, config):
        if await self.run_module(
            module_function=Minter(
                account_id=self.account_id,
                private_key=self.private_key,
            ).mint_nft,
            module_name="Mint NFTs2ME",
            module_transaction_id=config["performed_quantity"] + 1,
            function_kwargs={
                "contracts": self.modules_config[MODULES_NAMES.mint_nfts2me][
                    "contracts"
                ],
            },
        ):
            config["performed_quantity"] += 1
            return 1

        return 0

    async def mint_l2pass(self, config):
        if await self.run_module(
            module_function=L2Pass(
                account_id=self.account_id,
                private_key=self.private_key,
            ).mint,
            module_name="Mint L2Pass",
            module_transaction_id=config["performed_quantity"] + 1,
            function_kwargs={},
        ):
            config["performed_quantity"] += 1
            return 1

        return 0

    async def wrap_unwrap_eth(self, config):
        performed_quantity = 0

        if config.get("unwraped", True):
            try:
                await self.run_module(
                    module_function=Scroll(
                        account_id=self.account_id,
                        private_key=self.private_key,
                        chain="scroll",
                    ).wrap_eth,
                    module_name="Wrap Eth",
                    function_kwargs={
                        "min_amount": self.modules_config[MODULES_NAMES.wrap_eth][
                            "min_amount"
                        ],
                        "max_amount": self.modules_config[MODULES_NAMES.wrap_eth][
                            "max_amount"
                        ],
                        "decimal": self.modules_config[MODULES_NAMES.wrap_eth][
                            "decimal"
                        ],
                        "all_amount": self.modules_config[MODULES_NAMES.wrap_eth][
                            "all_amount"
                        ],
                        "min_percent": self.modules_config[MODULES_NAMES.wrap_eth][
                            "min_percent"
                        ],
                        "max_percent": self.modules_config[MODULES_NAMES.wrap_eth][
                            "max_percent"
                        ],
                    },
                    module_transaction_id=round(config["performed_quantity"] / 2) + 1,
                    fail_after_retries=True,
                )
                performed_quantity += 1
            except Exception as e:
                logger.error(
                    f"[{self.account_id}][{self.address}] | Wrap ETH failed. Skipping Unwrap | {e}"
                )

                if self.config["skip_if_failed"]:
                    config["performed_quantity"] += 2
                    return 2
                return 0

        done = await self.run_module(
            module_function=Scroll(
                account_id=self.account_id,
                private_key=self.private_key,
                chain="scroll",
            ).unwrap_eth,
            module_name="Unwrap Eth",
            function_kwargs={
                "min_amount": 1,
                "max_amount": 1,
                "decimal": 4,
                "all_amount": True,
                "min_percent": self.modules_config[MODULES_NAMES.unwrap_eth][
                    "min_percent"
                ],
                "max_percent": self.modules_config[MODULES_NAMES.unwrap_eth][
                    "max_percent"
                ],
            },
            module_transaction_id=round(config["performed_quantity"] / 2) + 1,
        )

        if done:
            performed_quantity += 1
            config["unwraped"] = True
        else:
            config["unwraped"] = False

        config["performed_quantity"] += performed_quantity

        return performed_quantity

    async def swaps(self, config):
        quantity = self.choose_number_of_swaps(config=config)
        config["current_max_quantity"] = quantity

        performed_quantity = 0  # <3

        for _ in range(quantity):
            done = await self.run_module(
                module_function=self.swap,
                module_name="Swap",
                module_transaction_id=config["performed_quantity"] + 1,
                function_kwargs={"config": config},
            )

            if not done:
                logger.info(
                    f"[{self.account_id}][{self.address}] | Swap #{config['performed_quantity'] + 1} failed. Skipping"
                )
            else:
                performed_quantity += 1
                config["performed_quantity"] += 1

        return performed_quantity

    async def swap(self, config):
        balances = await self.get_balances(config)

        src_token = self.choose_src_token(balances=balances, config=config)
        dst_token = self.choose_dst_token(
            src_token=src_token, balances=balances, config=config
        )
        swap_module = self.choose_swap_module(
            config=config, src_token=src_token, dst_token=dst_token
        )
        amount = self.get_amount(
            config=config,
            src_token=src_token,
        )

        return await swap_module["class"](
            account_id=self.account_id,
            private_key=self.private_key,
        ).swap(
            from_token=src_token["symbol"],
            to_token=dst_token["symbol"],
            min_amount=amount if amount != "all" else 0,
            max_amount=amount if amount != "all" else 0,
            decimal=src_token["decimal"],
            slippage=self.modules_config[swap_module["name"]]["slippage"],
            all_amount=amount == "all",
            min_percent=self.modules_config[swap_module["name"]]["min_percent"],
            max_percent=self.modules_config[swap_module["name"]]["max_percent"],
        )

    def get_amount(self, config, src_token):
        if src_token["symbol"] == "ETH":
            if src_token["balance"] <= self.config["min_balance_eth"]:
                raise ValueError(
                    f"Not enough ETH to swap | balance={src_token['balance']} | min_balance_eth={self.config['min_balance_eth']}"
                )

            if "min_amount" not in config or "max_amount" not in config:
                return float(src_token["balance"]) - self.config["min_balance_eth"]

            return min(
                float(src_token["balance"]) - self.config["min_balance_eth"],
                round(
                    random.uniform(config["min_amount"], config["max_amount"]),
                    src_token["decimal"],
                ),
            )

        return "all"

    def choose_swap_module(self, config, src_token, dst_token):
        modules = []
        for module_name in config["services"]:
            module = SWAP_MODULES[module_name]
            if (
                src_token["symbol"].upper() in module["tokens"]
                and dst_token["symbol"].upper()
                in module["tokens"][src_token["symbol"].upper()]
            ):
                module["name"] = module_name
                modules.append(module)

        return random.choice(modules)

    def choose_number_of_swaps(self, config):
        maximum = config["max_quantity"] - config["performed_quantity"]
        quantity = maximum - 1

        # exlude case when quantity == maximum - 1
        while quantity == maximum - 1:
            quantity = random.randint(2, maximum)

        return quantity

    def choose_src_token(self, balances, config) -> dict:
        balances = balances.copy()

        eth = balances.pop("ETH")
        if config["first_swap_from_eth"] and config["performed_quantity"] == 0:
            return eth

        tokens = sorted(balances.values(), key=lambda x: x["balance_wei"], reverse=True)
        chosen_token = None
        for token in tokens:
            if (
                token["balance"]
                >= self.config[f"min_balance_{token['symbol'].lower()}"]
            ):
                chosen_token = token
                break

        if chosen_token is None:
            chosen_token = eth

        chosen_token["symbol"] = chosen_token["symbol"].upper()

        return chosen_token

    def choose_dst_token(self, balances: dict, src_token, config) -> dict:
        balances = balances.copy()

        if config["performed_quantity"] == config["current_max_quantity"] - 1:
            if src_token["symbol"] != "ETH":
                return balances["ETH"]

        dst_tokens = set()

        for module_name in config["services"]:
            module = SWAP_MODULES[module_name]
            if src_token["symbol"] in module["tokens"]:
                dst_tokens.update(module["tokens"][src_token["symbol"]])

        token = random.choice(list(dst_tokens))

        chosen_token = balances[token]
        chosen_token["symbol"] = chosen_token["symbol"].upper()

        return chosen_token

    async def get_balances(self, config):
        swappable_tokens = self.get_swappable_tokens(config=config)
        tokens = {k: v for k, v in SCROLL_TOKENS.items() if k in swappable_tokens}

        balances = await super().get_balances(tokens=tokens)

        return balances

    async def okx_deposit(self):
        config = self.modules_config[MODULES_NAMES.okx_deposit]
        okx_client = OKX(
            account_id=self.account_id,
            private_key=self.private_key,
            chain=self.config[AutomaticModules.bridge_out]["bridge_out_chain"],
            credentials=config["credentials"],
        )

        if self.config[AutomaticModules.bridge_out]["bridge_out_chain"] == "scroll":
            min_amount_left = self.config["min_amount_leave_on_scroll"]
            max_amount_left = self.config["max_amount_leave_on_scroll"]
        else:
            min_amount_left = config["min_amount_left"]
            max_amount_left = config["max_amount_left"]

        if not (
            await self.execute_func_with_retries(
                func=okx_client.deposit,
                func_kwargs={
                    "address": self.okx_address,
                    "min_amount_left": min_amount_left,
                    "max_amount_left": max_amount_left,
                },
                module_name="OKX deposit",
            )
        ):
            raise ValueError("OKX deposit failed")

        return True

    async def okx_withdraw(self):
        config = self.modules_config[MODULES_NAMES.okx_withdraw]

        okx_client = OKX(
            account_id=self.account_id,
            private_key=self.private_key,
            chain=self.config[AutomaticModules.bridge_in]["bridge_in_chain"],
            credentials=config["credentials"],
        )
        if not (
            await self.execute_func_with_retries(
                func=okx_client.withdraw,
                func_kwargs={
                    "min_amount": config["min_amount"],
                    "max_amount": config["max_amount"],
                    "token": config["token"],
                    "transfer_from_subaccounts": config["transfer_from_subaccounts"],
                },
                module_name="OKX withdraw",
            )
        ):
            raise ValueError("OKX withdraw failed")

        return True

    async def layerswap_bridge_in(self):
        config = self.modules_config[MODULES_NAMES.bridge_layerswap]

        layerswap = LayerSwap(
            self.account_id,
            self.private_key,
            chain=self.config[AutomaticModules.bridge_in]["bridge_in_chain"],
        )
        if not await self.execute_func_with_retries(
            func=layerswap.bridge,
            func_kwargs={
                "to_chain": config["to_chain"],
                "min_amount": config["min_amount"],
                "max_amount": config["max_amount"],
                "decimal": config["decimal"],
                "all_amount": config["all_amount"],
                "min_percent": config["min_percent"],
                "max_percent": config["max_percent"],
            },
            module_name="LayerSwap bridge in",
        ):
            raise ValueError("LayerSwap bridge in failed")

        return True

    async def layerswap_bridge_out(self):
        try:
            amount = await self.get_amount_to_bridge_out()
        except ValueError as e:
            logger.info(
                f"[{self.account_id}][{self.address}] | Balance is too low to bridge out, skipping"
            )
            return True

        layerswap = LayerSwap(self.account_id, self.private_key, chain="scroll")
        if not await self.execute_func_with_retries(
            func=layerswap.bridge,
            func_kwargs={
                "to_chain": self.config[AutomaticModules.bridge_out][
                    "bridge_out_chain"
                ],
                "min_amount": amount,
                "max_amount": amount,
                "decimal": 5,
                "all_amount": False,
                "min_percent": 0,
                "max_percent": 0,
            },
            module_name="LayerSwap bridge out",
        ):
            raise ValueError("LayerSwap bridge out failed")

        return True

    async def orbiter_bridge_in(self):
        config = self.modules_config[MODULES_NAMES.bridge_orbiter]

        orbiter = Orbiter(
            self.account_id,
            self.private_key,
            chain=self.config[AutomaticModules.bridge_in]["bridge_in_chain"],
        )
        if not await self.execute_func_with_retries(
            func=orbiter.bridge,
            func_kwargs={
                "to_chain": "scroll",
                "min_amount": config["min_amount"],
                "max_amount": config["max_amount"],
                "decimal": config["decimal"],
                "all_amount": config["all_amount"],
                "min_percent": config["min_percent"],
                "max_percent": config["max_percent"],
            },
            module_name="Orbiter bridge in",
        ):
            raise ValueError("Orbiter bridge in failed")

        return True

    async def orbiter_bridge_out(self):
        try:
            amount = await self.get_amount_to_bridge_out()
        except ValueError as e:
            logger.info(
                f"[{self.account_id}][{self.address}] | Balance is too low to bridge out, skipping"
            )
            return True

        orbiter = Orbiter(self.account_id, self.private_key, chain="scroll")
        if not await self.execute_func_with_retries(
            func=orbiter.bridge,
            func_kwargs={
                "to_chain": self.config[AutomaticModules.bridge_out][
                    "bridge_out_chain"
                ],
                "min_amount": amount,
                "max_amount": amount,
                "decimal": 5,
                "all_amount": False,
                "min_percent": 0,
                "max_percent": 0,
            },
            module_name="Orbiter bridge out",
        ):
            raise ValueError("Orbiter bridge out failed")

        return True

    async def nitro_bridge_in(self):
        config = self.modules_config[MODULES_NAMES.bridge_nitro]

        nitro = Nitro(
            self.account_id,
            self.private_key,
            chain=self.config[AutomaticModules.bridge_in]["bridge_in_chain"],
        )
        if not await self.execute_func_with_retries(
            func=nitro.bridge,
            func_kwargs={
                "to_chain": "scroll",
                "min_amount": config["min_amount"],
                "max_amount": config["max_amount"],
                "decimal": config["decimal"],
                "all_amount": config["all_amount"],
                "min_percent": config["min_percent"],
                "max_percent": config["max_percent"],
            },
            module_name="Nitro bridge in",
        ):
            raise ValueError("Nitro bridge in failed")

        return True

    async def nitro_bridge_out(self):
        try:
            amount = await self.get_amount_to_bridge_out()
        except ValueError as e:
            logger.info(
                f"[{self.account_id}][{self.address}] | Balance is too low to bridge out, skipping"
            )
            return True

        nitro = Nitro(self.account_id, self.private_key, chain="scroll")
        if not await self.execute_func_with_retries(
            func=nitro.bridge,
            func_kwargs={
                "to_chain": self.config[AutomaticModules.bridge_out][
                    "bridge_out_chain"
                ],
                "min_amount": amount,
                "max_amount": amount,
                "decimal": 5,
                "all_amount": False,
                "min_percent": 0,
                "max_percent": 0,
            },
            module_name="Nitro bridge out",
        ):
            raise ValueError("Nitro bridge out failed")

        return True

    async def native_bridge_in(self):
        config = self.modules_config[MODULES_NAMES.bridge_in_scroll]

        scroll = Scroll(self.account_id, self.private_key, "ethereum")
        if not await self.execute_func_with_retries(
            func=scroll.deposit,
            func_kwargs={
                "min_amount": config["min_amount"],
                "max_amount": config["max_amount"],
                "decimal": config["decimal"],
                "all_amount": config["all_amount"],
                "min_percent": config["min_percent"],
                "max_percent": config["max_percent"],
            },
            module_name="Native bridge in",
        ):
            raise ValueError("Native bridge in failed")

        return True

    async def native_bridge_out(self):
        try:
            amount = await self.get_amount_to_bridge_out()
        except ValueError as e:
            logger.info(
                f"[{self.account_id}][{self.address}] | Balance is too low to bridge out, skipping"
            )
            return True

        config = self.modules_config[MODULES_NAMES.bridge_out_scroll]

        scroll = Scroll(self.account_id, self.private_key, "scroll")
        if not await self.execute_func_with_retries(
            func=scroll.withdraw,
            func_kwargs={
                "min_amount": amount,
                "max_amount": amount,
                "decimal": config["decimal"],
                "all_amount": False,
                "min_percent": 0,
                "max_percent": 0,
            },
            module_name="Native bridge out",
        ):
            raise ValueError("Native bridge out failed")

        return True

    async def get_amount_to_bridge_out(self):
        balance_wei = await self.w3.eth.get_balance(self.address)
        balance = float(Web3.from_wei(balance_wei, "ether"))

        amount_to_leave = round(
            random.uniform(
                self.config["min_amount_leave_on_scroll"],
                self.config["max_amount_leave_on_scroll"],
            ),
            5,
        )

        if balance <= amount_to_leave:
            raise ValueError(
                f"Not enough ETH to bridge out | balance={balance} | min_balance_eth={self.config['min_balance_eth']}"
            )

        return balance - amount_to_leave

    def get_swappable_tokens(self, config):
        tokens = set()
        for module_name in config["services"]:
            module = SWAP_MODULES[module_name]
            for token in module["tokens"].keys():
                tokens.add(token)
        return tokens

    def _remove_module_entries(self, module_name, quantity, all=False):
        removed = 0

        self.modules_entries = [
            module_entry
            for module_entry in self.modules_entries
            if module_entry.module_name != module_name
            or ((removed := removed + 1) > quantity and not all)
        ]

    def _configure(self, modules):
        if self.config[AutomaticModules.bridge_in]["bridge_in_service"] == "native":
            self.bridge_in = self.native_bridge_in
        elif self.config[AutomaticModules.bridge_in]["bridge_in_service"] == "orbiter":
            self.bridge_in = self.orbiter_bridge_in
        elif (
            self.config[AutomaticModules.bridge_in]["bridge_in_service"] == "layerswap"
        ):
            self.bridge_in = self.layerswap_bridge_in
        elif self.config[AutomaticModules.bridge_in]["bridge_in_service"] == "nitro":
            self.bridge_in = self.nitro_bridge_in
        else:
            raise ValueError(
                f"Unknown bridge_in_service: {self.config[AutomaticModules.bridge_in]['bridge_in_service']}"
            )
        if self.config[AutomaticModules.bridge_out]["bridge_out_service"] == "native":
            self.bridge_out = self.native_bridge_out
        elif (
            self.config[AutomaticModules.bridge_out]["bridge_out_service"] == "orbiter"
        ):
            self.bridge_out = self.orbiter_bridge_out
        elif (
            self.config[AutomaticModules.bridge_out]["bridge_out_service"]
            == "layerswap"
        ):
            self.bridge_out = self.layerswap_bridge_out
        elif self.config[AutomaticModules.bridge_out]["bridge_out_service"] == "nitro":
            self.bridge_out = self.nitro_bridge_out
        else:
            raise ValueError(
                f"Unknown bridge_out_service: {self.config[AutomaticModules.bridge_out]['bridge_out_service']}"
            )

        for module_name in modules:
            quantity = random.randint(
                self.config[module_name]["min_quantity"],
                self.config[module_name]["max_quantity"],
            )

            if module_name in (
                AutomaticModules.wrap_unwrap_eth,
                AutomaticModules.aave,
                AutomaticModules.layerbank,
            ):
                quantity *= 2

            config = self.config[module_name]
            config["total_quantity"] = quantity
            config["performed_quantity"] = 0

            entry = self.ModuleEntry(module_name, config)

            for _ in range(quantity):
                self.modules_entries.append(entry)
