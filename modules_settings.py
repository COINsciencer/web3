import asyncio
from config import AUTOMATIC_MODE
from modules import *
from modules.automatic import Automatic, AutomaticModules
from settings import (
    MAX_ALL_AMOUNT_ETH_PERCENT,
    MIN_ALL_AMOUNT_ETH_PERCENT,
    OKX_CREDENTIALS,
    SLEEP_MAX,
    SLEEP_MIN,
)


class Chains(str, enum.Enum):
    ethereum = "ethereum"
    arbitrum = "arbitrum"
    optimism = "optimism"
    zksync = "zksync"
    base = "base"
    scroll = "scroll"
    linea = "linea"


MODULES_CONFIG = {
    MODULES_NAMES.okx_withdraw: {
        # Withdraw from OKX
        # NOT USED IN AUTOMATION MODE
        "dst_chain": Chains.linea,  # destination chain (zksync, ethereum, polygon_zkevm, arbitrum, optimism)
        # USED IN MANUAL AND AUTOMATION MODE
        "min_amount": 0.1,  # minimal amount to withdraw
        "max_amount": 0.1,  # maximal amount to withdraw
        "token": "ETH",  # token to withdraw
        "transfer_from_subaccounts": True,  # transfer from subaccounts
        "credentials": OKX_CREDENTIALS,  # okx credentials
    },
    MODULES_NAMES.okx_deposit: {
        # Deposit to OKX
        # NOT USED IN AUTOMATION MODE
        "src_chain": Chains.linea,  # source chain
        # USED IN MANUAL AND AUTOMATION MODE
        "min_amount_left": 0,  # minimal amount to leave on wallet
        "max_amount_left": 0,  # maximal amount to leave on wallet
        "credentials": OKX_CREDENTIALS,  # okx credentials
    },
    MODULES_NAMES.bridge_in_scroll: {
        # Deposit to scroll using official bridge
        # USED IN MANUAL AND AUTOMATION MODE on bridge_in
        "min_amount": 0.001,  # minimal amount to bridge
        "max_amount": 0.002,  # maximal amount to bridge
        "decimal": 4,  # token decimal
        "all_amount": True,  # bridge configured % ETH
        "min_percent": 100,  # minimal of how many percents all_amount will bridge from ETH
        "max_percent": 100,  # maximal of how many percents all_amount will bridge from ETH
    },
    MODULES_NAMES.bridge_out_scroll: {
        # Withdraw from scroll using official bridge
        # NOT USED IN AUTOMATION MODE
        "min_amount": 0.001,  # minimal amount to bridge
        "max_amount": 0.002,  # maximal amount to bridge
        "all_amount": True,  # bridge configured % ETH
        "min_percent": 100,  # minimal of how many percents all_amount will bridge from ETH
        "max_percent": 100,  # maximal of how many percents all_amount will bridge from ETH
        # USED IN MANUAL AND AUTOMATION MODE
        "decimal": 4,  # token decimal
    },
    MODULES_NAMES.bridge_orbiter: {
        # Bridge using orbiter
        # NOT USED IN AUTOMATION MODE
        "from_chain": Chains.linea,
        "to_chain": Chains.scroll,
        # USED IN MANUAL AND AUTOMATION MODE on bridge_in
        "min_amount": 0.12,  # minimal amount to bridge
        "max_amount": 0.12,  # maximal amount to bridge
        "decimal": 4,  # token decimal
        "all_amount": True,  # bridge configured % ETH
        "min_percent": 100,  # minimal of how many percents all_amount will bridge from ETH
        "max_percent": 100,  # maximal of how many percents all_amount will bridge from ETH
    },
    MODULES_NAMES.bridge_layerswap: {
        # Bridge using layerswap
        # NOT USED IN AUTOMATION MODE
        "from_chain": Chains.arbitrum,  # NO LINEA SUPPORT
        "to_chain": Chains.scroll,  # NO LINEA SUPPORT
        # USED IN MANUAL AND AUTOMATION MODE on bridge_in
        "min_amount": 0.02,  # minimal amount to bridge
        "max_amount": 0.022,  # maximal amount to bridge
        "decimal": 4,  # token decimal
        "all_amount": True,  # bridge configured % ETH
        "min_percent": 100,  # minimal of how many percents all_amount will bridge from ETH
        "max_percent": 100,  # maximal of how many percents all_amount will bridge from ETH
    },
    MODULES_NAMES.bridge_nitro: {
        # Bridge using layerswap
        # NOT USED IN AUTOMATION MODE
        "from_chain": Chains.arbitrum,
        "to_chain": Chains.scroll,
        # USED IN MANUAL AND AUTOMATION MODE on bridge_in
        "min_amount": 0.001,  # minimal amount to bridge
        "max_amount": 0.002,  # maximal amount to bridge
        "decimal": 4,  # token decimal
        "all_amount": True,  # bridge configured % ETH
        "min_percent": 100,  # minimal of how many percents all_amount will bridge from ETH
        "max_percent": 100,  # maximal of how many percents all_amount will bridge from ETH
    },
    MODULES_NAMES.wrap_eth: {
        # Wrap ETH
        # USED IN MANUAL AND AUTOMATION MODE
        "min_amount": 0.0005,  # minimal amount to wrap
        "max_amount": 0.0005,  # maximal amount to wrap
        "decimal": 4,  # token decimal
        "all_amount": True,  # wrap configured % ETH
        "min_percent": MIN_ALL_AMOUNT_ETH_PERCENT,  # minimal of how many percents all_amount will swap from ETH
        "max_percent": MAX_ALL_AMOUNT_ETH_PERCENT,  # maximal of how many percents all_amount will swap from ETH
    },
    MODULES_NAMES.unwrap_eth: {
        # Unwrap ETH
        # NOT USED IN AUTOMATION MODE
        "min_amount": 0.0005,  # minimal amount to wrap
        "max_amount": 0.0005,  # maximal amount to wrap
        "decimal": 4,  # token decimal
        "all_amount": True,  # wrap configured % ETH
        "min_percent": 100,  # minimal of how many percents all_amount will swap from ETH
        "max_percent": 100,  # maximal of how many percents all_amount will swap from ETH
    },
    MODULES_NAMES.swap_skydrome: {
        # Swap using skydrome
        # NOT USED IN AUTOMATION MODE
        "from_token": "USDC",  # Choose SOURCE token ETH, USDC | Select one
        "to_token": "ETH",  # Choose DESTINATION token ETH, USDC | Select one
        "all_amount": True,  # Swap all amount (between min_percent and max_percent)
        "min_percent": MIN_ALL_AMOUNT_ETH_PERCENT,  # minimal of how many percents all_amount will swap from ETH
        "max_percent": MAX_ALL_AMOUNT_ETH_PERCENT,  # maximal of how many percents all_amount will swap from ETH
        # USED IN MANUAL AND AUTOMATION MODE
        "min_amount": 0.001,  # minimal amount to swap in ETH
        "max_amount": 0.002,  # maximal amount to swap in ETH
        "decimal": 6,
        "slippage": 0.1,  # slippage in %
    },
    MODULES_NAMES.swap_zebra: {
        # Swap using Zebra
        # NOT USED IN AUTOMATION MODE
        # Don't use stable coin in from and to token | from_token USDC to_token USDT DON'T WORK!!!
        "from_token": "USDC",  # Choose SOURCE token ETH, USDT, USDC | Select one
        "to_token": "ETH",  # Choose DESTINATION token ETH, USDT, USDC | Select one
        "all_amount": True,  # Swap all amount (between min_percent and max_percent)
        "min_percent": MIN_ALL_AMOUNT_ETH_PERCENT,  # minimal of how many percents all_amount will swap from ETH
        "max_percent": MAX_ALL_AMOUNT_ETH_PERCENT,  # maximal of how many percents all_amount will swap from ETH
        # USED IN MANUAL AND AUTOMATION MODE
        "decimal": 6,
        "slippage": 0.1,  # slippage in %
        "min_amount": 0.001,  # minimal amount to swap in ETH
        "max_amount": 0.002,  # maximal amount to swap in ETH
    },
    MODULES_NAMES.swap_syncswap: {
        # Swap using SyncSwap
        # NOT USED IN AUTOMATION MODE
        # Don't use stable coin in from and to token | from_token USDC to_token USDT DON'T WORK!!!
        "from_token": "USDC",  # Choose SOURCE token ETH, USDT, USDC | Select one
        "to_token": "ETH",  # Choose DESTINATION token ETH, USDT, USDC | Select one
        "all_amount": True,  # Swap all amount (between min_percent and max_percent)
        "min_percent": MIN_ALL_AMOUNT_ETH_PERCENT,  # minimal of how many percents all_amount will swap from ETH
        "max_percent": MAX_ALL_AMOUNT_ETH_PERCENT,  # maximal of how many percents all_amount will swap from ETH
        # USED IN MANUAL AND AUTOMATION MODE
        "min_amount": 0.001,  # minimal amount to swap in ETH
        "max_amount": 0.002,  # maximal amount to swap in ETH
        "decimal": 6,
        "slippage": 0.1,  # slippage in %
    },
    MODULES_NAMES.swap_xyswap: {
        # Swap using XYSwap
        # NOT USED IN AUTOMATION MODE
        "from_token": "USDC",  # Choose SOURCE token ETH, WETH, USDBC | Select one
        "to_token": "ETH",  # Choose DESTINATION token ETH, WETH, USDBC | Select one
        "all_amount": True,  # Swap all amount (between min_percent and max_percent)
        "min_percent": MIN_ALL_AMOUNT_ETH_PERCENT,  # minimal of how many percents all_amount will swap from ETH
        "max_percent": MAX_ALL_AMOUNT_ETH_PERCENT,  # maximal of how many percents all_amount will swap from ETH
        # USED IN MANUAL AND AUTOMATION MODE
        "min_amount": 0.001,  # minimal amount to swap in ETH
        "max_amount": 0.002,  # maximal amount to swap in ETH
        "decimal": 6,
        "slippage": 0.1,  # slippage in %
    },
    MODULES_NAMES.deposit_aave: {
        # Deposit to Aave
        # NOT USED IN AUTOMATION MODE
        "min_amount": 0.001,  # minimal amount to deposit
        "max_amount": 0.002,  # maximal amount to deposit
        "sleep_from": 20,  # minimal sleep in seconds between deposit and withdraw
        "sleep_to": 4000,  # maximal sleep in seconds between deposit and withdraw
        "decimal": 4,  # token decimal
        "make_withdraw": True,  # make withdraw after deposit
        "all_amount": True,  # deposit configured % ETH
        # USED IN MANUAL AND AUTOMATION MODE
        "min_percent": MIN_ALL_AMOUNT_ETH_PERCENT,  # minimal of how many percents all_amount will swap from ETH
        "max_percent": MAX_ALL_AMOUNT_ETH_PERCENT,  # maximal of how many percents all_amount will swap from ETH
    },
    MODULES_NAMES.mint_bridge_l2telegraph: {
        # Mint NFT and bridge NFT on L2Telegraph
        # NOT USED IN AUTOMATION MODE
        "sleep_from": SLEEP_MIN,  # minimal sleep in seconds between mint and bridge
        "sleep_to": SLEEP_MAX,  # maximal sleep in seconds between mint and bridge
        # USED IN MANUAL AND AUTOMATION MODE
        # availiable chaines: bsc, optimism, avalanche, arbitrum, polygon, linea
        "use_chain": ["linea", "bsc"],
    },
    MODULES_NAMES.send_message_l2telegraph: {
        # Send message with L2Telegraph
        # USED IN MANUAL AND AUTOMATION MODE
        # available chains: bsc, optimism, avalanche, arbitrum, polygon, linea, moonbeam, kava, telos, klaytn, gnosis, moonriver
        "use_chain": ["gnosis", "moonriver"]
    },
    MODULES_NAMES.deposit_layerbank: {
        # Deposit to Aave
        # NOT USED IN AUTOMATION MODE
        "min_amount": 0.001,  # minimal amount to deposit
        "max_amount": 0.002,  # maximal amount to deposit
        "sleep_from": SLEEP_MIN,  # minimal sleep in seconds between deposit and withdraw
        "sleep_to": SLEEP_MAX,  # maximal sleep in seconds between deposit and withdraw
        "decimal": 4,  # token decimal
        "make_withdraw": True,  # make withdraw after deposit
        "all_amount": True,  # deposit configured % ETH
        # USED IN MANUAL AND AUTOMATION MODE
        "min_percent": MIN_ALL_AMOUNT_ETH_PERCENT,  # minimal of how many percents all_amount will swap from ETH
        "max_percent": MAX_ALL_AMOUNT_ETH_PERCENT,  # maximal of how many percents all_amount will swap from ETH
    },
    MODULES_NAMES.mint_nfts2me: {
        # Mint NFTs on NFTs2Me
        # USED IN MANUAL AND AUTOMATION MODE
        # NFT contract addresses and prices
        "contracts": {
            "0xb96E802e8aa317A021DA6BDf20C959d340DAAAd4": 0,
            "0x7ae31829a9399f9aBb87BE3F1A92bd7cf9964132": 0.00001,
            "0xfe5c0e5e99886d9775244462187b126f13c00800": 0,
            "0x5C9911c0536b12d0A3B9af59803B854b30bb6A7F": 0.0000149,
            "0x2011054D72aBCa651532EFc5BEF4E95475C2CF4F": 0.0000149,
            "0x3039ae1575A0118db969A529Efa5a87989D5ABc9": 0.000002,
        }
    },
    MODULES_NAMES.mint_zerius: {
        # Mint NFTs on Zerius and bridge them
        # USED IN MANUAL AND AUTOMATION MODE
        # Disclaimer - The Mint function should be called "mint", to make sure of this, look at the name in Rabby Wallet or in explorer
        "chains": [
            "zora"
        ],  # list chains for random chain bridge: arbitrum, optimism, polygon, bsc, avalanche, zora
        "sleep_from": SLEEP_MIN,  # minimal sleep in seconds between mint and bridge
        "sleep_to": SLEEP_MAX,  # maximal sleep in seconds between mint and bridge
    },
    MODULES_NAMES.mint_zkstars: {
        # Mint NFTs on ZKStars
        # NOT USED IN AUTOMATION MODE
        "mint_min": 1,  # minimal amount to mint
        "mint_max": 3,  # maximal amount to mint
        "mint_all": False,  # mint all nfts
        "sleep_from": SLEEP_MIN,  # minimal sleep in seconds between mint and bridge
        "sleep_to": SLEEP_MAX,  # maximal sleep in seconds between mint and bridge
        # USED IN MANUAL AND AUTOMATION MODE
        "contracts": [
            "0x609c2f307940b8f52190b6d3d3a41c762136884e",
            "0x16c0baa8a2aa77fab8d0aece9b6947ee1b74b943",
            "0xc5471e35533e887f59df7a31f7c162eb98f367f7",
            "0xf861f5927c87bc7c4781817b08151d638de41036",
            "0x954e8ac11c369ef69636239803a36146bf85e61b",
            "0xa576ac0a158ebdcc0445e3465adf50e93dd2cad8",
            "0x17863384c663c5f95e4e52d3601f2ff1919ac1aa",
            "0x4c2656a6d1c0ecac86f5024e60d4f04dbb3d1623",
            "0x4e86532cedf07c7946e238bd32ba141b4ed10c12",
            "0x6b9db0ffcb840c3d9119b4ff00f0795602c96086",
            "0x10d4749bee6a1576ae5e11227bc7f5031ad351e4",
            "0x373148e566e4c4c14f4ed8334aba3a0da645097a",
            "0xdacbac1c25d63b4b2b8bfdbf21c383e3ccff2281",
            "0x2394b22b3925342f3216360b7b8f43402e6a150b",
            "0xf34f431e3fc0ad0d2beb914637b39f1ecf46c1ee",
            "0x6f1e292302dce99e2a4681be4370d349850ac7c2",
            "0xa21fac8b389f1f3717957a6bb7d5ae658122fc82",
            "0x1b499d45e0cc5e5198b8a440f2d949f70e207a5d",
            "0xec9bef17876d67de1f2ec69f9a0e94de647fcc93",
            "0x5e6c493da06221fed0259a49beac09ef750c3de1",
        ],
    },
    MODULES_NAMES.deploy_contract: {
        # Deploy contract
        # USED IN MANUAL AND AUTOMATION MODE
        # Paths to contracts to deploy. Will be chosen randomly
        "contracts": ["data/deploy/bytecode.txt"]
    },
}


