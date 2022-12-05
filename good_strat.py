import config
import finnhub as fh
import pandas as pd
import date_range as dr
import sim_config as sc
import streamlit as st
from plotly import graph_objs as go
import optuna
import math

st.title('Strategy 2?')

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
    
def add_emv_moving_average_data(price_data):
    ma = []
    for i in range(0, len(price_data['t'])):
        if i < 20:
            ma.append(0)
        else:
            ma.append(sum(price_data['emv'][i-20:i])/20)
    price_data['ema'] = ma

def add_volume_data(price_data):
    # add the simple moving average of the volume data to the price data
    ma = []
    for i in range(0, len(price_data['t'])):
        if i < 14:
            ma.append(0)
        else:
            ma.append(sum(price_data['v'][i-14:i])/14)
    price_data['sma_v'] = ma

def add_macd_data(price_data):
    if sc.use_crypto:
        symbol = sc.crypto
    else:
        symbol = sc.ticker
    macd = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'macd')
    price_data['macd'] = macd['macd']
    price_data['macd_signal'] = macd['macdSignal']
    price_data['macd_hist'] = macd['macdHist']

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

def add_average_true_range_data(price_data, atr_range):
    tr = []
    period = 5
    multiplier = 3.5
    for i in range(0, len(price_data['t'])):
        if i < 1:
            tr.append(0)
        else:
            tr.append(max((price_data['h'][i] - price_data['l'][i]), abs(price_data['h'][i] - price_data['c'][i-1]), abs(price_data['l'][i] - price_data['c'][i-1])))
    price_data['tr2'] = tr
    atr = []
    trailing_stop = []
    for i in range(0, len(price_data['t'])):
        if i < atr_range:
            atr.append(0)
            trailing_stop.append(None)
        else:
            atr.append(sum(price_data['tr2'][i-atr_range:i+1])/atr_range)
            loss = multiplier*atr[i]
            prev = trailing_stop[i-1]
            if trailing_stop[i-1] is None:
                prev = 0
            if(price_data['c'][i] > prev and price_data['c'][i-1] > prev):
                trailing_stop.append(max(prev, price_data['c'][i] - loss))
            elif(price_data['c'][i] < prev and price_data['c'][i-1] < prev):
                trailing_stop.append(min(prev, price_data['c'][i] + loss))
            elif(price_data['c'][i] > prev):
                trailing_stop.append(price_data['c'][i] - loss)
            else:
                trailing_stop.append(price_data['c'][i] + loss)
    price_data['atr'] = atr
    price_data['trailing_stop'] = trailing_stop

# add simple moving average to the price data
def add_sma_data(price_data, ema_range):
    sma = []
    sma50 = []
    for i in range(0, len(price_data['t'])):
        if i < ema_range:
            sma.append(None)
        else:
            sma.append(sum(price_data['c'][i-ema_range:i])/ema_range)
        if i < 50:
            sma50.append(None)
        else:
            sma50.append(sum(price_data['c'][i-50:i])/50)
    price_data['sma'] = sma
    price_data['sma50'] = sma50

def add_ichimoku_cloud_data(price_data):
    if sc.use_crypto:
        symbol = sc.crypto
    else:
        symbol = sc.ticker
    moving_average9_high = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': 9, 'seriestype': 'h'})['ema']
    moving_average9_low = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': 9, 'seriestype': 'l'})['ema']
    moving_average26_high = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': 26, 'seriestype': 'h'})['ema']
    moving_average26_low = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': 26, 'seriestype': 'l'})['ema']
    moving_average52_high = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': 52, 'seriestype': 'h'})['ema']
    moving_average52_low = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': 52, 'seriestype': 'l'})['ema']
    conversion_line = []
    base_line = []
    leading_span_a = []
    leading_span_b = []
    lagging_span = []
    time = []
    for i in range(0, len(price_data['t']) + 26):
        if i < len(price_data['t']):
            time.append(price_data['t'][i])
            if i < len(price_data['t']) - 26:
                lagging_span.append(price_data['c'][i+26])
            if i < 8:
                conversion_line.append(None)
            else:
                conversion_line.append((moving_average9_high[i] + moving_average9_low[i])/2)
            if i < 25:
                base_line.append(None)
            else:
                base_line.append((moving_average26_high[i] + moving_average26_low[i])/2)
        else:
            if sc.interval == 'D':
                time.append(time[i-1] + 24*60*60)
            else:
                time.append(time[i-1] + 60*int(sc.interval))

        if i < 26 + 25:
            leading_span_a.append(None)
            leading_span_b.append(None)
        else:
            leading_span_a.append((conversion_line[i-26] + base_line[i-26])/2)
            if i < 52 + 25:
                leading_span_b.append(None)
            else:
                leading_span_b.append((moving_average52_high[i-26] + moving_average52_low[i-26])/2)
    price_data['conversion_line'] = conversion_line
    price_data['base_line'] = base_line
    price_data['leading_span_a'] = leading_span_a
    price_data['leading_span_b'] = leading_span_b
    price_data['lagging_span'] = lagging_span
    price_data['t2'] = time    

