import config
import finnhub as fh
import pandas as pd
import date_range as dr
import sim_config as sc
import streamlit as st
from plotly import graph_objs as go
import optuna

st.title('Strategy 2?')

# initialize the Finnhub API client
finnhub_client = fh.Client(api_key=config.API_KEY)

sentiment = finnhub_client.stock_social_sentiment(sc.ticker, dr.from_date_unix, dr.to_date_unix)

for i in range(len(sentiment['twitter'])):
    sentiment['twitter'][i]['atTime'] = pd.to_datetime(sentiment['twitter'][i]['atTime'])
st.write(sentiment)

def plot_sentiment(sentiment):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[sentiment['twitter'][i]['atTime'] for i in range(len(sentiment['twitter']))], y=[sentiment['twitter'][j]['positiveMention'] for j in range(len(sentiment['twitter']))], name='positiveMention'))
    fig.add_trace(go.Scatter(x=[sentiment['twitter'][i]['atTime'] for i in range(len(sentiment['twitter']))], y=[sentiment['twitter'][j]['negativeMention'] for j in range(len(sentiment['twitter']))], name='negativeMention'))
    st.plotly_chart(fig)

# plot the sentiment
plot_sentiment(sentiment)

def get_price_data(ticker, interval):
    # load price data
    price_data = finnhub_client.stock_candles(ticker, interval, dr.from_date_unix, dr.to_date_unix)
    return price_data

def get_crypto_price_data(crypto, interval):
    # load price data
    price_data = finnhub_client.crypto_candles(crypto, interval, dr.from_date_unix, dr.to_date_unix)
    return price_data

def add_stochastic_data(price_data, stoch_range):
    k = []
    d = []
    for i in range(0, len(price_data['t'])):
        if i < stoch_range:
            k.append(0)
            d.append(0)
        else:
            maximum = max(price_data['h'][i-stoch_range:i])
            minimum = min(price_data['l'][i-stoch_range:i])
            if maximum - minimum == 0:
                k.append(0)
                d.append(0)
            else:
                k.append((price_data['c'][i] - minimum)/(maximum - minimum)*100)
                d.append(sum(k[i-3:i])/3)
    price_data['slowk'] = k
    price_data['slowd'] = d
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
    price_data['macd'] = [(ema12[i] - ema26[i])/price_data['c'][i] for i in range(0, len(price_data['t']))]
    macavg = []
    for i in range(0, len(price_data['macd'])):
        if i < 2:
            macavg.append(0)
        else:
            macavg.append(sum(price_data['macd'][i-2:i])/2)
    price_data['macavg'] = macavg
    return price_data

def add_bollinger_bands_data(price_data, bb_range):
    # add the simple moving average of the price data to the price data
    ma = []
    for i in range(0, len(price_data['t'])):
        if i < bb_range:
            ma.append(0)
        else:
            ma.append(sum(price_data['c'][i-bb_range:i])/bb_range)
    price_data['bsma'] = ma
    # add the standard deviation of the price data to the price data
    std = []
    for i in range(0, len(price_data['t'])):
        if i < bb_range:
            std.append(0)
        else:
            std.append(pd.Series(price_data['c'][i-bb_range:i]).std())
    price_data['std'] = std
    # add the upper bollinger band to the price data
    price_data['upper_bb'] = [price_data['bsma'][i] + 2*price_data['std'][i] for i in range(0, len(price_data['t']))]
    # add the lower bollinger band to the price data
    price_data['lower_bb'] = [price_data['bsma'][i] - 2*price_data['std'][i] for i in range(0, len(price_data['t']))]
    return price_data