# Config for automation mode
# !!! DON'T FORGET TO ALSO CONFIGURE MODULES_CONFIG !!!
AUTOMATIC_CONFIG = {
    "sleep_at_start": True,  # Script will sleep after bridge and before first transaction
    "okx_withdraw_enabled": True,  # Withdraw funds from OKX to EVM or not
    "okx_deposit_enabled": True,  # Deposit funds to OKX from EVM to okx or not
    "swap_all_tokens_to_eth_before_withdraw": True,  # Swap all tokens to ETH before withdraw from scroll
    # !IMPORTANT NOTICE
    # OKX WILL WITHDRAW FUNDS TO THE CHAIN SPECIFIED IN THE BRIDGE_IN MODULE
    # OKX WILL DEPOSIT FUNDS FROM THE CHAIN SPECIFIED IN THE BRIDGE_OUT MODULE
    "min_balance_eth": 0.0025,  # minimal amount to not swap on scroll in ETH (will always leave this amount for fees)
    "min_balance_usdc": 0.1,  # not to swap when balance is smaller than this amount
    "min_balance_usdt": 0.1,  # not to swap when balance is smaller than this amount
    "min_balance_weth": 0.00005,  # not to swap when balance is smaller than this amount
    "min_amount_leave_on_scroll": 0.011,  # minimal amount to leave on scroll when bridging out
    "max_amount_leave_on_scroll": 0.012,  # maximal amount to leave on scroll when bridging out
    # better to keep True, otherwise might lead to stuck
    "skip_if_failed": True,  # if swap failed it will be counted as performed after retries
    AutomaticModules.bridge_in: {
        "bridge_in_enabled": True,  # Bridge funds from EVM to scroll or not
        "bridge_in_service": "orbiter",  # Choose bridge in scroll service: native, nitro, orbiter, layerswap
        # !IMPORTANT NOTICE
        # OKX WILL WITHDRAW FUNDS TO THE bridge_in_chain
        # If bridge_in_service == "native", then ethereum only!
        "bridge_in_chain": Chains.linea,
    },
    AutomaticModules.bridge_out: {
        "bridge_out_enabled": True,  # Bridge funds from scroll to EVM or not
        "bridge_out_service": "orbiter",  # Choose bridge out of scroll service: native, nitro, orbiter, layerswap
        # !IMPORTANT NOTICE
        # OKX WILL DEPOSIT FUNDS FROM THE bridge_out_chain
        # If bridge_out_service == "native", then ethereum only!
        "bridge_out_chain": Chains.linea,
    },
    AutomaticModules.swaps: {
        "first_swap_from_eth": False,  # first swap will be from ETH
        "services": [
            MODULES_NAMES.swap_skydrome,
            MODULES_NAMES.swap_syncswap,
            MODULES_NAMES.swap_zebra,
            MODULES_NAMES.swap_xyswap,
        ],  # Select any available swap services or comment existing if you don't need it
        "min_quantity": 4,  # ! MINIMUM 2
        "max_quantity": 6,
        "decimal": 6,  # do not change
        "min_amount": 0.007,  # minimal amount to swap on scroll in ETH
        "max_amount": 0.008,  # maximal amount to swap on scroll in ETH
    },
    AutomaticModules.wrap_unwrap_eth: {
        # Quantity of wrap and unwrap eth. 1 quantity = 2 transactions
        "min_quantity": 0,
        "max_quantity": 1,
    },
    AutomaticModules.send_email: {
        "min_quantity": 0,
        "max_quantity": 1,
    },
    AutomaticModules.aave: {
        # Quantity of deposit and withdraw on aave. 1 quantity = 2 transactions
        "min_quantity": 2,
        "max_quantity": 3,
    },
    AutomaticModules.layerbank: {
        # Quantity of deposit and withdraw on layerbank. 1 quantity = 2 transactions
        "min_quantity": 1,
        "max_quantity": 2,
    },
    AutomaticModules.mint_bridge_l2_telegraph: {
        # COSTS 0.0005 ETH + gas
        "min_quantity": 0,
        "max_quantity": 1,
        "bridge": False,  # bridge nft after mint
    },
    AutomaticModules.l2telegraph_send_message: {
        # COSTS 0.0003 ETH + gas
        "min_quantity": 0,
        "max_quantity": 1,
    },
    AutomaticModules.mint_nfts2me: {
        "min_quantity": 0,
        "max_quantity": 1,
    },
    AutomaticModules.mint_zerius: {
        "min_quantity": 0,
        "max_quantity": 1,
    },
    AutomaticModules.mint_zkstars: {
        "min_quantity": 0,
        "max_quantity": 1,
    },
    AutomaticModules.rubyscore_vote: {
        "min_quantity": 0,
        "max_quantity": 1,
    },
    AutomaticModules.deploy_contract: {
        "min_quantity": 0,
        "max_quantity": 1,
    },
    AutomaticModules.create_gnosis_safe: {
        "min_quantity": 0,
        "max_quantity": 1,
    },
    AutomaticModules.create_omnisea_collection: {
        "min_quantity": 0,
        "max_quantity": 1,
    },
    AutomaticModules.mint_l2pass: {
        "min_quantity": 0,
        "max_quantity": 1,
    },
}