# add volume weighted average price data to the price data
def add_vwap_data(price_data):
    vwap = []
    for i in range(0, len(price_data['t'])):
        vwap.append(sum([(price_data['c'][j] + price_data['h'][j] + price_data['l'][j])/3*price_data['v'][j] for j in range(0, i+1)])/sum(price_data['v'][0:i+1]))
    price_data['vwap'] = vwap

def add_all_indicators(price_data):
    add_stochastic_data(price_data, sc.stoch_range)
    #price_data = add_ease_of_movement_data(price_data)
    #price_data = add_emv_moving_average_data(price_data)
    #price_data = add_volume_data(price_data)
    add_macd_data(price_data)
    add_bollinger_bands_data(price_data, sc.bb_range)
    # price_data = add_adx_data(price_data, sc.adx_range)
    add_average_true_range_data(price_data, sc.atr_range)
    add_sma_data(price_data, sc.sma_range)
    add_vwap_data(price_data)
    add_ichimoku_cloud_data(price_data)
    return price_data

def ichimoku_strat(price_data, reward_to_risk):
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])
    in_trade = False
    short = False
    buy = False
    just_got_here = False
    price = 0
    for i in range(0, len(price_data['t'])):
        df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'hold']
    for i in range(52 + 26 + 25, len(price_data['t'])):
        if not in_trade:
            min_span_now = min(price_data['leading_span_a'][i], price_data['leading_span_b'][i])
            max_span_now = max(price_data['leading_span_a'][i], price_data['leading_span_b'][i])
            min_span_26 = min(price_data['leading_span_a'][i-26], price_data['leading_span_b'][i-26])
            max_span_26 = max(price_data['leading_span_a'][i-26], price_data['leading_span_b'][i-26])
            #min_span_1 = min(price_data['leading_span_a'][i-1], price_data['leading_span_b'][i-1])
            #max_span_1 = max(price_data['leading_span_a'][i-1], price_data['leading_span_b'][i-1])
            up_trend = price_data['c'][i] > price_data['trailing_stop'][i]
            if price_data['c'][i] < min_span_now and price_data['lagging_span'][i-26] < min_span_26 and \
                price_data['leading_span_b'][i+26] > price_data['leading_span_a'][i+26] and \
                    price_data['conversion_line'][i] < price_data['base_line'][i] and price_data['slowk'][i] > 80:
                short = True
                buy = False
                in_trade = True
                df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'short_open']
                price = price_data['c'][i]
                if(price_data['trailing_stop'][i] > price_data['c'][i]):
                    stop_loss_price = price_data['trailing_stop'][i]
                else:
                    stop_loss_price = price_data['c'][i] + price_data['atr'][i] * 2
                take_profit_price = price_data['c'][i] * (1-(stop_loss_price/price_data['c'][i]-1) * reward_to_risk)
                just_got_here = True
            elif price_data['c'][i] > max_span_now and price_data['lagging_span'][i-26] > max_span_26 and \
                price_data['leading_span_b'][i+26] < price_data['leading_span_a'][i+26] and \
                    price_data['conversion_line'][i] > price_data['base_line'][i] and price_data['slowk'][i] < 20:
                buy = True
                short = False
                in_trade = True
                df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'buy']
                price = price_data['c'][i]
                if(price_data['trailing_stop'][i] < price_data['c'][i]):
                    stop_loss_price = price_data['trailing_stop'][i]
                else:
                    stop_loss_price = price_data['c'][i] - price_data['atr'][i] * 2
                take_profit_price = price_data['c'][i] * ((1 - stop_loss_price/price_data['c'][i]) * reward_to_risk + 1)
                just_got_here = True 
        else:
            if not just_got_here:
                if buy and price_data['c'][i] < stop_loss_price:
                    df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_sell']
                    in_trade = False
                    buy = False
                elif buy and price_data['c'][i] > take_profit_price and price_data['slowk'][i] > 80:
                    df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_sell']
                    in_trade = False
                    buy = False
                elif buy and price_data['c'][i-1] > take_profit_price and price_data['c'][i] < take_profit_price:
                    df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_sell']
                    in_trade = False
                    buy = False
                elif short and price_data['c'][i] > stop_loss_price:
                    df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_short_close']
                    in_trade = False
                    short = False
                elif short and price_data['c'][i] < take_profit_price and price_data['slowk'][i] < 20 and take_profit_price > 0:
                    df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_short_close']
                    in_trade = False
                    short = False
                elif short and price_data['c'][i-1] < take_profit_price and price_data['c'][i] > take_profit_price and take_profit_price > 0:
                    df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_short_close']
                    in_trade = False
                    short = False
                elif short and price_data['slowk'][i] < 20 and price_data['slowk'][i] > price_data['slowd'][i] and price_data['slowk'][i-1] < price_data['slowd'][i-1]:
                    df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_short_close']
                    in_trade = False
                    short = False
            just_got_here = False
    return df

