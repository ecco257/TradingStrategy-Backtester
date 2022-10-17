from ratelimit import limits, sleep_and_retry

CALLS = 60
RATE_LIMIT = 61

@sleep_and_retry
@limits(calls=CALLS, period=RATE_LIMIT)
def check_limit():
    ''' Empty function just to check for calls to API '''
    return