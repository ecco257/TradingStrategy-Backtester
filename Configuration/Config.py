from dotenv import load_dotenv
import os
import pandas as pd
from typing import Dict, List

load_dotenv()

# the following variables can be changed by the user
#=======================================================================================================================
# NOTE: you must create a .env file in the same directory as this file and add your API key to it
# For example, create a file called ".env" and put API_KEY=your_api_key in it
API_KEY = os.getenv('API_KEY')
DELTA_TIME = 365
TO_DATE_LESS = 0
INTERVAL = 'D' # the amount of time in one candle, valid options are '1' '5' '15' '30' '60' 'D' 'W' 'M'
CRYPTO_INTERVAL = '1h' # the amount of time in one candle for crypto (ccxt); These are the intervals for kucoin exchange, which is currently in use: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 1w
TAKER_FEE = 0.001 # the fee for market orders as a decimal
MAKER_FEE = 0.000 # the fee for limit orders as a decimal
INITIAL_CAPITALS: Dict[str, float] = { # the initial capital to use for each security when backtesting
    'AAPL': 10000.0,
    'BTC/USDT': 10000.0,
}
POSITION_LIMITS: Dict[str, int] = { # the maximum number of positions to hold at once for each symbol
    'AAPL': 100,
    'BTC/USDT': 1.0,
}
SYMBOLS_TO_BE_TRADED: List[str] = [
    'BTC/USDT',
]
STRATEGY_NAME = 'RegimeDetectionStrategy' # the name of the strategy to backtest, must be in the Strategies folder and should not include the .py extension
STRATEGY_HYPERPARAMETERS = {
    'kama_lookback': 14,
    'kama_threshold': 0.026279525839930054,
}
STRATEGY_HYPERPARAMETER_RANGES = { # a dictionary of hyperparameter ranges to be used when running a hyperparameter optimization
    'kama_lookback': (1, 20),
    'kama_threshold': (0.0, 0.1),
}
HYPER_OPT_TRIALS = 100 # the number of trials to run when doing a hyperparameter optimization
SYMBOL_TO_OPTIMIZE = 'BTC/USDT' # the symbol to optimize the hyperparameters for. this is needed for things such as pair trading
SYMBOL_TO_TRAIN = 'BTC/USDT' # the symbol to train the HMM on
NUMBER_OF_HIDDEN_STATES = 2 # the number of hidden states to use for the HMM
COVARIANCE_TYPE = 'full' # the type of covariance to use for the HMM, valid options are 'full', 'tied', 'diag', 'spherical'
NUMBER_OF_TRAINING_ITERATIONS = 1000 # the number of iterations to use when training the HMM
MODEL_TO_USE = 'RegimeDetectionStrategy_BTC_USDT_1' # the name of the HMM stored in Models to use for backtesting (without the .pkl extension). Leave as None to use no HMM
#=======================================================================================================================

# the following variables are set by the program and should not be changed
PRICE_DATA: Dict[str, pd.DataFrame] = None # the price data to use for hyperparameter optimization so that the api is not called multiple times
