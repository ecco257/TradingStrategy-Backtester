import config
from datetime import datetime as dt
import time
import finnhub as fh
import pandas as pd
import json
import api_rate_limit_handling as api
import os
import date_range as dr
import stochastic_config as sc
import streamlit as st
from plotly import graph_objs as go

'''
this strategy uses the stochastic oscillator to decide when to buy and sell stocks
'''

st.title('Stochastic Oscillator Strategy')

# initialize the data frame that will be used to store the time stamps to buy or sell the ticker and whether it is a 
# buy or sell
df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])

# initialize the Finnhub API client
finnhub_client = fh.Client(api_key=config.API_KEY)

def get_stochastic_data(ticker, interval):
    # load stochastic data
    stochastic_data = finnhub_client.technical_indicator(ticker, interval, dr.from_date_unix, dr.to_date_unix, 'stoch')

    # return the stochastic data
    return stochastic_data

def write_stochastic_data(ticker, interval):
    stochastic_data = finnhub_client.technical_indicator(ticker, interval, dr.from_date_unix, dr.to_date_unix, 'stoch')

    with open('stochastic.json', 'w') as f:
        json.dump(stochastic_data, f, indent=4)


def get_buy_and_sell_points(stochastic_data, buy_thres, sell_thres, pct_change):
    # initialize the data frame that will be used to store the time stamps to buy or sell the ticker and whether it is a 
    # buy or sell
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])

    # go through the stochastic data and find the buy and sell points
    for i in range(10, len(stochastic_data['t'])):
        print(str(int((float(i))/len(stochastic_data['t'])*100)) + '%', end='\r') 

        if stochastic_data['slowk'][i] < buy_thres and stochastic_data['c'][i-10]/stochastic_data['c'][i] > \
            pct_change and stochastic_data['slowk'][i] > stochastic_data['slowd'][i] and \
            stochastic_data['slowk'][i-1] < stochastic_data['slowd'][i-1]:
            df.loc[len(df)] = [dr.unix_to_date(stochastic_data['t'][i]),stochastic_data['c'][i], 'buy']

        elif stochastic_data['slowk'][i] > sell_thres and stochastic_data['c'][i]/stochastic_data['c'][i-10] > \
            pct_change and stochastic_data['slowk'][i] < stochastic_data['slowd'][i] and \
            stochastic_data['slowk'][i-1] > stochastic_data['slowd'][i-1]:
            df.loc[len(df)] = [dr.unix_to_date(stochastic_data['t'][i]),stochastic_data['c'][i], 'sell']
        
        else:
            df.loc[len(df)] = [dr.unix_to_date(stochastic_data['t'][i]),stochastic_data['c'][i], 'hold']
    return df

# recursively test the get buy and sell points function for different values of the buy and sell thresholds and the percent change to buy or sell in order to find the best values
def optimize_parameters(sell_thres, buy_thres, pct_change, stoc_data, df, current_max, max_df):
    if sell_thres > sc.max_sell and buy_thres > sc.max_buy and pct_change > sc.pct_change_max:
        return max_df
    new_max = simulate_buying_and_selling(df)
    if new_max > current_max:
        optimize_parameters(sell_thres, buy_thres, pct_change, stoc_data, df, new_max, df)
    else:
        new_buy = buy_thres + 1
        new_sell = sell_thres + 1
        new_pct_change = pct_change + 0.01
        df_buy = get_buy_and_sell_points(stoc_data, new_buy, sell_thres, pct_change)
        df_sell = get_buy_and_sell_points(stoc_data, buy_thres, new_sell, pct_change)
        df_pct = get_buy_and_sell_points(stoc_data, buy_thres, sell_thres, new_pct_change)
        optimize_parameters(sell_thres, new_buy, pct_change, stoc_data, df_buy, current_max, max_df)
        optimize_parameters(new_sell, buy_thres, pct_change, stoc_data, df_sell, current_max, max_df)
        optimize_parameters(sell_thres, buy_thres, new_pct_change, stoc_data, df_pct, current_max, max_df)


    

