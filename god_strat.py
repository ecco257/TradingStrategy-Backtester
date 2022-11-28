import config
import finnhub as fh
import pandas as pd
import date_range as dr
import sim_config as sc
import streamlit as st
from plotly import graph_objs as go
import optuna

st.title('Strategy 2')

# initialize the Finnhub API client
finnhub_client = fh.Client(api_key=config.API_KEY)

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
            k.append((price_data['c'][i] - min(price_data['l'][i-stoch_range:i]))/(max(price_data['h'][i-stoch_range:i]) - min(price_data['l'][i-stoch_range:i]))*100)
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
            sma.append(0)
        else:
            sma.append(sum(price_data['c'][i-sma_range:i])/sma_range)
    price_data['sma'] = sma
    return price_data

def add_all_indicators(price_data):
    price_data = add_stochastic_data(price_data, sc.stoch_range)
    #price_data = add_ease_of_movement_data(price_data)
    #price_data = add_emv_moving_average_data(price_data)
    #price_data = add_volume_data(price_data)
    price_data = add_macd_data(price_data)
    price_data = add_bollinger_bands_data(price_data, sc.bb_range)
    price_data = add_adx_data(price_data, sc.adx_range)
    price_data = add_average_true_range_data(price_data, sc.atr_range)
    price_data = add_sma_data(price_data, sc.sma_range)
    return price_data

# use adx to determine if the price is trending
def get_buy_and_sell_points_adx(price_data, buy_thres, sell_thres):
    # initialize the data frame that will be used to store the time stamps to buy or sell the ticker and whether it is a 
    # buy or sell
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])
    # initially everything is a hold
    for i in range(0, len(price_data['t'])):
        df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'hold']
    for i in range(1, len(price_data['t'])):
        if price_data['adx'][i] > buy_thres and price_data['adx'][i-1] < buy_thres:
            df.loc[i, 'buy/sell/hold'] = 'buy'
        elif price_data['adx'][i] < sell_thres and price_data['adx'][i-1] > sell_thres:
            df.loc[i, 'buy/sell/hold'] = 'sell'
    return df

# use stochastic to determine if the price is trending
def get_buy_and_sell_points_stoch(price_data, buy_thres, sell_thres, change_consec, change_diff):
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
        short = price_data['c'][i] < price_data['sma'][i]
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
        elif short and (prev_short_price == 0 or (price_data['c'][i]/prev_short_price > change_consec and prev_short_open) or (price_data['c'][i]/prev_short_price > change_diff and prev_short_close)) and price_data['slowk'][i] > buy_thres and price_data['slowk'][i] < price_data['slowd'][i] and price_data['slowk'][i-1] > price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'short_open'
            prev_short_price = price_data['c'][i]
            prev_short_open = True
            prev_short_close = False
        elif short and (prev_short_price == 0 or (prev_short_price/price_data['c'][i] > change_consec and prev_short_close) or (prev_short_price/price_data['c'][i] > change_diff and prev_short_open)) and price_data['slowk'][i] < sell_thres and price_data['slowk'][i] > price_data['slowd'][i] and price_data['slowk'][i-1] < price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'short_close'
            prev_short_price = price_data['c'][i]
            prev_short_open = False
            prev_short_close = True
    return df

