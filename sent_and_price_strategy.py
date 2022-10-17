import config
from datetime import datetime as dt
import time
import finnhub as fh
import pandas as pd
import json


to_date = int(time.time())
print(to_date)

from_date = 0
if int(config.delta_time) >= dt.now().month:
    from_date = dt.now().replace(year=dt.now().year-1, month=dt.now().month+12-int(config.delta_time)).strftime('%Y-%m-\
%d')
else:
    from_date = dt.now().replace(month=dt.now().month-int(config.delta_time)).strftime('%Y-%m-%d')

from_date = int(time.mktime(dt(int(from_date.split('-')[0]), int(from_date.split('-')[1]), 
    int(from_date.split('-')[2])).timetuple()))

print(from_date)

df = pd.DataFrame(columns=['ticker', 'trend score', 'sentiment score', 'price score', 'time'])

finnhub_client = fh.Client(api_key=config.API_KEY)

def get_sentiment_score(ticker):
    print('------------------------------------')
    print(f'Getting sentiment score for {ticker}')

    print('Loading sentiment data...')
    sentiment = finnhub_client.stock_social_sentiment(ticker, from_date, to_date)

    print('Calculating sentiment score for reddit...')
    reddit_score = 0
    for i in range(len(sentiment['reddit'])):
        reddit_score += sentiment['reddit'][i]['positiveMentions'] - sentiment['reddit'][i]['negativeMentions']
    if(len(sentiment['reddit']) != 0):
        reddit_score /= len(sentiment['reddit'])
    else:
        reddit_score = 0
    print('Calculating sentiment score for twitter...')
    twitter_score = 0
    for i in range(len(sentiment['twitter'])):
        twitter_score += sentiment['twitter'][i]['positiveMentions'] - sentiment['twitter'][i]['negativeMentions']
    if len(sentiment['twitter']) != 0:
        twitter_score /= len(sentiment['twitter'])
    else:
        twitter_score = 0

    print('Calculating total sentiment score...')
    total_sentiment_score = reddit_score + twitter_score
    return total_sentiment_score

def write_sentiment_data(ticker):
    sentiment = finnhub_client.stock_social_sentiment(ticker, from_date, to_date)

    with open('sentiment.json', 'w') as f:
        json.dump(sentiment, f, indent=4)

def get_trend_score(ticker):
    print('------------------------------------')
    print(f'Getting trend score for {ticker}')

    print('Loading trend data...')
    trend = finnhub_client.recommendation_trends(ticker)

    print('Saving trend data to trend.json...')
    with open('trend.json', 'w') as f:
        json.dump(trend, f, indent=4)

    print('Calculating trend score...')
    total_trend_score = 0
    for i in range(len(trend)):
        total_trend_score += trend[i]['strongBuy']*1.5 + trend[i]['buy']*1 + trend[i]['hold']*0.5 + trend[i]['sell']*-1\
        + trend[i]['strongSell']*-1.5
    if(len(trend) != 0):
        total_trend_score /= len(trend)
    else:
        return 0
    return total_trend_score

def write_trend_data(ticker):
    trend = finnhub_client.recommendation_trends(ticker)

    with open('trend.json', 'w') as f:
        json.dump(trend, f, indent=4)

def get_stochastic_score(ticker):
    print('------------------------------------')
    print(f'Getting stochastic score for {ticker}')

    print('Loading stochastic data...')
    print(from_date)
    stochastic = finnhub_client.technical_indicator(ticker, 'D', from_date, to_date, 'stoch')
    print(json.dumps(stochastic, indent=4))
    with open('stochastic.json', 'w') as f:
        json.dump(stochastic, f, indent=4)

get_stochastic_score('AAPL')