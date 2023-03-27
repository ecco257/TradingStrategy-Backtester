from dotenv import load_dotenv
import os
load_dotenv()

# NOTE: you must create a .env file in the same directory as this file and add your API key to it
# For example, create a file called ".env" and put API_KEY=your_api_key in it
API_KEY = os.getenv('API_KEY')
DELTA_TIME = 30
TO_DATE_LESS = 0
STOCK_TICKER = 'AMD' # stock ticker to backtest
CRYPTO_PAIR = 'BINANCE:BTCUSDT' # crypto to backtest
USE_CRYPTO = True # set to True to use crypto, set to False to use stocks
INTERVAL = '15' # the amount of time in one candle, valid options are '1' '5' '15' '30' '60' 'D' 'W' 'M'
TAKER_FEE = 0.001 # the fee for market orders as a decimal
MAKER_FEE = 0.000 # the fee for limit orders as a decimal
POSITION_LIMIT = 1 # the maximum gross position size, set to 0 or less for no limit
STRATEGY_NAME = 'ExampleLimitOrderStrategy' # the name of the strategy to backtest, must be in the Strategies folder and should not include the .py extension
STRATEGY_HYPERPARAMETERS = { # a dictionary of hyperparameters to pass to the strategy
    'spread_pct': 0.01,
}
STRATEGY_HYPERPARAMETER_RANGES = { # a dictionary of hyperparameter ranges to be used when running a hyperparameter optimization
    'spread_pct': (0.001, 0.1),
}
HYPER_OPT_TRIALS = 100 # the number of trials to run when doing a hyperparameter optimization