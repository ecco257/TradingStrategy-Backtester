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