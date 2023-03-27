from dotenv import load_dotenv
import os
load_dotenv()

# NOTE: you must create a .env file in the same directory as this file and add your API key to it
# For example, create a file called ".env" and put API_KEY=your_api_key in it
API_KEY = os.getenv('API_KEY')
DELTA_TIME = 30
TO_DATE_LESS = 0
STOCK_TICKER = 'AMD' # ticker to backtest
CRYPTO_PAIR = 'BINANCE:BTCUSDT' # crypto to backtest
USE_CRYPTO = True # set to True to use crypto, set to False to use stocks
INTERVAL = '15' # the amount of time in one candle, valid options are '1' '5' '15' '30' '60' 'D' 'W' 'M'
TAKER_FEE = 0.001 # the fee for market orders as a decimal
MAKER_FEE = 0.000 # the fee for limit orders as a decimal
POSITION_LIMIT = 100 # at any given timestamp, this is the maximum long or short position you can have
                     # for example, if POSITION_LIMIT = 100, and on this timestamp you have 50 long shares, you can only
                     # buy 50 more shares, but you can sell 150 shares
                     # NOTE: this is just per timestamp, so you can have pending limit orders that eventually get filled
                     # and bring your position above this limit
STRATEGY_NAME = 'ExampleMarketOrderStrategy' # the name of the strategy to backtest, must be in the Strategies folder and should not include the .py extension
