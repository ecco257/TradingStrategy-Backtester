import config
from datetime import datetime as dt
import time


# initialize the to and from dates based on the delta_time specified in config.py
to_date_unix = int(time.time() - 60*60*24*config.to_date_less)

from_date_unix = to_date_unix - int(config.delta_time * 24 * 60 * 60)

def unix_to_date(unix):
    return dt.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S')

def date_to_unix(date):
    return int(time.mktime(dt.strptime(date, '%Y-%m-%d %H:%M:%S').timetuple()))

'''
if price_data['c'][i] > price_data['sma'][i] and price_data['c'][i-1] < price_data['sma'][i-1] and prev_short_open_price != 0 and prev_short_open_price/price_data['c'][i] > 1.07 and not prev_big_short_close:
    df.loc[i, 'buy/sell/hold'] = 'big_short_close'
    prev_big_short_close = True
    prev_big_sell = False
elif price_data['c'][i] < price_data['sma'][i] and price_data['c'][i-1] > price_data['sma'][i-1] and prev_buy_price != 0 and price_data['c'][i]/prev_buy_price > 1.07 and not prev_big_sell:
    df.loc[i, 'buy/sell/hold'] = 'big_sell'
    prev_big_short_close = False
    prev_big_sell = True
'''