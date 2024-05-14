import json

with open("data/rpc.json") as file:
    RPC = json.load(file)

with open("data/abi/erc20_abi.json") as file:
    ERC20_ABI = json.load(file)

with open("data/wallets.txt", "r") as file:
    WALLETS = file.read().splitlines()

with open("data/okx_addresses.txt", "r") as file:
    OKX_ADDRESSES = file.read().splitlines()

with open("data/abi/bridge/deposit.json") as file:
    DEPOSIT_ABI = json.load(file)

with open("data/abi/bridge/withdraw.json") as file:
    WITHDRAW_ABI = json.load(file)

with open("data/abi/bridge/oracle.json") as file:
    ORACLE_ABI = json.load(file)

with open("data/abi/scroll/weth.json") as file:
    WETH_ABI = json.load(file)

with open("data/abi/syncswap/router.json", "r") as file:
    SYNCSWAP_ROUTER_ABI = json.load(file)

with open("data/abi/syncswap/classic_pool.json") as file:
    SYNCSWAP_CLASSIC_POOL_ABI = json.load(file)

with open("data/abi/syncswap/classic_pool_data.json") as file:
    SYNCSWAP_CLASSIC_POOL_DATA_ABI = json.load(file)

with open("data/abi/skydrome/abi.json", "r") as file:
    SKYDROME_ROUTER_ABI = json.load(file)

with open("data/abi/zebra/abi.json", "r") as file:
    ZEBRA_ROUTER_ABI = json.load(file)

with open("data/abi/aave/abi.json", "r") as file:
    AAVE_ABI = json.load(file)

with open("data/abi/layerbank/abi.json", "r") as file:
    LAYERBANK_ABI = json.load(file)

with open("data/abi/zerius/abi.json", "r") as file:
    ZERIUS_ABI = json.load(file)

with open("data/abi/l2pass/abi.json", "r") as file:
    L2PASS_ABI = json.load(file)

with open("data/abi/dmail/abi.json", "r") as file:
    DMAIL_ABI = json.load(file)

with open("data/abi/omnisea/abi.json", "r") as file:
    OMNISEA_ABI = json.load(file)

with open("data/abi/nft2me/abi.json", "r") as file:
    NFTS2ME_ABI = json.load(file)

with open("data/abi/gnosis/abi.json", "r") as file:
    SAFE_ABI = json.load(file)

with open("data/deploy/abi.json", "r") as file:
    DEPLOYER_ABI = json.load(file)

with open("data/abi/zkstars/abi.json", "r") as file:
    ZKSTARS_ABI = json.load(file)

with open("data/abi/rubyscore/abi.json", "r") as file:
    RUBYSCORE_VOTE_ABI = json.load(file)

with open("data/abi/l2telegraph/send_message.json", "r") as file:
    L2TELEGRAPH_MESSAGE_ABI = json.load(file)

with open("data/abi/l2telegraph/bridge_nft.json", "r") as file:
    L2TELEGRAPH_NFT_ABI = json.load(file)

with open("data/abi/nft-origins/abi.json", "r") as file:
    NFT_ORIGINS_ABI = json.load(file)


class AutomaticMode:
    def __init__(self, value: bool) -> None:
        self.value = value

    def set(self, value: bool) -> None:
        self.value = value

    def get(self) -> bool:
        return self.value


AUTOMATIC_MODE = AutomaticMode(False)

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

BRIDGE_CONTRACTS = {
    "deposit": "0xf8b1378579659d8f7ee5f3c929c2f3e332e41fd6",
    "withdraw": "0x4C0926FF5252A435FD19e10ED15e5a249Ba19d79",
    "oracle": "0x987e300fDfb06093859358522a79098848C33852",
}

ORBITER_CONTRACT = "0x80c67432656d59144ceff962e8faf8926599bcf8"

SCROLL_TOKENS = {
    "ETH": "0x5300000000000000000000000000000000000004",
    "WETH": "0x5300000000000000000000000000000000000004",
    "USDT": "0xf55BEC9cafDbE8730f096Aa55dad6D22d44099Df",
    "USDC": "0x06eFdBFf2a14a7c8E15944D1F4A48F9F95F663A4",
}

SYNCSWAP_CONTRACTS = {
    "router": "0x80e38291e06339d10aab483c65695d004dbd5c69",
    "classic_pool": "0x37BAc764494c8db4e54BDE72f6965beA9fa0AC2d",
}

SKYDROME_CONTRACTS = {"router": "0xAA111C62cDEEf205f70E6722D1E22274274ec12F"}

ZEBRA_CONTRACTS = {"router": "0x0122960d6e391478bfe8fb2408ba412d5600f621"}

AMBIENT_CONTRACTS = {
    "router": "0xaaaaaaaacb71bf2c8cae522ea5fa455571a74106",
    "impact": "0xc2c301759B5e0C385a38e678014868A33E2F3ae3",
}

XYSWAP_CONTRACT = {
    "router": "0x22bf2a9fcaab9dc96526097318f459ef74277042",
    "use_ref": True,  # If you use True, you support me 1% of the transaction amount
}

AAVE_CONTRACT = "0xff75a4b698e3ec95e608ac0f22a03b8368e05f5d"

AAVE_WETH_CONTRACT = "0xf301805be1df81102c957f6d4ce29d2b8c056b2a"

LAYERBANK_CONTRACT = "0xec53c830f4444a8a56455c6836b5d2aa794289aa"

LAYERBANK_WETH_CONTRACT = "0x274C3795dadfEbf562932992bF241ae087e0a98C"

ZERIUS_CONTRACT = "0xeb22c3e221080ead305cae5f37f0753970d973cd"

DMAIL_CONTRACT = "0x47fbe95e981c0df9737b6971b451fb15fdc989d9"

OMNISEA_CONTRACT = "0x46ce46951d12710d85bc4fe10bb29c6ea5012077"

SAFE_CONTRACT = "0xa6b71e26c5e0845f74c812102ca7114b6a896ab2"

RUBYSCORE_VOTE_CONTRACT = "0xe10Add2ad591A7AC3CA46788a06290De017b9fB4"

L2TELEGRAPH_MESSAGE_CONTRACT = "0x9f63dbdf90837384872828d1ed6eb424a7f7f939"

L2TELEGRAPH_NFT_CONTRACT = "0xdc60fd9d2a4ccf97f292969580874de69e6c326e"

NFT_ORIGINS_CONTRACT = "0x74670A3998d9d6622E32D0847fF5977c37E0eC91"

L2PASS_CONTRACT = "0x0000049f63ef0d60abe49fdd8bebfa5a68822222"

SCROLL_FEE_INACCURACY = 0.00001
