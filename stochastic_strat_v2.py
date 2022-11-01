import config
import finnhub as fh
import pandas as pd
import date_range as dr
import sim_config as sc
import streamlit as st
from plotly import graph_objs as go
import optuna

st.title('Stochastic Oscillator Strategy 2')

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

def get_buy_and_sell_points(price_data, buy_thres, sell_thres, buy_skips, sell_skips):
    # initialize the data frame that will be used to store the time stamps to buy or sell the ticker and whether it is a 
    # buy or sell
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])
    n_buy = 0
    n_sell = 0
    # go through the stochastic data and find the buy and sell points
    for i in range(1, len(price_data['t'])):
        
        if price_data['slowk'][i] < buy_thres and price_data['slowk'][i] > price_data['slowd'][i] and \
            price_data['slowk'][i-1] < price_data['slowd'][i-1]:
            n_sell = 0
            n_buy += 1
            if n_buy >= buy_skips:
                df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]),price_data['c'][i], 'buy']
                n_buy = 0
            else:
                df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]),price_data['c'][i], 'hold']

        elif price_data['slowk'][i] > sell_thres and price_data['slowk'][i] < price_data['slowd'][i] and \
            price_data['slowk'][i-1] > price_data['slowd'][i-1]:
            n_buy = 0
            n_sell += 1
            if n_sell >= sell_skips:
                df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]),price_data['c'][i], 'sell']
                n_sell = 0
            else:
                df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]),price_data['c'][i], 'hold']
        
        else:
            df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]),price_data['c'][i], 'hold']
    return df

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
            money += num_stocks*df['price'][i]
            num_stocks = 0
    return money

def objective(trial, stoc_data):
    # get the parameters
    buy_thres = trial.suggest_float('buy_thres', 5, 40)
    sell_thres = trial.suggest_float('sell_thres', 60, 95)
    buy_skips = trial.suggest_int('buy_skips', 1, 6)
    sell_skips = trial.suggest_int('sell_skips', 1, 6)
    # get the buy and sell points
    df = get_buy_and_sell_points(stoc_data, buy_thres, sell_thres, buy_skips, sell_skips)
    # simulate buying and selling
    return 1/simulate_buying_and_selling(df)

def optimize_parameters(stoc_data):
    # optimize the parameters for maximizing the profit
    study = optuna.create_study()
    study.optimize(lambda trial: objective(trial, stoc_data), n_trials=sc.optimization_depth, show_progress_bar=True)
    return study.best_params
        
stoc_data = add_stochastic_data(get_price_data(sc.ticker, sc.interval))

if sc.optimize_params:
    params = optimize_parameters(stoc_data)
    df = get_buy_and_sell_points(stoc_data, params['buy_thres'], params['sell_thres'], params['buy_skips'], params['sell_skips'])
else:
    df = get_buy_and_sell_points(stoc_data, sc.buy_threshold, sc.sell_threshold, sc.buy_skips, sc.sell_skips)

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
st.header('Stochastic Parameters')
if sc.optimize_params:
    st.write('Optimized Parameters: ', params)
else:
    st.write('Parameters: ', 'buy threshold: ', sc.buy_threshold, 'sell threshold: ', sc.sell_threshold, 'buy skips: ', sc.buy_skips, 'sell skips: ', sc.sell_skips)
st.header('Profitability')
st.write('If you bought and sold the stock based on the stochastic data, you would have made ' + str(simulate_buying_and_selling(df)/10000*100 - 100) + '% profit.')
plot_stochastic_data(stoc_data)