# add the average directional movement index to the price data
def add_adx_data(price_data, adx_range):
    tr = []
    tr_pos = []
    tr_neg = []
    for i in range(0, len(price_data['t'])):
        if i < 1:
            tr.append(0)
            tr_pos.append(0)
            tr_neg.append(0)
        else:
            tr.append(max(price_data['h'][i] - price_data['l'][i], abs(price_data['h'][i] - price_data['c'][i-1]), abs(price_data['l'][i] - price_data['c'][i-1])))
            tr_pos.append(max(price_data['h'][i] - price_data['c'][i-1], 0))
            tr_neg.append(max(price_data['c'][i-1] - price_data['l'][i], 0))
    price_data['tr'] = tr
    price_data['tr_pos'] = tr_pos
    price_data['tr_neg'] = tr_neg
    tr_avg = []
    tr_pos_avg = []
    tr_neg_avg = []
    for i in range(0, len(price_data['t'])):
        if i < adx_range:
            tr_avg.append(0)
            tr_pos_avg.append(0)
            tr_neg_avg.append(0)
        else:
            tr_avg.append(sum(price_data['tr'][i-adx_range:i])/adx_range)
            tr_pos_avg.append(sum(price_data['tr_pos'][i-adx_range:i])/adx_range)
            tr_neg_avg.append(sum(price_data['tr_neg'][i-adx_range:i])/adx_range)
    price_data['tr_avg'] = tr_avg
    price_data['tr_pos_avg'] = tr_pos_avg
    price_data['tr_neg_avg'] = tr_neg_avg
    price_data['dx'] = [100*abs(price_data['tr_pos_avg'][i] - price_data['tr_neg_avg'][i])/(price_data['tr_pos_avg'][i] + price_data['tr_neg_avg'][i]) for i in range(adx_range, len(price_data['t']))]
    adx = []
    for i in range(0, len(price_data['t'])):
        if i < adx_range:
            adx.append(0)
        else:
            adx.append(sum(price_data['dx'][i-adx_range:i])/adx_range)
    price_data['adx'] = adx
    price_data['adx_avg'] = [sum(price_data['adx'][i-3:i])/3 for i in range(3, len(price_data['t']))]
    return price_data

def add_average_true_range_data(price_data, atr_range):
    tr = []
    for i in range(0, len(price_data['t'])):
        if i < 1:
            tr.append(0)
        else:
            tr.append(max((price_data['h'][i] - price_data['l'][i])/price_data['l'][i], abs(price_data['h'][i] - price_data['c'][i-1])/min(price_data['h'][i], price_data['c'][i-1]), abs(price_data['l'][i] - price_data['c'][i-1])/min(price_data['l'][i], price_data['c'][i-1]))*100)
    price_data['tr2'] = tr
    atr = []
    for i in range(0, len(price_data['t'])):
        if i < atr_range:
            atr.append(0)
        else:
            atr.append(sum(price_data['tr2'][i-atr_range:i])/atr_range)
    price_data['atr'] = atr
    atr_sma = []
    for i in range(0, len(price_data['t'])):
        if i < 3:
            atr_sma.append(0)
        else:
            atr_sma.append(sum(price_data['atr'][i-3:i])/3)
    price_data['atr_sma'] = atr_sma
    return price_data  

def add_sma_data(price_data, sma_range):
    sma = []
    for i in range(0, len(price_data['t'])):
        if i < sma_range:
            sma.append(price_data['c'][i])
        else:
            sma.append(sum(price_data['c'][i-sma_range:i])/sma_range)
    price_data['sma'] = sma
    return price_data

# add volume weighted average price data to the price data
def add_vwap_data(price_data):
    vwap = []
    for i in range(0, len(price_data['t'])):
        vwap.append(sum([(price_data['c'][j] + price_data['h'][j] + price_data['l'][j])/3*price_data['v'][j] for j in range(0, i+1)])/sum(price_data['v'][0:i+1]))
    price_data['vwap'] = vwap
    return price_data
        
def add_all_indicators(price_data):
    price_data = add_stochastic_data(price_data, sc.stoch_range)
    #price_data = add_ease_of_movement_data(price_data)
    #price_data = add_emv_moving_average_data(price_data)
    #price_data = add_volume_data(price_data)
    price_data = add_macd_data(price_data)
    price_data = add_bollinger_bands_data(price_data, sc.bb_range)
    # price_data = add_adx_data(price_data, sc.adx_range)
    price_data = add_average_true_range_data(price_data, sc.atr_range)
    price_data = add_sma_data(price_data, sc.sma_range)
    price_data = add_vwap_data(price_data)
    return price_data