async def automatic(account_id, key, okx_address, *args, **kwargs):
    """
    Automatic module: Automatically performs the specified number of transactions
    interacting with random swaps, contracts etc..
    ______________________________________________________
    modules - list of modules to use. Select any from:
    AutomaticModules.swaps
    AutomaticModules.mint_bridge_l2_telegraph
    AutomaticModules.wrap_unwrap_eth
    AutomaticModules.l2telegraph_send_message
    AutomaticModules.rubyscore_vote
    AutomaticModules.send_email
    AutomaticModules.aave
    AutomaticModules.mint_nfts2me
    AutomaticModules.mint_zerius
    AutomaticModules.mint_zkstars
    AutomaticModules.mint_l2pass
    AutomaticModules.create_omnisea_collection
    AutomaticModules.create_gnosis_safe
    AutomaticModules.deploy_contract
    AutomaticModules.layerbank
    """

    modules = [
        AutomaticModules.swaps,
        AutomaticModules.wrap_unwrap_eth,
        AutomaticModules.send_email,
        AutomaticModules.mint_bridge_l2_telegraph,
        AutomaticModules.l2telegraph_send_message,
        AutomaticModules.rubyscore_vote,
        AutomaticModules.aave,
        AutomaticModules.mint_l2pass,
        AutomaticModules.mint_nfts2me,
        AutomaticModules.mint_zerius,
        AutomaticModules.mint_zkstars,
        AutomaticModules.create_omnisea_collection,
        AutomaticModules.create_gnosis_safe,
        AutomaticModules.deploy_contract,
        AutomaticModules.layerbank,
    ]

    automatic = Automatic(
        account_id=account_id,
        private_key=key,
        okx_address=okx_address,
        modules=modules,
        config=AUTOMATIC_CONFIG,
        modules_config=MODULES_CONFIG,
    )
    AUTOMATIC_MODE.set(True)

    await automatic.run()


