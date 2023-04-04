import Configuration.Config as cfg
from datetime import datetime as dt
import time


# initialize the to and from dates based on the delta_time specified in config.py
TO_DATE_UNIX = int((time.time() - 60*60*24*cfg.TO_DATE_LESS)//60 * 60)

FROM_DATE_UNIX = TO_DATE_UNIX - int(cfg.DELTA_TIME * 24 * 60 * 60)

TO_DATE_MS = TO_DATE_UNIX * 1000

FROM_DATE_MS = TO_DATE_MS - int(cfg.DELTA_TIME * 24 * 60 * 60 * 1000)

def unix_to_date(unix):
    return dt.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S')

def unix_to_date_time(unix):
    return dt.fromtimestamp(unix)

def date_to_unix(date):
    if type(date) == str:
        return int(time.mktime(dt.strptime(date, '%Y-%m-%d %H:%M:%S').timetuple()))
    else:
        return int(time.mktime(date.timetuple()))

def date_to_unix_ms(date):
    return date_to_unix(date) * 1000

def unix_ms_to_date(unix):
    return dt.fromtimestamp(unix/1000).strftime('%Y-%m-%d %H:%M:%S')

def unix_ms_to_date_time(unix):
    return dt.fromtimestamp(unix/1000)