# use bollinger bands to determine if the price is trending
def get_buy_and_sell_points_bollinger(price_data, bollinger_buy_gap, bollinger_sell_gap, bb_range, change_consec, change_diff):
    # initialize the data frame that will be used to store the time stamps to buy or sell the ticker and whether it is a 
    # buy or sell
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])
    # initially everything is a hold
    last_bb_buy = False
    last_bb_sell = False
    last_price = 0
    
    for i in range(0, len(price_data['t'])):
        df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'hold']
    for i in range(bb_range + 1, len(price_data['t'])):
        # if the price is above the upper bollinger band and the previous value was below the upper bollinger band, sell
        if (last_price == 0 or ((price_data['c'][i]/last_price > change_consec and last_bb_sell) or (price_data['c'][i]/last_price > change_diff and last_bb_buy))) and price_data['upper_bb'][i]/price_data['c'][i] < bollinger_buy_gap and price_data['upper_bb'][i-1]/price_data['c'][i-1] > bollinger_buy_gap:
            df.loc[i, 'buy/sell/hold'] = 'sell'
            last_bb_buy = False
            last_bb_sell = True
            last_price = price_data['c'][i]
        # if the price is below the lower bollinger band and the previous value was above the lower bollinger band, buy
        elif (last_price == 0 or ((last_price/price_data['c'][i] > change_consec and last_bb_buy) or (last_price/price_data['c'][i] > change_diff and last_bb_sell))) and price_data['c'][i]/price_data['lower_bb'][i] < bollinger_sell_gap and price_data['c'][i-1]/price_data['lower_bb'][i-1] > bollinger_sell_gap:
            df.loc[i, 'buy/sell/hold'] = 'buy'
            last_bb_buy = True
            last_bb_sell = False
            last_price = price_data['c'][i]
        elif (last_price == 0 or ((last_price/price_data['c'][i] > change_consec and last_bb_buy) or (last_price/price_data['c'][i] > change_diff and last_bb_sell))) and price_data['c'][i] > price_data['lower_bb'][i] and price_data['c'][i-1] < price_data['lower_bb'][i-1] and last_price > price_data['c'][i]:
            df.loc[i, 'buy/sell/hold'] = 'buy'
            last_bb_buy = True
            last_bb_sell = False
            last_price = price_data['c'][i]
        elif (last_price == 0 or ((price_data['c'][i]/last_price > change_consec and last_bb_sell) or (price_data['c'][i]/last_price > change_diff and last_bb_buy)))  and price_data['c'][i] < price_data['upper_bb'][i] and price_data['c'][i-1] > price_data['upper_bb'][i-1] and last_price < price_data['c'][i]:
            df.loc[i, 'buy/sell/hold'] = 'sell'
            last_bb_buy = False
            last_bb_sell = True
            last_price = price_data['c'][i]
    return df

def get_buy_and_sell_bb_stoch_dynamic(price_data, bb_range, buy_thres, sell_thres, change_factor, buy_constant, sell_constant):
    
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])

    prev_price = 0
    prev_buy = False
    prev_sell = False

    for i in range(0, len(price_data['t'])):
        df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'hold']

    for i in range(bb_range + 1, len(price_data['t'])):
        change_consec = price_data['atr'][i] / change_factor * 1 + 1
        change_diff = price_data['atr'][i] / change_factor * 1 + 1
        if (prev_price == 0 or (prev_price/price_data['c'][i] > change_consec and prev_buy) or (prev_price/price_data['c'][i] > change_diff and prev_sell)) and price_data['slowk'][i] / (price_data['atr'][i] * buy_constant) < buy_thres and price_data['slowk'][i] > price_data['slowd'][i] and price_data['slowk'][i-1] < price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'buy'
            prev_price = price_data['c'][i]
            prev_buy = True
            prev_sell = False
        elif (prev_price == 0 or (price_data['c'][i]/prev_price > change_consec and prev_sell) or (price_data['c'][i]/prev_price > change_diff and prev_buy)) and price_data['slowk'][i] * (price_data['atr'][i] * sell_constant) > sell_thres and price_data['slowk'][i] < price_data['slowd'][i] and price_data['slowk'][i-1] > price_data['slowd'][i-1]:
            df.loc[i, 'buy/sell/hold'] = 'sell'
            prev_price = price_data['c'][i]
            prev_buy = False
            prev_sell = True
    
    return df