def get_buy_and_sell_points_vwap(price_data):
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])
    short = False
    buy = False  
    prev_short_open_price = 0
    prev_buy_price = 0
    for i in range(0, len(price_data['t'])):
        df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'hold']
    for i in range(sc.sma_range + 1, len(price_data['t'])):
        short = price_data['sma'][i]/price_data['c'][i] > 1 and price_data['vwap'][i]/price_data['c'][i] > 1
        buy = price_data['c'][i]/price_data['sma'][i] > 1 and price_data['c'][i]/price_data['vwap'][i] > 1
        if short and prev_short_open_price != 0 and prev_short_open_price/price_data['c'][i] > 1.01 and price_data['slowk'][i] < 20 and price_data['slowk'][i] > price_data['slowd'][i] and price_data['slowk'][i-1] < price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'short_close'
        elif buy and prev_buy_price != 0 and price_data['c'][i]/prev_buy_price > 1.01 and price_data['slowk'][i] > 80 and price_data['slowk'][i] < price_data['slowd'][i] and price_data['slowk'][i-1] > price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'sell'
        elif short and price_data['slowk'][i] > 80 and price_data['slowk'][i] < price_data['slowd'][i] and price_data['slowk'][i-1] > price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'short_open'
            prev_short_open_price = price_data['c'][i]
        elif buy and price_data['slowk'][i] < 20 and price_data['slowk'][i] > price_data['slowd'][i] and price_data['slowk'][i-1] < price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'buy'
            prev_buy_price = price_data['c'][i]

    return df

# use stochastic to determine if the price is trending
def get_buy_and_sell_points_shorting(price_data, buy_thres, sell_thres, change_consec, change_diff):
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])
    prev_price = 0
    prev_short_price = 0
    prev_buy = False
    prev_sell = False
    prev_short_open = False
    prev_short_close = False
    short = False
    for i in range(0, len(price_data['t'])):
        df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'hold']
    for i in range(sc.sma_range, len(price_data['t'])):
        short = price_data['vwap'][i] > price_data['c'][i] and price_data['c'][i] < price_data['sma'][i]
        if not short and (prev_price == 0 or (prev_price/price_data['c'][i] > change_consec and prev_buy) or (prev_price/price_data['c'][i] > change_diff and prev_sell)) and price_data['slowk'][i] < buy_thres and price_data['slowk'][i] > price_data['slowd'][i] and price_data['slowk'][i-1] < price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'buy'
            prev_price = price_data['c'][i]
            prev_buy = True
            prev_sell = False
        elif not short and (prev_price == 0 or (price_data['c'][i]/prev_price > change_consec and prev_sell) or (price_data['c'][i]/prev_price > change_diff and prev_buy)) and price_data['slowk'][i] > sell_thres and price_data['slowk'][i] < price_data['slowd'][i] and price_data['slowk'][i-1] > price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'sell'
            prev_price = price_data['c'][i]
            prev_buy = False
            prev_sell = True
        elif short and (prev_short_price == 0 or (price_data['c'][i]/prev_short_price > change_consec and prev_short_open) or (price_data['c'][i]/prev_short_price > change_diff and prev_short_close)) and price_data['slowk'][i] > sell_thres and price_data['slowk'][i] < price_data['slowd'][i] and price_data['slowk'][i-1] > price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'short_open'
            prev_short_price = price_data['c'][i]
            prev_short_open = True
            prev_short_close = False
        elif short and (prev_short_price == 0 or (prev_short_price/price_data['c'][i] > change_consec and prev_short_close) or (prev_short_price/price_data['c'][i] > change_diff and prev_short_open)) and price_data['slowk'][i] < buy_thres and price_data['slowk'][i] > price_data['slowd'][i] and price_data['slowk'][i-1] < price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'short_close'
            prev_short_price = price_data['c'][i]
            prev_short_open = False
            prev_short_close = True
    return df