async def okx_deposit(account_id, key, okx_address, *args, **kwargs):
    """
    Deposit from wallet to OKX
    ______________________________________________________

    Deposits ETH only!
    """

    config = MODULES_CONFIG[MODULES_NAMES.okx_deposit]

    okx = OKX(
        account_id=account_id,
        private_key=key,
        chain=config["src_chain"],
        credentials=config["credentials"],
    )

    await okx.deposit(
        address=okx_address,
        min_amount_left=config["min_amount_left"],
        max_amount_left=config["max_amount_left"],
    )


async def okx_withdraw(account_id, key, *args, **kwargs):
    """Withdraw from OKX"""

    config = MODULES_CONFIG[MODULES_NAMES.okx_withdraw]

    okx = OKX(
        account_id=account_id,
        private_key=key,
        chain=config["dst_chain"],
        credentials=config["credentials"],
    )
    await okx.withdraw(
        min_amount=config["min_amount"],
        max_amount=config["max_amount"],
        token=config["token"],
        transfer_from_subaccounts=config["transfer_from_subaccounts"],
    )


async def deposit_scroll(account_id, key, *args, **kwargs):
    """
    Deposit from official bridge
    """

    config = MODULES_CONFIG[MODULES_NAMES.bridge_in_scroll]
    scroll = Scroll(account_id, key, "ethereum")
    await scroll.deposit(**config)