# simulate the profitability if buying and selling over the time period
def simulate_buying_and_selling(df):
    # initialize the money and the number of stocks
    money_history_df = pd.DataFrame(columns=['t', 'money'])
    money = sc.starting_money
    num_stocks = sc.starting_stocks
    num_short_stocks = sc.starting_short_stocks
    prev = 'hold'
    prev_price = 0
    prev_short_price = 0
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
            prev = 'buy'
            prev_price = df['price'][i]
            money_history_df.loc[len(money_history_df)] = [df['time'][i], money]
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
            prev = 'sell'
            prev_price = df['price'][i]
            money_history_df.loc[len(money_history_df)] = [df['time'][i], money]
        elif df['buy/sell/hold'][i] == 'short_open':
            if prev_short_price != 0 and money >= sc.investment * df['price'][i]/prev_short_price:
                num_short_stocks += sc.investment*(df['price'][i]/prev_short_price)*(1-sc.transaction_fee)/df['price'][i]
                money -= sc.investment * (df['price'][i]/prev_short_price)
            elif money > 0 and prev_short_price != 0:
                num_short_stocks += money*(1-sc.transaction_fee)/df['price'][i]
                money = 0
            elif prev_short_price == 0 and money >= sc.investment:
                num_short_stocks += sc.investment*(1-sc.transaction_fee)/df['price'][i]
                money -= sc.investment
            prev = 'short_open'
            prev_short_price = df['price'][i]
            money_history_df.loc[len(money_history_df)] = [df['time'][i], money]
        elif df['buy/sell/hold'][i] == 'short_close':
            if prev_short_price != 0 and num_short_stocks >= sc.investment*(prev_short_price/df['price'][i])/df['price'][i]:
                money += sc.investment*(prev_short_price/df['price'][i])*(1-sc.transaction_fee)
                num_short_stocks -= sc.investment*(prev_short_price/df['price'][i])/df['price'][i]
            elif num_short_stocks > 0 and prev_short_price != 0:
                money += prev_short_price*num_short_stocks*(1-sc.transaction_fee)
                num_short_stocks = 0
            prev = 'short_close'
            prev_short_price = df['price'][i]
            money_history_df.loc[len(money_history_df)] = [df['time'][i], money]
            
    # backtrack to last buy to make an accurate profit calculation
    return money, money_history_df

if sc.use_crypto:
    price_data = get_crypto_price_data(sc.crypto, sc.interval)
else:
    price_data = get_price_data(sc.ticker, sc.interval)

indicator_data = add_all_indicators(price_data)

# optimize stochastic parameters with optuna
def stoch_objective(trial, indicator_data):
    buy_thres = trial.suggest_float('buy_thres', 0, 100)
    sell_thres = trial.suggest_float('sell_thres', 0, 100)
    stoch_range = trial.suggest_int('stoch_range', 2, int(len(indicator_data['t'])/10))
    change_consec = trial.suggest_float('change_consec', 1, 1.1)
    change_diff = trial.suggest_float('change_diff', 1, 1.1)
    indicator_data = add_stochastic_data(indicator_data, stoch_range)
    df = get_buy_and_sell_points_stoch(indicator_data, buy_thres, sell_thres, change_consec, change_diff)
    profit = simulate_buying_and_selling(df)
    return profit

def adx_objective(trial, indicator_data):
    buy_thres = trial.suggest_float('buy_thres', 0, 100)
    sell_thres = trial.suggest_float('sell_thres', 0, 100)
    adx_range = trial.suggest_int('adx_range', 2, 30)
    indicator_data = add_adx_data(indicator_data, adx_range)
    df = get_buy_and_sell_points_adx(indicator_data, buy_thres, sell_thres)
    profit = simulate_buying_and_selling(df)
    return profit

def bb_objective(trial, indicator_data):
    bollinger_buy_gap = trial.suggest_float('bollinger_buy_gap', 1, 2)
    bollinger_sell_gap = trial.suggest_float('bollinger_sell_gap', 1, 2)
    bb_range = trial.suggest_int('bb_range', 2, int(len(indicator_data['t'])/10))
    change_consec = trial.suggest_float('change_consec', 1, 2)
    change_diff = trial.suggest_float('change_diff', 1, 2)
    indicator_data = add_bollinger_bands_data(indicator_data, bb_range)
    df = get_buy_and_sell_points_bollinger(indicator_data, bollinger_buy_gap, bollinger_sell_gap, bb_range, change_consec, change_diff)
    profit = simulate_buying_and_selling(df)
    return profit

def bb_stoch_objective(trial, indicator_data):
    buy_constant = trial.suggest_float('buy_constant', 0, 2)
    sell_constant = trial.suggest_float('sell_constant', 0, 2)
    df = get_buy_and_sell_bb_stoch_dynamic(indicator_data, sc.bb_range, sc.stoch_buy, sc.stoch_sell, 1000, buy_constant, sell_constant) 
    profit = simulate_buying_and_selling(df)[0]
    return profit