def get_buy_and_sell_points_only_up_trend(price_data, buy_thres, sell_thres, change_consec, change_diff):
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])
    prev_price = 0
    prev_buy = False
    prev_sell = False
    up_trend = False
    for i in range(0, len(price_data['t'])):
        df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'hold']
    for i in range(sc.sma_range, len(price_data['t'])):
        up_trend = price_data['c'][i] > price_data['vwap'][i] and price_data['c'][i] > price_data['sma'][i]
        if up_trend and (prev_price == 0 or (prev_price/price_data['c'][i] > change_consec and prev_buy) or (prev_price/price_data['c'][i] > change_diff and prev_sell)) and price_data['slowk'][i] < buy_thres and price_data['slowk'][i] > price_data['slowd'][i] and price_data['slowk'][i-1] < price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'buy'
            prev_price = price_data['c'][i]
            prev_buy = True
            prev_sell = False
        elif up_trend and (prev_price == 0 or (price_data['c'][i]/prev_price > change_consec and prev_sell) or (price_data['c'][i]/prev_price > change_diff and prev_buy)) and price_data['slowk'][i] > sell_thres and price_data['slowk'][i] < price_data['slowd'][i] and price_data['slowk'][i-1] > price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'sell'
            prev_price = price_data['c'][i]
            prev_buy = False
            prev_sell = True
    return df

def get_buy_and_sell_points_all(price_data, buy_thres, sell_thres, change_consec, change_diff):
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])
    prev_price = 0
    prev_buy = False
    prev_sell = False
    for i in range(0, len(price_data['t'])):
        df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'hold']
    for i in range(sc.sma_range, len(price_data['t'])):
        if (prev_price == 0 or (prev_price/price_data['c'][i] > change_consec and prev_buy) or (prev_price/price_data['c'][i] > change_diff and prev_sell)) and price_data['slowk'][i] < buy_thres and price_data['slowk'][i] > price_data['slowd'][i] and price_data['slowk'][i-1] < price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'buy'
            prev_price = price_data['c'][i]
            prev_buy = True
            prev_sell = False
        elif (prev_price == 0 or (price_data['c'][i]/prev_price > change_consec and prev_sell) or (price_data['c'][i]/prev_price > change_diff and prev_buy)) and price_data['slowk'][i] > sell_thres and price_data['slowk'][i] < price_data['slowd'][i] and price_data['slowk'][i-1] > price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'sell'
            prev_price = price_data['c'][i]
            prev_buy = False
            prev_sell = True
    return df