async def withdraw_scroll(account_id, key, *args, **kwargs):
    """
    Withdraw from official bridge
    """

    config = MODULES_CONFIG[MODULES_NAMES.bridge_out_scroll]

    scroll = Scroll(account_id, key, "scroll")
    await scroll.withdraw(**config)


async def bridge_orbiter(account_id, key, *args, **kwargs):
    """
    Bridge from orbiter
    """

    config = MODULES_CONFIG[MODULES_NAMES.bridge_orbiter]

    orbiter = LayerSwap(
        account_id=account_id, private_key=key, chain=config.pop("from_chain")
    )
    await orbiter.bridge(**config)


async def bridge_layerswap(account_id, key, *args, **kwargs):
    """
    Bridge from Layerswap
    """

    config = MODULES_CONFIG[MODULES_NAMES.bridge_layerswap]

    layerswap = LayerSwap(
        account_id=account_id, private_key=key, chain=config.pop("from_chain")
    )
    await layerswap.bridge(**config)


async def bridge_nitro(account_id, key, *args, **kwargs):
    """
    Bridge from nitro
    """

    config = MODULES_CONFIG[MODULES_NAMES.bridge_nitro]

    nitro = Nitro(
        account_id=account_id, private_key=key, chain=config.pop("from_chain")
    )
    await nitro.bridge(**config)


