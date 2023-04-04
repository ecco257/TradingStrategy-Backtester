from dotenv import load_dotenv
import os
from HyperOpt.OptimizeFunctions import byMinDrawdown, byProfit, byNumTrades
import pandas as pd
from typing import Dict, List

load_dotenv()

# NOTE: you must create a .env file in the same directory as this file and add your API key to it
# For example, create a file called ".env" and put API_KEY=your_api_key in it
API_KEY = os.getenv('API_KEY')
DELTA_TIME = 30
TO_DATE_LESS = 0
INTERVAL = '15' # the amount of time in one candle, valid options are '1' '5' '15' '30' '60' 'D' 'W' 'M'
CRYPTO_INTERVAL = '30m' # the amount of time in one candle for crypto (ccxt)
TAKER_FEE = 0.001 # the fee for market orders as a decimal
MAKER_FEE = 0.000 # the fee for limit orders as a decimal
POSITION_LIMITS: Dict[str, int] = { # the maximum number of positions to hold at once for each symbol
    'AMD': 10,
    'BTC/USDT': 1.0,
}
SYMBOLS_TO_BE_TRADED: List[str] = [
    'BTC/USDT',
]
STRATEGY_NAME = 'ExampleMarketOrderStrategy' # the name of the strategy to backtest, must be in the Strategies folder and should not include the .py extension
STRATEGY_HYPERPARAMETERS = {
    'rsi_lookback': 16,
    'rsi_buy_threshold': 24,
    'rsi_sell_threshold': 74,
}
STRATEGY_HYPERPARAMETER_RANGES = { # a dictionary of hyperparameter ranges to be used when running a hyperparameter optimization
    'rsi_lookback': (1, 100),
    'rsi_buy_threshold': (0.0, 50.0),
    'rsi_sell_threshold': (50.0, 100.0),
}
HYPER_OPT_METHODS = [ # the methods used to optimize the hyperparameters. If one method is used 
    byMinDrawdown,
    byProfit,
    byNumTrades,
]
HYPER_OPT_TRIALS = 100 # the number of trials to run when doing a hyperparameter optimization
SYMBOL_TO_OPTIMIZE = 'BTC/USDT' # the symbol to optimize the hyperparameters for. this is needed for things such as pair trading
PRICE_DATA: Dict[str, pd.DataFrame] = None # the price data to use for hyperparameter optimization so that the api is not called multiple times
