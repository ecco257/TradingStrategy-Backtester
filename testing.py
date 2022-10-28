import finnhub as fh
import config
import date_range as dr

# initialize the Finnhub API client
finnhub_client = fh.Client(api_key=config.API_KEY)

# load price data
price_data = finnhub_client.stock_candles('AAPL', 'D', dr.from_date_unix, dr.to_date_unix)

print(price_data)