async def wrap_eth(account_id, key, *args, **kwargs):
    """
    Wrap ETH
    """

    config = MODULES_CONFIG[MODULES_NAMES.wrap_eth]

    scroll = Scroll(account_id, key, "scroll")
    await scroll.wrap_eth(**config)


async def unwrap_eth(account_id, key, *args, **kwargs):
    """
    Unwrap ETH
    """

    config = MODULES_CONFIG[MODULES_NAMES.unwrap_eth]

    scroll = Scroll(account_id, key, "scroll")
    await scroll.unwrap_eth(**config)


async def swap_skydrome(account_id, key, *args, **kwargs):
    """
    Make swap on Skydrome
    """

    config = MODULES_CONFIG[MODULES_NAMES.swap_skydrome]

    skydrome = Skydrome(account_id, key)
    await skydrome.swap(**config)


async def swap_zebra(account_id, key, *args, **kwargs):
    """
    Make swap on Zebra
    """

    config = MODULES_CONFIG[MODULES_NAMES.swap_zebra]

    zebra = Zebra(account_id, key)
    await zebra.swap(**config)


async def swap_syncswap(account_id, key, *args, **kwargs):
    """
    Make swap on SyncSwap
    """

    config = MODULES_CONFIG[MODULES_NAMES.swap_syncswap]

    syncswap = SyncSwap(account_id, key)
    await syncswap.swap(**config)


