MAX_PRIORITY_FEE = {
    "ethereum": 0.01,
    "polygon": 40,
    "arbitrum": 0.1,
    "base": 0.1,
    "zksync": 0.25,
}

LAYERSWAP_API_KEY = ""  # Layerswap API key. Fill in if you want to use LayerSwap

ENABLE_ERROR_TRACEBACK = True  # Enable error tracebacks for debug purposes

# RANDOM WALLETS MODE
RANDOM_WALLET = False  # True or False

RETRIES = 3  # Number of retries

RETRY_DELAY_MIN = 120  # Minimum delay before retry
RETRY_DELAY_MAX = 500  # Maximum delay before retry

SLEEP_MIN = 200  # Minimum sleep time between modules in automation mode
SLEEP_MAX = 1000  # Maximum sleep time between modules in automation mode

MIN_SLEEP_BEFORE_ACCOUNT_START = (
    0 * 60
)  # Minimum sleep time before starting next account
MAX_SLEEP_BEFORE_ACCOUNT_START = (
    180 * 60
)  # Maximum sleep time before starting next account

# GWEI CONTROL MODE
CHECK_GWEI = True  # True or False
MAX_GWEI = 27

THREADS = 2  # Number of threads

GAS_MULTIPLIER = 1.5

MIN_ALL_AMOUNT_ETH_PERCENT = (
    92  # minimal of how many percents all_amount will swap from ETH
)
MAX_ALL_AMOUNT_ETH_PERCENT = (
    95  # maximal of how many percents all_amount will swap from ETH
)


BRIDGE_FEES = {
    "native": {
        "in": 0.0095,
        "out": 0.001,
    },
    "orbiter": 0.0013,
    "nitro": 0.0013,
    "layerswap": 0.0013,
}

OKX_CREDENTIALS = {
    "apikey": "",
    "apisecret": "",
    "passphrase": "",
}