def write_buy_and_sell_points(stochastic_data):
    # initialize the data frame that will be used to store the time stamps to buy or sell the ticker and whether it is a 
    # buy or sell
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])

    # go through the stochastic data and find the buy and sell points
    for i in range(1, len(stochastic_data['t'])):
        print(str(int((float(i+1))/len(stochastic_data['t'])*100)) + '%', end='\r')       
        # if the stochastic oscillator is below 20 and is rising, buy
        if stochastic_data['slowk'][i] < 20 and stochastic_data['slowk'][i] > stochastic_data['slowk'][i-1]:
            df.loc[len(df)] = [dr.unix_to_date(stochastic_data['t'][i]), 'buy']
        # if the stochastic oscillator is above 80 and is falling, sell
        elif stochastic_data['slowk'][i] > 80 and stochastic_data['slowk'][i] < stochastic_data['slowk'][i-1]:
            df.loc[len(df)] = [dr.unix_to_date(stochastic_data['t'][i]), 'sell']
        else:
            df.loc[len(df)] = [dr.unix_to_date(stochastic_data['t'][i]), 'hold']
    df.to_csv('buy_and_sell_points.csv')

# simulate the profitability if buying and selling over the time period
def simulate_buying_and_selling(df):
    # initialize the money and the number of stocks
    money = sc.starting_money
    num_stocks = 0

    # go through the data frame and simulate buying and selling
    for i in range(0, len(df)):
        # if the buy/sell/hold is buy, spend a certain amount of money on stock
        if df['buy/sell/hold'][i] == 'buy':
            num_stocks += money*(1-sc.transaction_fee)/df['price'][i]
            money = 0
        # if the buy/sell/hold is sell, sell a certain amount of shares
        elif df['buy/sell/hold'][i] == 'sell':
            money += num_stocks*df['price'][i]*(1-sc.transaction_fee)
            num_stocks = 0

    # backtrack to last buy or sell
    if num_stocks > 0:
        i = len(df)-1
        while(df['buy/sell/hold'][i] == 'hold'):
            i -= 1
        if df['buy/sell/hold'][i] == 'buy':
            money += num_stocks*df['price'][i]*(1-sc.transaction_fee)
            num_stocks = 0
    return money

# make all leading buys holds except for last one, and all leading sells holds except for last one
def prune_buy_and_selling_data(df):
    # go through the data frame and make all leading buys holds except for last one, and all leading sells holds except for last one
    last_buy_or_sell = -1
    for i in range(0, len(df)):
        if df['buy/sell/hold'][i] == 'buy':
            while i < len(df) and df['buy/sell/hold'][i] != 'sell':
                if df['buy/sell/hold'][i] == 'buy':
                    last_buy_or_sell = i
                df['buy/sell/hold'][i] = 'hold'
                i += 1
            df['buy/sell/hold'][last_buy_or_sell] = 'buy'
        elif df['buy/sell/hold'][i] == 'sell':
            while i < len(df) and df['buy/sell/hold'][i] != 'buy':
                if df['buy/sell/hold'][i] == 'sell':
                    last_buy_or_sell = i
                df['buy/sell/hold'][i] = 'hold'
                i += 1
            df['buy/sell/hold'][last_buy_or_sell] = 'sell'
    return df

df = get_buy_and_sell_points(get_stochastic_data(sc.ticker, sc.interval), sc.buy_threshold, sc.sell_threshold, sc.percent_change)

df = optimize_parameters(sc.min_sell, sc.min_buy, sc.pct_change_min, get_stochastic_data(sc.ticker, sc.interval), df, simulate_buying_and_selling(df), df)

# plot the prices over time, highlighting the buy and sell points on streamlit
def plot_buy_and_sell_points(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['time'], y=df['price'], mode='lines', name='price'))
    fig.add_trace(go.Scatter(x=df[df['buy/sell/hold'] == 'buy']['time'], y=df[df['buy/sell/hold'] == 'buy']['price'], mode='markers', name='buy', marker_color='green'))
    fig.add_trace(go.Scatter(x=df[df['buy/sell/hold'] == 'sell']['time'], y=df[df['buy/sell/hold'] == 'sell']['price'], mode='markers', name='sell', marker_color='red'))
    fig.update_layout(title='Stochastic Data', xaxis_title='Date', yaxis_title='Price')
    st.plotly_chart(fig)

# plot the slowk and slowd over time on streamlit
def plot_stochastic_data(stochastic_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in stochastic_data['t']], y=stochastic_data['slowk'], mode='lines', name='slowk'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in stochastic_data['t']], y=stochastic_data['slowd'], mode='lines', name='slowd'))
    fig.update_layout(title='Stochastic Data', xaxis_title='Date', yaxis_title='%k and %d')
    st.plotly_chart(fig)
plot_buy_and_sell_points(df)
st.header('Profitability')
st.write('If you bought and sold the stock based on the stochastic data, you would have made ' + str(simulate_buying_and_selling(df)/10000*100 - 100) + '% profit.')
plot_stochastic_data(get_stochastic_data(sc.ticker, sc.interval))