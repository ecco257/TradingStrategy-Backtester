import config
import finnhub as fh
import pandas as pd
import date_range as dr
import sim_config as sc
import streamlit as st
from plotly import graph_objs as go

st.title('Strategy 2')

# initialize the Finnhub API client
finnhub_client = fh.Client(api_key=config.API_KEY)

def get_price_data(ticker, interval):
    # load price data
    price_data = finnhub_client.stock_candles(ticker, interval, dr.from_date_unix, dr.to_date_unix)
    return price_data

def add_stochastic_data(price_data):
    k = []
    d = []
    for i in range(0, len(price_data['t'])):
        if i < 14:
            k.append(0)
            d.append(0)
        else:
            k.append((price_data['c'][i] - min(price_data['l'][i-14:i]))/(max(price_data['h'][i-14:i]) - min(price_data['l'][i-14:i]))*100)
            d.append(sum(k[i-3:i])/3)
    price_data['slowk'] = k
    price_data['slowd'] = d
    return price_data

def add_fast_moving_average_data(price_data):
    ma = []
    for i in range(0, len(price_data['t'])):
        if i < 2:
            ma.append(0)
        else:
            ma.append(sum(price_data['c'][i-2:i])/2)
    price_data['fma'] = ma
    return price_data

def add_slow_moving_average_data(price_data):
    ma = []
    for i in range(0, len(price_data['t'])):
        if i < 3:
            ma.append(0)
        else:
            ma.append(sum(price_data['c'][i-3:i])/3)
    price_data['sma'] = ma
    return price_data

# this is the 14 period simple moving average of 1-period emv (ease of movement) where 1-period emv is the high plus the low
# divided by 2 minus the previous high plus the previous low divided by 2 all divided by the current volume divided by the
# average daily volume divided by high minus low
def add_ease_of_movement_data(price_data):
    emv = []
    for i in range(0, len(price_data['t'])):
        if i < 14:
            emv.append(0)
        else:
            emv.append(((price_data['h'][i] + price_data['l'][i])/2 - (price_data['h'][i-1] + price_data['l'][i-1])/2)/(price_data['v'][i]/(sum(price_data['v'][i-14:i])/14)/(price_data['h'][i] - price_data['l'][i])))
    price_data['emv'] = emv
    return price_data
    
def add_emv_moving_average_data(price_data):
    ma = []
    for i in range(0, len(price_data['t'])):
        if i < 20:
            ma.append(0)
        else:
            ma.append(sum(price_data['emv'][i-20:i])/20)
    price_data['ema'] = ma
    return price_data

def add_volume_data(price_data):
    # add the simple moving average of the volume data to the price data
    ma = []
    for i in range(0, len(price_data['t'])):
        if i < 14:
            ma.append(0)
        else:
            ma.append(sum(price_data['v'][i-14:i])/14)
    price_data['sma_v'] = ma
    return price_data

def add_macd_data(price_data):
    ema12 = []
    ema26 = []
    for i in range(0, len(price_data['t'])):
        if i < 26:
            ema12.append(0)
            ema26.append(0)
        else:
            ema12.append(sum(price_data['c'][i-12:i])/12)
            ema26.append(sum(price_data['c'][i-26:i])/26)
    price_data['ema12'] = ema12
    price_data['ema26'] = ema26
    price_data['macd'] = [ema12[i] - ema26[i] for i in range(0, len(price_data['t']))]
    macavg = []
    for i in range(0, len(price_data['macd'])):
        if i < 1:
            macavg.append(0)
        else:
            macavg.append(sum(price_data['macd'][i-1:i])/2)
    price_data['macavg'] = macavg
    return price_data

def add_all_indicators(price_data):
    price_data = add_stochastic_data(price_data)
    price_data = add_fast_moving_average_data(price_data)
    price_data = add_slow_moving_average_data(price_data)
    #price_data = add_ease_of_movement_data(price_data)
    #price_data = add_emv_moving_average_data(price_data)
    #price_data = add_volume_data(price_data)
    price_data = add_macd_data(price_data)
    return price_data

def get_buy_and_sell_points_stoch(price_data, buy_thres, sell_thres):
    # initialize the data frame that will be used to store the time stamps to buy or sell the ticker and whether it is a 
    # buy or sell
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])
    # initially everything is a hold
    for i in range(0, len(price_data['t'])):
        df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'hold']
    for i in range(3, len(price_data['t'])):

        if price_data['macd'][i] < -5 and price_data['macavg'][i] - price_data['macd'][i] > 4:      
            df.loc[i, 'buy/sell/hold'] = 'buy'

        elif price_data['macd'][i] > 5 and price_data['macd'][i] - price_data['macavg'][i] > 4:
            df.loc[i, 'buy/sell/hold'] = 'sell'

    return df

def get_buy_and_sell_points_ma(price_data):
    # initialize the data frame that will be used to store the time stamps to buy or sell the ticker and whether it is a 
    # buy or sell
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])
    # go through the moving average data and find the buy and sell points
    for i in range(1, len(price_data['t'])):
        
        if price_data['fma'][i] > price_data['sma'][i] and price_data['fma'][i-1] < price_data['sma'][i-1]:
            df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]),price_data['c'][i], 'buy']

        elif price_data['fma'][i] < price_data['sma'][i] and price_data['fma'][i-1] > price_data['sma'][i-1]:
            df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]),price_data['c'][i], 'sell']
        
        else:
            df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]),price_data['c'][i], 'hold']

    return df