# simulate the profitability if buying and selling over the time period
def simulate_buying_and_selling(df, return_chart=False):
    # initialize the money and the number of stocks
    if return_chart:
        money_history_df = pd.DataFrame(columns=['t', 'money', 'stop_loss', 'short_stop_loss'])
    money = sc.starting_money
    num_stocks = sc.starting_stocks
    num_short_stocks_owed = sc.starting_short_stocks
    money += num_short_stocks_owed * df['price'][0]
    money -= num_stocks * df['price'][0]
    prev_price = 0
    prev_sell = 0
    prev_short_price = 0
    prev_short_sell = 0
    short_stop_loss = False
    stop_loss = False
    # go through the data frame and simulate buying and selling
    for i in range(0, len(df)):
        if df['buy/sell/hold'][i] == 'buy':
            if prev_price != 0 and money >= sc.investment * prev_price/df['price'][i]:
                num_stocks += sc.investment*(prev_price/df['price'][i])*(1-sc.transaction_fee)/df['price'][i]
                money -= sc.investment * (prev_price/df['price'][i])
            elif money > 0 and prev_price != 0:
                num_stocks += money*(1-sc.transaction_fee)/df['price'][i]
                money = 0
            elif prev_price == 0 and money >= sc.investment:
                num_stocks += sc.investment*(1-sc.transaction_fee)/df['price'][i]
                money -= sc.investment
            prev_price = df['price'][i]
        elif df['buy/sell/hold'][i] == 'sell':
            if prev_price != 0 and num_stocks >= sc.investment/prev_price:
                money += df['price'][i]/prev_price*sc.investment*(1-sc.transaction_fee)
                num_stocks -= sc.investment/prev_price
            elif num_stocks > 0 and prev_price != 0:
                money += df['price'][i]*num_stocks*(1-sc.transaction_fee)
                num_stocks = 0
            elif num_stocks > sc.investment/df['price'][i]:
                money += sc.investment*(1-sc.transaction_fee)
                num_stocks -= sc.investment/df['price'][i]
            prev_price = df['price'][i]
            prev_sell = df['price'][i]
        elif df['buy/sell/hold'][i] == 'big_sell':
            if num_stocks > 0:
                money += df['price'][i]*num_stocks*(1-sc.transaction_fee)
                num_stocks = 0
            prev_price = df['price'][i]
            prev_sell = df['price'][i]
        elif df['buy/sell/hold'][i] == 'short_open':
            if prev_short_price != 0:
                money += (df['price'][i]/prev_short_price)*sc.investment*(1-sc.transaction_fee)
                num_short_stocks_owed += sc.investment/prev_short_price
            else:
                money += sc.investment*(1-sc.transaction_fee)
                num_short_stocks_owed += sc.investment/df['price'][i]
            prev_short_price = df['price'][i]
        elif df['buy/sell/hold'][i] == 'short_close':
            if prev_short_price != 0 and num_short_stocks_owed >= sc.investment/prev_short_price:
                money -= df['price'][i]/prev_short_price*sc.investment*(1+sc.transaction_fee)
                num_short_stocks_owed -= sc.investment/prev_short_price
            elif num_short_stocks_owed > 0 and prev_short_price != 0:
                money -= df['price'][i]*num_short_stocks_owed*(1+sc.transaction_fee)
                num_short_stocks_owed = 0
            elif num_short_stocks_owed > sc.investment/df['price'][i]:
                money -= sc.investment*(1+sc.transaction_fee)
                num_short_stocks_owed -= sc.investment/df['price'][i]
            prev_short_price = df['price'][i]
            prev_short_sell = df['price'][i]
        elif df['buy/sell/hold'][i] == 'big_short_close':
            if num_short_stocks_owed > 0:
                money -= df['price'][i]*num_short_stocks_owed*(1+sc.transaction_fee)
                num_short_stocks_owed = 0
            prev_short_price = df['price'][i]
            prev_short_sell = df['price'][i]
        # stoploss for shorting
        #if prev_short_sell != 0 and df['price'][i]/prev_short_sell > 1.1 and num_short_stocks_owed > 0:
        #    money -= num_short_stocks_owed*df['price'][i]*(1+sc.transaction_fee)
        #    num_short_stocks_owed = 0
        #    short_stop_loss = True
        #    prev_short_price = df['price'][i]
        #    prev_short_sell = df['price'][i]
        # stoploss for buying
        #if prev_sell != 0 and prev_sell/df['price'][i] > 1.1 and num_stocks > 0:
        #    money += num_stocks*df['price'][i]*(1-sc.transaction_fee)
        #    num_stocks = 0
        #    stop_loss = True
        #    prev_price = df['price'][i]
        #    prev_sell = df['price'][i]
        if return_chart:
            money_history_df.loc[i] = [df['time'][i], money, stop_loss, short_stop_loss]
        short_stop_loss = False
        stop_loss = False

            
    # at the end of the simulation, sell all stocks, and pay off all short stocks
    money += num_stocks * df['price'][len(df)-1]
    if return_chart:
        money_history_df.loc[len(money_history_df)] = [dr.unix_to_date(dr.date_to_unix(df['time'][len(df)-1]) + 1), money, False, False]
    money -= num_short_stocks_owed * df['price'][len(df)-1]
    if return_chart:
        money_history_df.loc[len(money_history_df)] = [dr.unix_to_date(dr.date_to_unix(df['time'][len(df)-1]) + 2), money, False, False]
    if return_chart:
        return money_history_df
    return money

if sc.use_crypto:
    price_data = get_crypto_price_data(sc.crypto, sc.interval)
else:
    price_data = get_price_data(sc.ticker, sc.interval)

indicator_data = add_all_indicators(price_data)

# optimize stochastic parameters with optuna
def stoch_objective(trial, indicator_data):
    stoch_range = trial.suggest_int('stoch_range', 2, int(len(indicator_data['t'])/10))
    sma_range = trial.suggest_int('sma_range', 2, int(len(indicator_data['t'])/7))
    indicator_data = add_stochastic_data(indicator_data, stoch_range)
    indicator_data = add_sma_data(indicator_data, sma_range)
    df = get_buy_and_sell_points_shorting(indicator_data, sc.stoch_buy, sc.stoch_sell, sc.change_consec, sc.change_diff)
    profit = simulate_buying_and_selling(df)
    return profit