async def swap_xyswap(account_id, key, *args, **kwargs):
    """
    Make swap on XYSwap
    """

    config = MODULES_CONFIG[MODULES_NAMES.swap_xyswap]

    xyswap = XYSwap(account_id, key)
    await xyswap.swap(**config)


async def deposit_layerbank(account_id, key, *args, **kwargs):
    """
    Make deposit on LayerBank
    """
    config = MODULES_CONFIG[MODULES_NAMES.deposit_layerbank]

    layerbank = LayerBank(account_id, key)
    await layerbank.deposit(**config)


async def deposit_aave(account_id, key, *args, **kwargs):
    """
    Make deposit on Aave
    """
    config = MODULES_CONFIG[MODULES_NAMES.deposit_aave]

    aave = Aave(account_id, key)
    await aave.deposit(**config)


async def mint_zerius(account_id, key, *args, **kwargs):
    """
    Mint + bridge Zerius NFT
    """

    config = MODULES_CONFIG[MODULES_NAMES.mint_zerius]

    zerius = Zerius(account_id, key)
    await zerius.bridge_mint(**config)


async def mint_l2pass(account_id, key, *args, **kwargs):
    """
    Mint L2Pass NFT
    """

    l2pass = L2Pass(account_id, key)
    await l2pass.mint()