df1 = get_buy_and_sell_points_stoch(indicator_data, sc.stoch_buy, sc.stoch_sell, sc.change_consec, sc.change_diff)

df3 = get_buy_and_sell_points_bollinger(indicator_data, sc.bollinger_buy_gap, sc.bollinger_sell_gap, sc.bb_range, sc.change_consec, sc.change_diff)


# plot the prices over time, highlighting the buy and sell points on streamlit
def plot_buy_and_sell_points(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['time'], y=df['price'], mode='lines', name='price'))
    fig.add_trace(go.Scatter(x=df[df['buy/sell/hold'] == 'buy']['time'], y=df[df['buy/sell/hold'] == 'buy']['price'], mode='markers', name='buy', marker_color='green'))
    fig.add_trace(go.Scatter(x=df[df['buy/sell/hold'] == 'sell']['time'], y=df[df['buy/sell/hold'] == 'sell']['price'], mode='markers', name='sell', marker_color='red'))
    fig.add_trace(go.Scatter(x=df[df['buy/sell/hold'] == 'short_open']['time'], y=df[df['buy/sell/hold'] == 'short_open']['price'], mode='markers', name='short_open', marker_color='blue'))
    fig.add_trace(go.Scatter(x=df[df['buy/sell/hold'] == 'short_close']['time'], y=df[df['buy/sell/hold'] == 'short_close']['price'], mode='markers', name='short_close', marker_color='orange'))
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

# plot ema12 and ema26 over time on streamlit
def plot_ema12_ema26(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['ema12'], mode='lines', name='ema12'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['ema26'], mode='lines', name='ema26'))
    fig.update_layout(title='EMA12 and EMA26', xaxis_title='Date', yaxis_title='EMA12 and EMA26')
    st.plotly_chart(fig)

# plot bollinger bands over time on streamlit
def plot_bollinger_bands(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['upper_bb'], mode='lines', name='upperband'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['sma'], mode='lines', name='middleband'))
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
    fig.add_trace(go.Scatter(x=[t for t in money_history['t']], y=money_history['money'], mode='lines', name='money'))
    # fig.add_trace(go.Scatter(x=[t for t in money_history['t']], y=money_history['stocks'], mode='lines', name='stocks'))
    fig.update_layout(title='Investments', xaxis_title='Date', yaxis_title='Investments')
    st.plotly_chart(fig)
    
def plot_atr(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['atr'], mode='lines', name='atr'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['atr_sma'], mode='lines', name='atr average'))
    fig.update_layout(title='ATR', xaxis_title='Date', yaxis_title='ATR')
    st.plotly_chart(fig)


st.header('Buy and Sell Points bb')
plot_buy_and_sell_points(df3)
st.header('Buy and Sell Points stoch')
plot_buy_and_sell_points(df1)
st.header('Profitability')
st.write('bb profitability: ', simulate_buying_and_selling(df3)[0]/(sc.starting_money + sc.starting_stocks*indicator_data['c'][0] + sc.starting_short_stocks*indicator_data['c'][0]) * 100 - 100, '%')
st.write('stoch profitability: ', (simulate_buying_and_selling(df1)[0]/(sc.starting_money + sc.starting_stocks*indicator_data['c'][0] + sc.starting_short_stocks*indicator_data['c'][0]) * 100 - 100), '%')
st.header('Real Change')
st.write('change in price: ' , (indicator_data['c'][-1] - indicator_data['c'][0]) / indicator_data['c'][0] * 100, '%')
st.header('Investments for stoch')
plot_investments(simulate_buying_and_selling(df1)[1])
st.header('Investments for bb')
plot_investments(simulate_buying_and_selling(df3)[1])
plot_moving_average(indicator_data)
plot_stochastic_data(indicator_data)
plot_atr(indicator_data)
plot_bollinger_bands(indicator_data)
plot_volume(indicator_data)
plot_adx(indicator_data)
plot_macd(indicator_data)
plot_ema12_ema26(indicator_data)