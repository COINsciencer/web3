import enum

from .aave import Aave
from .account import Account
from .l2pass import L2Pass
from .l2telegraph import L2Telegraph
from .deploy import Deployer
from .nftorigins import NftOrigins
from .nitro import Nitro
from .rubyscore import RubyScore
from .safe import GnosisSafe
from .scroll import Scroll
from .orbiter import Orbiter
from .layerswap import LayerSwap
from .xyswap import XYSwap
from .zebra import Zebra
from .zkstars import ZkStars
from .skydrome import Skydrome
from .syncswap import SyncSwap
from .layerbank import LayerBank
from .zerius import Zerius
from .dmail import Dmail
from .omnisea import Omnisea
from .nfts2me import Minter
from .deploy import Deployer
from .okx import OKX


class MODULES_NAMES(str, enum.Enum):
    okx_deposit = "okx_deposit"
    okx_withdraw = "okx_withdraw"
    bridge_in_scroll = "bridge_in_scroll"
    bridge_out_scroll = "bridge_out_scroll"
    bridge_orbiter = "bridge_orbiter"
    bridge_layerswap = "bridge_layerswap"
    bridge_nitro = "bridge_nitro"
    swap_syncswap = "swap_syncswap"
    swap_zebra = "swap_zebra"
    swap_xyswap = "swap_xyswap"
    deposit_aave = "deposit_aave"
    withdraw_aave = "withdraw_aave"
    swap_skydrome = "swap_skydrome"
    deposit_layerbank = "deposit_layerbank"
    withdraw_layerbank = "withdraw_layerbank"
    wrap_eth = "wrap_eth"
    unwrap_eth = "unwrap_eth"
    mint_nfts2me = "mint_nfts2me"
    mint_l2pass = "mint_l2pass"
    mint_zkstars = "mint_zkstars"
    mint_nft_origins = "mint_nft_origins"
    rubyscore_vote = "rubyscore_vote"
    mint_bridge_l2telegraph = "mint_bridge_l2telegraph"
    send_message_l2telegraph = "send_message_l2telegraph"
    create_gnosis_safe = "create_gnosis_safe"
    mint_zerius = "mint_zerius"
    create_omnisea_collection = "create_omnisea_collection"
    deploy_contract = "deploy_contract"
    send_mail = "send_mail"
    tx_checker = "tx_checker"


SWAP_MODULES = {
    MODULES_NAMES.swap_skydrome: {
        "class": Skydrome,
        "tokens": {
            "ETH": ["USDC", "USDT"],
            "USDC": ["ETH"],
            "USDT": ["ETH"],
        },
    },
    MODULES_NAMES.swap_zebra: {
        "class": Zebra,
        "tokens": {
            "ETH": ["USDC", "USDT"],
            "USDC": ["ETH"],
            "USDT": ["ETH"],
        },
    },
    MODULES_NAMES.swap_syncswap: {
        "class": SyncSwap,
        "tokens": {
            "ETH": ["USDC", "USDT"],
            "USDC": ["ETH"],
            "USDT": ["ETH"],
        },
    },
    MODULES_NAMES.swap_xyswap: {
        "class": XYSwap,
        "tokens": {
            "ETH": ["USDC", "WETH"],
            "USDC": ["ETH"],
            "WETH": ["ETH"],
        },
    },
}