def stoch_strat(price_data, reward_to_risk):
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])
    in_trade = False
    buy = False
    short = False
    just_got_here = False
    vwap_hit_down_trend = False
    vwap_hit_up_trend = False
    for i in range(0, len(price_data['t'])):
        df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'hold']
    for i in range(200, len(price_data['t'])):
        if not in_trade:
            atr_relative = price_data['atr'][i]/price_data['vwap'][i]
            up_trend = price_data['slowk'][i] < 20 and price_data['sma'][i] < price_data['c'][i]
            down_trend = price_data['slowk'][i] > 80 and price_data['sma'][i] > price_data['c'][i]
            if up_trend:
                buy = True
                short = False
                in_trade = True
                just_got_here = True
                stop_loss_price = price_data['c'][i] - price_data['atr'][i]*reward_to_risk
                take_profit_price = price_data['c'][i] * ((1 - stop_loss_price/price_data['c'][i]) * reward_to_risk + 1)
                df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'buy']
            elif down_trend:
                short = True
                buy = False
                in_trade = True
                just_got_here = True
                stop_loss_price = price_data['c'][i] + price_data['atr'][i]*reward_to_risk
                take_profit_price = price_data['c'][i] * (1-(stop_loss_price/price_data['c'][i]-1) * reward_to_risk)
                df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'short_open']
        if in_trade:
            if not just_got_here:
                if buy and price_data['c'][i] < stop_loss_price and price_data['slowk'][i] > 80:
                    df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_sell']
                    in_trade = False
                    buy = False
                elif buy and price_data['c'][i] > take_profit_price and price_data['slowk'][i] > 80:
                    df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_sell']
                    in_trade = False
                    buy = False
                elif buy and price_data['c'][i-1] > take_profit_price and price_data['c'][i] < take_profit_price:
                    df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_sell']
                    in_trade = False
                    buy = False
                elif short and price_data['c'][i] > stop_loss_price and price_data['slowk'][i] < 20:
                    df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_short_close']
                    in_trade = False
                    short = False
                elif short and price_data['c'][i] < take_profit_price and price_data['slowk'][i] < 20 and take_profit_price > 0:
                    df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_short_close']
                    in_trade = False
                    short = False
                elif short and price_data['c'][i-1] < take_profit_price and price_data['c'][i] > take_profit_price and take_profit_price > 0:
                    df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_short_close']
                    in_trade = False
                    short = False
                elif short and price_data['slowk'][i] < 20 and price_data['slowk'][i] > price_data['slowd'][i] and price_data['slowk'][i-1] < price_data['slowd'][i-1]:
                    df.loc[i] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_short_close']
                    in_trade = False
                    short = False
            just_got_here = False
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
    real_money = money
    prev_price = 0
    prev_sell = 0
    prev_short_price = 0
    prev_short_sell = 0
    short_stop_loss = False
    stop_loss = False
    wins = 0
    losses = 0
    prev_money = 0
    # go through the data frame and simulate buying and selling
    for i in range(0, len(df)):
        if df['buy/sell/hold'][i] == 'buy':
            prev_money = money
            if money > sc.investment:
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
            real_money = money
            if prev_money < money:
                wins += 1
            else:
                losses += 1
        elif df['buy/sell/hold'][i] == 'short_open':
            prev_money = money
            money += sc.investment * (1-sc.transaction_fee)
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
            real_money = money
            if prev_money < real_money:
                wins += 1
            else:
                losses += 1
        if return_chart:
            money_history_df.loc[i] = [df['time'][i], real_money, stop_loss, short_stop_loss]
        short_stop_loss = False
        stop_loss = False            
    # at the end of the simulation, sell all stocks, and pay off all short stocks
    money += num_stocks * df['price'][len(df)-1]
    money -= num_short_stocks_owed * df['price'][len(df)-1]
    if return_chart:
        money_history_df.loc[len(money_history_df)] = [dr.unix_to_date(dr.date_to_unix(df['time'][len(df)-1]) + 1), money, False, False]
        st.write('win rate: ', wins/(wins+losses) * 100, '%')
    if return_chart:
        return money_history_df
    return money, wins/(wins+losses)

