API_KEY = 'cddjbiaad3iag7bhr1pgcddjbiaad3iag7bhr1q0' # This is the API key for the Finnhub API
delta_time = 365*5
all_tickers = False # if True, all tickers in the ticker file will be analyzed - WARNING: this will take a long time 
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
