API_KEY = 'c5bmrg2ad3ifmvj0ngb0' # This is the API key for the Finnhub API
delta_time = 365*3
all_tickers = False # if True, all tickers in the tickers.txt will be analyzed - WARNING: this will take a long time 
# because of the API rate limit
if not all_tickers:
    ticker_list = [# list of tickers to analyze if all_tickers is False
        'AAPL', 
        'MSFT', 
        'NVDA', 
        'GOOG', 
        'META', 
        'AMD',
        'TSLA',
        'RBLX',
        'AMZN',
        'NFLX',
        'BABA',
        'BIDU'
        ] 
else:
    ticker_list = []