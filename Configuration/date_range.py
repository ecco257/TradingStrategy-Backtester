import Configuration.config as cfg
from datetime import datetime as dt
import time


# initialize the to and from dates based on the delta_time specified in config.py
TO_DATE_UNIX = int(time.time() - 60*60*24*cfg.TO_DATE_LESS)

FROM_DATE_UNIX = TO_DATE_UNIX - int(cfg.DELTA_TIME * 24 * 60 * 60)

def unix_to_date(unix):
    return dt.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S')

def unix_to_date_time(unix):
    return dt.fromtimestamp(unix)

def date_to_unix(date):
    return int(time.mktime(dt.strptime(date, '%Y-%m-%d %H:%M:%S').timetuple()))
