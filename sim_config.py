ticker = 'AAPL' # ticker to analyze
crypto = 'BINANCE:SOLUSDT' # crypto to analyze
use_crypto = True # if True, the crypto will be analyzed instead of the stock
interval = '15' # less than a day means only a month of data, valid options are '1' '5' '15' '30' '60' 'D' 'W' 'M'
transaction_fee = 0.001 # 2% transaction fee default
starting_money = 100000 # $1,000 default
starting_stocks = 0 # 0 stocks default
starting_short_stocks = 0 # 0 stocks default
investment = 50000 # $50 default
adx_sell = 40 # default 40
adx_buy = 20 # default 20
adx_range = 5 # default 14
stoch_sell = 80 # default 80
stoch_buy = 20 # default 20
stoch_range = 14 # default 14
bollinger_buy_gap = 1.08 # default 1.08
bollinger_sell_gap = 1.08 # default 1.08
bb_range = 20 # default 20
atr_range = 3 # default 14
sma_range = 200 # default 50
change_consec = 1.005 # default 1.005
change_diff = 1.005 # default 1.001
consec_factor = 1
diff_factor = 1
optimize_params = True # default True
optimization_depth = 100 # default 100