if sc.use_crypto:
    price_data = get_crypto_price_data(sc.crypto, sc.interval)
else:
    price_data = get_price_data(sc.ticker, sc.interval)

indicator_data = add_all_indicators(price_data)

def ichimoku_objective(trial):
    risk_reward = trial.suggest_float('risk_reward', 1, 3)
    df = ichimoku_strat(price_data, risk_reward)
    profit = simulate_buying_and_selling(df)[0]
    return profit

if sc.optimize_params:
    study = optuna.create_study(direction='maximize')
    study.optimize(ichimoku_objective, n_trials=sc.optimization_depth)
    df2 = ichimoku_strat(price_data, study.best_params['risk_reward'])
else:
    df1 = stoch_strat(price_data, 2)
    df2 = ichimoku_strat(price_data, 2)




#df2 = get_buy_and_sell_points_only_up_trend(indicator_data, sc.stoch_buy, sc.stoch_sell, sc.change_consec, sc.change_diff)

#df3 = get_buy_and_sell_points_all(indicator_data, sc.stoch_buy, sc.stoch_sell, sc.change_consec, sc.change_diff)

#df4 = get_buy_and_sell_points_vwap(indicator_data)

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
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['macd_signal'], mode='lines', name='signal'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['macd_hist'], mode='lines', name='histogram'))
    fig.update_layout(title='MACD', xaxis_title='Date', yaxis_title='MACD')
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
    fig.update_layout(title='ATR', xaxis_title='Date', yaxis_title='ATR')
    st.plotly_chart(fig)

def plot_vwap(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['c'], mode='lines', name='price'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['vwap'], mode='lines', name='vwap'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['sma'], mode='lines', name='moving average'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['sma50'], mode='lines', name='50 period moving average'))
    fig.update_layout(title='VWAP', xaxis_title='Date', yaxis_title='VWAP')
    st.plotly_chart(fig)

def plot_ichimoku(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['c'], mode='lines', name='price', line_color='black'))
    #fig.add_trace(go.Candlestick(x=[dr.unix_to_date(t) for t in indicator_data['t']], open=indicator_data['o'], high=indicator_data['h'], low=indicator_data['l'], close=indicator_data['c'], name='price'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['conversion_line'], mode='lines', name='conversion line', line_color='blue'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['base_line'], mode='lines', name='base line', line_color='orange'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t2']], y=indicator_data['leading_span_a'], mode='lines', name='leading span a', line_color='green'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t2']], y=indicator_data['leading_span_b'], mode='lines', name='leading span b', line_color='red'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['lagging_span'], mode='lines', name='lagging span', line_color='purple'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['sma'], mode='lines', name='sma', line_color='grey'))
    fig.update_layout(title='Ichimoku', xaxis_title='Date', yaxis_title='Ichimoku')
    st.plotly_chart(fig)

def plot_atr_trailing_stop(indicator_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['c'], mode='lines', name='price'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['trailing_stop'], mode='lines', name='atr trailing stop'))
    fig.update_layout(title='ATR Trailing Stop', xaxis_title='Date', yaxis_title='ATR Trailing Stop')
    st.plotly_chart(fig)

st.header('sotch strategy buy and sell points')
plot_buy_and_sell_points(df1)
st.header('ichimoku strategy buy and sell points')
plot_buy_and_sell_points(df2)
st.header('sotch strategy change in liquidity')
plot_investments(simulate_buying_and_selling(df1, True))
st.header('ichimoku strategy change in liquidity')
plot_investments(simulate_buying_and_selling(df2, True))
st.write('sotch strategy profitability: ', (simulate_buying_and_selling(df1)[0]/(sc.starting_money) * 100 - 100), '%')
st.write('ichimoku strategy profitability: ', (simulate_buying_and_selling(df2)[0]/(sc.starting_money) * 100 - 100), '%')
st.header('Real Change')
st.write('change in price: ' , (indicator_data['c'][-1] - indicator_data['c'][0]) / indicator_data['c'][0] * 100, '%')
plot_atr_trailing_stop(indicator_data)
plot_vwap(indicator_data)
plot_moving_average(indicator_data)
plot_stochastic_data(indicator_data)
plot_atr(indicator_data)
plot_ichimoku(indicator_data)
plot_bollinger_bands(indicator_data)
plot_volume(indicator_data)
plot_macd(indicator_data)