if sc.optimize_params:
    study = optuna.create_study(direction='maximize')
    study.optimize(lambda trial: stoch_objective(trial, indicator_data), n_trials=sc.optimization_depth)
    indicator_data = add_stochastic_data(indicator_data, study.best_params['stoch_range'])
    indicator_data = add_sma_data(indicator_data, study.best_params['sma_range'])
    df1 = get_buy_and_sell_points_shorting(indicator_data, sc.stoch_buy, sc.stoch_sell, sc.change_consec, sc.change_diff)
else:
    df1 = get_buy_and_sell_points_shorting(indicator_data, sc.stoch_buy, sc.stoch_sell, sc.change_consec, sc.change_diff)

indicator_data = add_stochastic_data(indicator_data, sc.stoch_range)
indicator_data = add_sma_data(indicator_data, sc.sma_range)

df2 = get_buy_and_sell_points_only_up_trend(indicator_data, sc.stoch_buy, sc.stoch_sell, sc.change_consec, sc.change_diff)

df3 = get_buy_and_sell_points_all(indicator_data, sc.stoch_buy, sc.stoch_sell, sc.change_consec, sc.change_diff)

df4 = get_buy_and_sell_points_vwap(indicator_data)

# plot the prices over time, highlighting the buy and sell points/short opens and closes on streamlit
def plot_buy_and_sell_points(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['time'], y=df['price'], mode='lines', name='price'))
    fig.add_trace(go.Scatter(x=df[df['buy/sell/hold'] == 'buy']['time'], y=df[df['buy/sell/hold'] == 'buy']['price'], mode='markers', name='buy', marker_color='green'))
    fig.add_trace(go.Scatter(x=df[df['buy/sell/hold'] == 'sell']['time'], y=df[df['buy/sell/hold'] == 'sell']['price'], mode='markers', name='sell', marker_color='red'))
    fig.add_trace(go.Scatter(x=df[df['buy/sell/hold'] == 'short_open']['time'], y=df[df['buy/sell/hold'] == 'short_open']['price'], mode='markers', name='short_open', marker_color='blue'))
    fig.add_trace(go.Scatter(x=df[df['buy/sell/hold'] == 'short_close']['time'], y=df[df['buy/sell/hold'] == 'short_close']['price'], mode='markers', name='short_close', marker_color='orange'))
    fig.add_trace(go.Scatter(x=df[df['buy/sell/hold'] == 'big_sell']['time'], y=df[df['buy/sell/hold'] == 'big_sell']['price'], mode='markers', name='sell all', marker_color='darkred'))
    fig.add_trace(go.Scatter(x=df[df['buy/sell/hold'] == 'big_short_close']['time'], y=df[df['buy/sell/hold'] == 'big_short_close']['price'], mode='markers', name='close all shorts', marker_color='black'))
    fig.update_layout(title='Results', xaxis_title='Date', yaxis_title='Price')
    st.plotly_chart(fig)

def plot_stochastic_data(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['slowk'], mode='lines', name='slowk'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['slowd'], mode='lines', name='slowd'))
    fig.update_layout(title='Stochastic Data', xaxis_title='Date', yaxis_title='%k and %d')
    st.plotly_chart(fig)

def plot_moving_average(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['sma'], mode='lines', name='slow moving average'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['c'], mode='lines', name='price'))
    fig.update_layout(title='Moving Average', xaxis_title='Date', yaxis_title='Price')
    st.plotly_chart(fig)

def plot_emv(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['emv'], mode='lines', name='emv'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['ema'], mode='lines', name='ema'))
    fig.update_layout(title='EMV', xaxis_title='Date', yaxis_title='EMV and EMA')
    st.plotly_chart(fig)

def plot_volume(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['v'], mode='lines', name='volume'))
    fig.update_layout(title='Volume', xaxis_title='Date', yaxis_title='Volume')
    st.plotly_chart(fig)

