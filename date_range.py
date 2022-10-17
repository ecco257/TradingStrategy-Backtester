import config
from datetime import datetime as dt
import time


# initialize the to and from dates based on the delta_time specified in config.py
to_date_unix = int(time.time())
to_date = dt.fromtimestamp(to_date_unix).strftime('%Y-%m-%d %H:%M:%S')

from_date = 0
if int(config.delta_time) >= dt.now().month:
    from_date = dt.now().replace(year=dt.now().year-1, month=dt.now().month+12-int(config.delta_time)).strftime('%Y-%m-\
%d')
else:
    from_date = dt.now().replace(month=dt.now().month-int(config.delta_time)).strftime('%Y-%m-%d')
from_date_unix = int(time.mktime(dt(int(from_date.split('-')[0]), int(from_date.split('-')[1]), 
    int(from_date.split('-')[2])).timetuple()))