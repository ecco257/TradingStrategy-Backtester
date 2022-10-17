import config
from datetime import datetime as dt
import time
import finnhub as fh
import pandas as pd
import json
import api_rate_limit_handling as api
import os
import date_range as dr


# initialize the data frame that will be used to store the scores for each ticker
df = pd.DataFrame(columns=['ticker', 'trend score', 'sentiment score', 'average score'])

# initialize the Finnhub API client
finnhub_client = fh.Client(api_key=config.API_KEY)

def get_sentiment_score(ticker):
    # load sentiment data
    sentiment = finnhub_client.stock_social_sentiment(ticker, dr.from_date, dr.to_date)

    # calculate sentiment score for reddit over the past n months, specified in config.py
    reddit_score = 0
    for i in range(len(sentiment['reddit'])):
        reddit_score += sentiment['reddit'][i]['positiveMention'] - sentiment['reddit'][i]['negativeMention']
    if(len(sentiment['reddit']) != 0):
        reddit_score /= len(sentiment['reddit'])
    else:
        reddit_score = 0

    # calculate sentiment score for twitter over the past n months, specified in config.py
    twitter_score = 0
    for i in range(len(sentiment['twitter'])):
        twitter_score += sentiment['twitter'][i]['positiveMention'] - sentiment['twitter'][i]['negativeMention']
    if len(sentiment['twitter']) != 0:
        twitter_score /= len(sentiment['twitter'])
    else:
        twitter_score = 0

    # calculate the total sentiment score based on reddit and twitter
    total_sentiment_score = reddit_score + twitter_score
    return total_sentiment_score

def write_sentiment_data(ticker):
    sentiment = finnhub_client.stock_social_sentiment(ticker, dr.from_date, dr.to_date)

    with open('sentiment.json', 'w') as f:
        json.dump(sentiment, f, indent=4)

def get_trend_score(ticker):
    # load trend data
    trend = finnhub_client.recommendation_trends(ticker)

    # calculate trend score
    total_trend_score = 0
    for i in range(len(trend)):
        total_trend_score += trend[i]['strongBuy']*1.5 + trend[i]['buy']*1 + trend[i]['sell']*-1 + \
            trend[i]['strongSell']*-1.5
    if(len(trend) != 0):
        total_trend_score /= len(trend)
    else:
        return 0
    return total_trend_score

def write_trend_data(ticker):
    trend = finnhub_client.recommendation_trends(ticker)

    with open('trend.json', 'w') as f:
        json.dump(trend, f, indent=4)

def save_all_scores():
    if(config.all_tickers):
        # load all tickers from tickers.txt
        with open('tickers.txt', 'r') as f:
            ticker_list = f.readlines()
        # save all scores to the data frame
        for i in range(len(ticker_list)):
            # print progress
            seconds_remaining = (len(ticker_list)-i)*api.RATE_LIMIT/api.CALLS*2
            minutes_and_seconds_remaining = str(int(seconds_remaining/60)) + ' minutes and ' + \
                str(int(seconds_remaining%60)) + ' seconds'
            print('Analyzing tickers: ' + str(i+1) + '/' + str(len(ticker_list)) + ' Estimated time remaining: ' + \
                minutes_and_seconds_remaining, end='\r')

            # add the sentiment score and trend score to the data frame
            api.check_limit()
            trend_score = get_trend_score(ticker_list[i])
            api.check_limit()
            sentiment_score = get_sentiment_score(ticker_list[i])
            df.loc[i] = [ticker_list[i], trend_score, sentiment_score, None]
    else:
        # save all scores to the data frame
        for i in range(len(config.ticker_list)):
            # print progress
            seconds_remaining = (len(config.ticker_list)-i)*api.RATE_LIMIT/api.CALLS*2
            minutes_and_seconds_remaining = str(int(seconds_remaining/60)) + ' minutes and ' + \
                str(int(seconds_remaining%60)) + ' seconds'
            print('Analyzing tickers: ' + str(i+1) + '/' + str(len(config.ticker_list)) + ' Estimated time remaining: '\
                + minutes_and_seconds_remaining, end='\r')

            # add the sentiment score and trend score to the data frame
            api.check_limit()
            trend_score = get_trend_score(config.ticker_list[i])
            api.check_limit()
            sentiment_score = get_sentiment_score(config.ticker_list[i])
            df.loc[i] = [config.ticker_list[i], trend_score, sentiment_score, None]

    os.system('cls' if os.name == 'nt' else 'clear')

def write_scores_to_csv():
    df.to_csv('scores.csv', index=False)

def sort_top_scores():
    # add the average score to the data frame and sort the data frame by the average score
    df['average score'] = df[['trend score', 'sentiment score']].mean(axis=1)
    df.sort_values(by=['average score'], inplace=True, ascending=False)

save_all_scores()
sort_top_scores()
write_scores_to_csv()