def plot_macd(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['macd'], mode='lines', name='macd'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['macavg'], mode='lines', name='macd sma'))
    fig.update_layout(title='MACD', xaxis_title='Date', yaxis_title='MACD')
    st.plotly_chart(fig)

def plot_ema12_ema26(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['ema12'], mode='lines', name='ema12'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['ema26'], mode='lines', name='ema26'))
    fig.update_layout(title='EMA12 and EMA26', xaxis_title='Date', yaxis_title='EMA12 and EMA26')
    st.plotly_chart(fig)

def plot_bollinger_bands(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['upper_bb'], mode='lines', name='upperband'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['bsma'], mode='lines', name='middleband'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['lower_bb'], mode='lines', name='lowerband'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['c'], mode='lines', name='price'))
    fig.update_layout(title='Bollinger Bands', xaxis_title='Date', yaxis_title='Bollinger Bands')
    st.plotly_chart(fig)

def plot_adx(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['adx'], mode='lines', name='adx'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['adx_avg'], mode='lines', name='adx average'))
    fig.update_layout(title='ADX', xaxis_title='Date', yaxis_title='ADX')
    st.plotly_chart(fig)

def plot_investments(money_history):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=money_history['t'], y=money_history['money'], mode='lines', name='money'))
    fig.add_trace(go.Scatter(x=money_history[money_history['stop_loss']]['t'], y=money_history[money_history['stop_loss']]['money'], mode='markers', name='stop loss', marker_color='red'))
    fig.add_trace(go.Scatter(x=money_history[money_history['short_stop_loss']]['t'], y=money_history[money_history['short_stop_loss']]['money'], mode='markers', name='short stop loss', marker_color='orange'))
    fig.update_layout(title='Investments', xaxis_title='Date', yaxis_title='Investments')
    st.plotly_chart(fig)
    
def plot_atr(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['atr'], mode='lines', name='atr'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['atr_sma'], mode='lines', name='atr average'))
    fig.update_layout(title='ATR', xaxis_title='Date', yaxis_title='ATR')
    st.plotly_chart(fig)

def plot_vwap(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['c'], mode='lines', name='price'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['vwap'], mode='lines', name='vwap'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['sma'], mode='lines', name='moving average'))
    fig.update_layout(title='VWAP', xaxis_title='Date', yaxis_title='VWAP')
    st.plotly_chart(fig)

plot_vwap(indicator_data)
st.header('buy and sell points vwap')
plot_buy_and_sell_points(df4)
st.header('Buy and Sell Points buy, sell, short')
plot_buy_and_sell_points(df1)
st.header('Buy and Sell Points only up trend')
plot_buy_and_sell_points(df2)
st.header('Buy and Sell Points all')
plot_buy_and_sell_points(df3)
st.header('Change in liquidity vwap')
plot_investments(simulate_buying_and_selling(df4, True))
st.header('Change in liquidity including shorting')
plot_investments(simulate_buying_and_selling(df1, True))
st.header('Change in liquidity only up trend')
plot_investments(simulate_buying_and_selling(df2, True))
st.header('Change in liquidity all')
plot_investments(simulate_buying_and_selling(df3, True))
st.header('Profitability')
st.write('vwap: ', (simulate_buying_and_selling(df4)/(sc.starting_money) * 100 - 100), '%')
st.write('buy/sell/short profitability: ', (simulate_buying_and_selling(df1)/(sc.starting_money) * 100 - 100), '%')
st.write('buy/sell only up trend profitability: ', (simulate_buying_and_selling(df2)/(sc.starting_money) * 100 - 100), '%')
st.write('buy/sell all profitability: ', (simulate_buying_and_selling(df3)/(sc.starting_money) * 100 - 100), '%')
st.header('Real Change')
st.write('change in price: ' , (indicator_data['c'][-1] - indicator_data['c'][0]) / indicator_data['c'][0] * 100, '%')
plot_moving_average(indicator_data)
plot_stochastic_data(indicator_data)
plot_atr(indicator_data)
plot_bollinger_bands(indicator_data)
plot_volume(indicator_data)
plot_macd(indicator_data)
plot_ema12_ema26(indicator_data)