async def mint_nft(account_id, key, *args, **kwargs):
    """
    Mint NFT on NFTS2ME
    """

    config = MODULES_CONFIG[MODULES_NAMES.mint_nfts2me]

    minter = Minter(account_id, key)
    await minter.mint_nft(**config)


async def mint_zkstars(account_id, key, *args, **kwargs):
    """
    Mint ZkStars NFT
    """
    config = MODULES_CONFIG[MODULES_NAMES.mint_zerius]

    zkstars = ZkStars(account_id, key)
    await zkstars.mint(**config)


async def send_message(account_id, key, *args, **kwargs):
    """
    Send message with L2Telegraph
    """
    config = MODULES_CONFIG[MODULES_NAMES.send_message_l2telegraph]

    l2telegraph = L2Telegraph(account_id, key)
    await l2telegraph.send_message(**config)


async def bridge_nft(account_id, key, *args, **kwargs):
    """
    Make mint NFT and bridge NFT on L2Telegraph
    """
    config = MODULES_CONFIG[MODULES_NAMES.mint_bridge_l2telegraph]

    l2telegraph = L2Telegraph(account_id, key)
    await l2telegraph.bridge(**config)


#########################################
########### NO NEED TO CHANGE ###########
#########################################


async def withdraw_layerbank(account_id, key, *args, **kwargs):
    layerbank = LayerBank(account_id, key)
    await layerbank.withdraw()


async def withdraw_aave(account_id, key, *args, **kwargs):
    aave = Aave(account_id, key)
    await aave.withdraw()


async def send_mail(account_id, key, *args, **kwargs):
    dmail = Dmail(account_id, key)
    await dmail.send_mail()


async def create_omnisea(account_id, key, *args, **kwargs):
    omnisea = Omnisea(account_id, key)
    await omnisea.create()


async def create_safe(account_id, key, *args, **kwargs):
    gnosis_safe = GnosisSafe(account_id, key)
    await gnosis_safe.create_safe()


async def deploy_contract(account_id, key, *args, **kwargs):
    deployer = Deployer(account_id, key)
    await deployer.deploy_token()


async def rubyscore_vote(account_id, key, *args, **kwargs):
    rubyscore = RubyScore(account_id, key)
    await rubyscore.vote()


async def nft_origins(account_id, key, *args, **kwargs):
    nft = NftOrigins(account_id, key)
    await nft.mint()