# get the optimal buy and sell points based on the stochastic oscillator, and moving average combination
def get_optimal_buy_and_sell_points(price_data, buy_thres, sell_thres):
    # initialize the data frame that will be used to store the time stamps to buy or sell the ticker and whether it is a 
    # buy or sell
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])
    # initialize everything to hold
    for i in range(0, len(price_data['t'])):
        df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]),price_data['c'][i], 'hold']
    # go through the stochastic and moving average data and find the buy and sell points
    for i in range(1, len(df['time'])):
        if price_data['fma'][i] > price_data['sma'][i] and price_data['fma'][i-1] < price_data['sma'][i-1]:
            j = i
            while j > 0 and (price_data['slowk'][j] > buy_thres or price_data['slowk'][j] < price_data['slowd'][j] or \
                price_data['slowk'][j-1] > price_data['slowd'][j-1]):
                j -= 1  
            if j != 0:
                df.loc[j, 'buy/sell/hold'] = 'buy'
        elif price_data['fma'][i] < price_data['sma'][i] and price_data['fma'][i-1] > price_data['sma'][i-1]:
            j = i
            while j > 0 and (price_data['slowk'][j] < sell_thres or price_data['slowk'][j] > price_data['slowd'][j] or \
                price_data['slowk'][j-1] < price_data['slowd'][j-1]):
                j -= 1  
            if j != 0:
                df.loc[j, 'buy/sell/hold'] = 'sell'
    return df

# simulate the profitability if buying and selling over the time period
def simulate_buying_and_selling(df):
    # initialize the money and the number of stocks
    money = sc.starting_money
    num_stocks = 0

    # go through the data frame and simulate buying and selling
    for i in range(0, len(df)):
        # if the buy/sell/hold is buy, spend a certain amount of money on stock
        if df['buy/sell/hold'][i] == 'buy' and money > 500:
            num_stocks += 500*(1-sc.transaction_fee)/df['price'][i]
            money -= 500
        # if the buy/sell/hold is sell, sell a certain amount of shares
        elif df['buy/sell/hold'][i] == 'sell' and num_stocks*df['price'][i] > 500:
            money += 500*(1-sc.transaction_fee)
            num_stocks -= 500/df['price'][i]

    # backtrack to last buy or sell
    if num_stocks > 0:
        i = len(df)-1
        while(df['buy/sell/hold'][i] == 'hold'):
            i -= 1
        if df['buy/sell/hold'][i] == 'buy' or df['buy/sell/hold'][i] == 'sell':
            money += num_stocks*df['price'][i]
            num_stocks = 0
    return money
        
indicator_data = add_all_indicators(get_price_data(sc.ticker, sc.interval))

df1 = get_buy_and_sell_points_stoch(indicator_data, sc.buy_threshold, sc.sell_threshold)
#df2 = get_buy_and_sell_points_ma(indicator_data)
#df3 = get_optimal_buy_and_sell_points(indicator_data, sc.buy_threshold, sc.sell_threshold)

# plot the prices over time, highlighting the buy and sell points on streamlit
def plot_buy_and_sell_points(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['time'], y=df['price'], mode='lines', name='price'))
    fig.add_trace(go.Scatter(x=df[df['buy/sell/hold'] == 'buy']['time'], y=df[df['buy/sell/hold'] == 'buy']['price'], mode='markers', name='buy', marker_color='green'))
    fig.add_trace(go.Scatter(x=df[df['buy/sell/hold'] == 'sell']['time'], y=df[df['buy/sell/hold'] == 'sell']['price'], mode='markers', name='sell', marker_color='red'))
    fig.update_layout(title='Results', xaxis_title='Date', yaxis_title='Price')
    st.plotly_chart(fig)

# plot the slowk and slowd over time on streamlit
def plot_stochastic_data(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['slowk'], mode='lines', name='slowk'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['slowd'], mode='lines', name='slowd'))
    fig.update_layout(title='Stochastic Data', xaxis_title='Date', yaxis_title='%k and %d')
    st.plotly_chart(fig)

# plot the moving average over time on streamlit
def plot_moving_average(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['fma'], mode='lines', name='fast moving average'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['sma'], mode='lines', name='slow moving average'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['c'], mode='lines', name='price'))
    fig.update_layout(title='Moving Average', xaxis_title='Date', yaxis_title='Price')
    st.plotly_chart(fig)

# plot emv and ema over time on streamlit
def plot_emv(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['emv'], mode='lines', name='emv'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['ema'], mode='lines', name='ema'))
    fig.update_layout(title='EMV', xaxis_title='Date', yaxis_title='EMV and EMA')
    st.plotly_chart(fig)

# plot the volume over time on streamlit and the simple moving average of the volume
def plot_volume(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['v'], mode='lines', name='volume'))
    fig.update_layout(title='Volume', xaxis_title='Date', yaxis_title='Volume')
    st.plotly_chart(fig)

# plot the macd over time on streamlit
def plot_macd(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['macd'], mode='lines', name='macd'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['macavg'], mode='lines', name='macd sma'))
    fig.update_layout(title='MACD', xaxis_title='Date', yaxis_title='MACD')
    st.plotly_chart(fig)

st.header('Buy and Sell Points for Stochastic')
plot_buy_and_sell_points(df1)
st.header('strategy parameters')
st.write('Parameters: ', 'buy threshold: ', sc.buy_threshold, 'sell threshold: ', sc.sell_threshold)
st.header('Profitability')
st.write('Optimal profitability: ', simulate_buying_and_selling(df1)/sc.starting_money*100 - 100, '%')
plot_stochastic_data(indicator_data)
plot_moving_average(indicator_data)
plot_volume(indicator_data)
plot_macd(indicator_data)