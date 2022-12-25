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
            ma.append(None)
        else:
            ma.append(sum(price_data['c'][i-bb_range:i])/bb_range)
    price_data['bsma'] = ma
    # add the standard deviation of the price data to the price data
    std = []
    for i in range(0, len(price_data['t'])):
        if i < bb_range:
            std.append(None)
        else:
            std.append(pd.Series(price_data['c'][i-bb_range:i]).std())
    price_data['std'] = std
    # add the upper bollinger band to the price data
    price_data['upper_bb'] = [price_data['bsma'][i] + 2*price_data['std'][i] for i in range(bb_range, len(price_data['t']))]
    # add the lower bollinger band to the price data
    price_data['lower_bb'] = [price_data['bsma'][i] - 2*price_data['std'][i] for i in range(bb_range, len(price_data['t']))]

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
    atr500 = []
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
        if i < 200:
            atr500.append(None)
        else:
            atr500.append(sum(price_data['tr2'][i-200:i+1])/200)

    price_data['atr'] = atr
    price_data['atr500'] = atr500
    price_data['trailing_stop'] = trailing_stop

# add simple moving average to the price data
def add_sma_data(price_data, ema_range):
    if sc.use_crypto:
        symbol = sc.crypto
    else:
        symbol = sc.ticker
    price_data['sma'] = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': ema_range})['ema']
    price_data['sma50'] = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': 50})['ema']
    price_data['sma500'] = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': 500})['ema']
    for i in range(0,ema_range):
        if(i < 50):
            price_data['sma50'][i] = None
        price_data['sma'][i] = None

def add_ichimoku_cloud_data(price_data):
    if sc.use_crypto:
        symbol = sc.crypto
    else:
        symbol = sc.ticker
    my_bar1 = st.progress(0.0)
    moving_average9_high = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': 9, 'seriestype': 'h'})['ema']
    my_bar1.progress(float(1/6))
    moving_average9_low = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': 9, 'seriestype': 'l'})['ema']
    my_bar1.progress(float(2/6))
    moving_average26_high = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': 26, 'seriestype': 'h'})['ema']
    my_bar1.progress(float(3/6))
    moving_average26_low = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': 26, 'seriestype': 'l'})['ema']
    my_bar1.progress(float(4/6))
    moving_average52_high = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': 52, 'seriestype': 'h'})['ema']
    my_bar1.progress(float(5/6))
    moving_average52_low = finnhub_client.technical_indicator(symbol, sc.interval, dr.from_date_unix, dr.to_date_unix, 'ema', {'timeperiod': 52, 'seriestype': 'l'})['ema']
    my_bar1.progress(1.0)
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
def add_vwap_data(price_data, percent_increment):
    vwap = []
    day_start_index = 0
    for i in range(0, len(price_data['t'])):
        #if dr.unix_to_date_time(price_data['t'][i]).day != dr.unix_to_date_time(price_data['t'][day_start_index]).day:
        #    day_start_index = i
        if i > 0 and not (1 - percent_increment < vwap[i-1]/price_data['c'][i] < 1 + percent_increment):
            day_start_index = i
        vwap.append(sum([(price_data['c'][j] + price_data['h'][j] + price_data['l'][j])/3*price_data['v'][j] for j in range(day_start_index, i+1)])/sum(price_data['v'][day_start_index:i+1]))
    price_data['vwap'] = vwap

def add_all_indicators(price_data):
    add_stochastic_data(price_data, sc.stoch_range)
    st.write('loaded stochastic data')
    #price_data = add_ease_of_movement_data(price_data)
    #price_data = add_emv_moving_average_data(price_data)
    #price_data = add_volume_data(price_data)
    add_macd_data(price_data)
    st.write('loaded macd data')
    add_bollinger_bands_data(price_data, sc.bb_range)
    st.write('loaded bollinger bands data')
    # price_data = add_adx_data(price_data, sc.adx_range)
    add_average_true_range_data(price_data, sc.atr_range)
    st.write('loaded atr data')
    add_sma_data(price_data, sc.sma_range)
    st.write('loaded sma data')
    add_vwap_data(price_data, .1)
    st.write('loaded vwap data')
    #add_ichimoku_cloud_data(price_data)
    #st.write('loaded ichimoku cloud data')
    return price_data

def macd_vwap_strat(price_data, reward_to_risk, atr_multiplier):
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])
    in_trade = False
    short = False
    buy = False
    just_got_here = False
    my_bar = st.progress(0.0)
    price_sold = 0
    price_closed = 0
    up = False
    for i in range(201, len(price_data['t'])):
        my_bar.progress(float(i - 200)/(len(price_data['t']) - 200))
        if not in_trade:
            if price_data['macd'][i] < 0 and price_data['c'][i] < price_data['vwap'][i] and price_data['c'][i-1] > price_data['vwap'][i-1] and price_data['sma50'][i] > price_data['sma'][i]:
                buy = True
                short = False
                in_trade = True
                df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'buy']
                price = price_data['c'][i]
                stop_loss_price = price_data['c'][i] - price_data['atr'][i] * atr_multiplier
                take_profit_price = price_data['c'][i] * ((1 - stop_loss_price/price_data['c'][i]) * reward_to_risk + 1)
                just_got_here = True
            elif price_data['macd'][i] > 0 and price_data['c'][i] > price_data['vwap'][i] and price_data['c'][i-1] < price_data['vwap'][i-1] and price_data['sma50'][i] < price_data['sma'][i]:
                buy = False
                short = True
                in_trade = True
                df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'short_open']
                price = price_data['c'][i]
                stop_loss_price = price_data['c'][i] + price_data['atr'][i] * atr_multiplier
                take_profit_price = price_data['c'][i] * (1 - (stop_loss_price/price_data['c'][i] - 1) * reward_to_risk)
                just_got_here = True
        else:
            if not just_got_here:
                if buy and price_data['c'][i] < stop_loss_price and price_data['macd'][i] > 0:
                    df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_sell']
                    in_trade = False
                    buy = False
                    price_sold = price_data['c'][i]
                elif buy and price_data['c'][i] > take_profit_price and price_data['macd'][i] > 0:
                    df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_sell']
                    in_trade = False
                    buy = False
                    price_sold = price_data['c'][i]
                elif buy and price_data['c'][i] < take_profit_price and price_data['c'][i-1] > take_profit_price:
                    df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_sell']
                    in_trade = False
                    buy = False
                    price_sold = price_data['c'][i]
                elif short and price_data['c'][i] > stop_loss_price and price_data['macd'][i] < 0:
                    df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_short_close']
                    in_trade = False
                    short = False
                    price_closed = price_data['c'][i]
                elif short and price_data['c'][i] < take_profit_price and price_data['macd'][i] < 0:
                    df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_short_close']
                    in_trade = False
                    short = False
                    price_closed = price_data['c'][i]
                elif short and price_data['c'][i] > take_profit_price and price_data['c'][i-1] < take_profit_price:
                    df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_short_close']
                    in_trade = False
                    short = False
                    price_closed = price_data['c'][i]
            just_got_here = False
    # make the last trade a hold
    df.loc[len(df)] = [dr.unix_to_date(price_data['t'][len(price_data['t']) - 1]), price_data['c'][len(price_data['c']) - 1], 'hold']
    return df


def ichimoku_strat(price_data, reward_to_risk, atr_multiplier, atr_percent):
    df = pd.DataFrame(columns=['time', 'price', 'buy/sell/hold'])
    in_trade = False
    short = False
    buy = False
    just_got_here = False
    my_bar = st.progress(0.0)
    price_sold = 0
    price_closed = 0
    up = False
    for i in range(201, len(price_data['t'])):
        my_bar.progress(float(i - 200)/(len(price_data['t']) - 200))
        if not in_trade:
            if price_data['sma50'][i] > price_data['sma'][i] and price_data['sma50'][i-1] < price_data['sma'][i-1]:
                price_sold = 0
                price_closed = 0
            if price_data['sma50'][i] < price_data['sma'][i] and price_data['sma50'][i-1] > price_data['sma'][i-1]:
                price_closed = 0
                price_sold = 0
            up = price_data['sma50'][i] > price_data['sma'][i]
            if not up and price_data['macd'][i] > 0 and price_data['macd'][i] < price_data['macd_signal'][i] and \
                price_data['macd'][i-1] > price_data['macd_signal'][i-1] and ((price_data['c'][i] > price_closed or price_closed == 0) or price_data['atr'][i]/price_data['c'][i] > atr_percent):
                short = True
                buy = False
                in_trade = True
                df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'short_open']
                price = price_data['c'][i]
                stop_loss_price = price_data['c'][i] + price_data['atr'][i] * atr_multiplier
                take_profit_price = price_data['c'][i] * (1-(stop_loss_price/price_data['c'][i]-1) * reward_to_risk)
                just_got_here = True
            elif up and price_data['macd'][i] < 0 and price_data['macd'][i] > price_data['macd_signal'][i] and \
                price_data['macd'][i-1] < price_data['macd_signal'][i-1] and ((price_data['c'][i] < price_sold or price_sold == 0) or price_data['atr'][i]/price_data['c'][i] > atr_percent):
                buy = True
                short = False
                in_trade = True
                df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'buy']
                price = price_data['c'][i]
                stop_loss_price = price_data['c'][i] - price_data['atr'][i] * atr_multiplier
                take_profit_price = price_data['c'][i] * ((1 - stop_loss_price/price_data['c'][i]) * reward_to_risk + 1)
                just_got_here = True
        else:
            if not just_got_here:
                if buy and price_data['c'][i] < stop_loss_price and price_data['macd'][i] > 0:
                    df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_sell']
                    in_trade = False
                    buy = False
                    price_sold = price_data['c'][i]
                elif buy and price_data['c'][i] > take_profit_price and price_data['macd'][i] > 0:
                    df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_sell']
                    in_trade = False
                    buy = False
                    price_sold = price_data['c'][i]
                elif buy and price_data['c'][i] < take_profit_price and price_data['c'][i-1] > take_profit_price:
                    df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_sell']
                    in_trade = False
                    buy = False
                    price_sold = price_data['c'][i]
                elif short and price_data['c'][i] > stop_loss_price and price_data['macd'][i] < 0:
                    df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_short_close']
                    in_trade = False
                    short = False
                    price_closed = price_data['c'][i]
                elif short and price_data['c'][i] < take_profit_price and price_data['macd'][i] < 0:
                    df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_short_close']
                    in_trade = False
                    short = False
                    price_closed = price_data['c'][i]
                elif short and price_data['c'][i] > take_profit_price and price_data['c'][i-1] < take_profit_price:
                    df.loc[len(df)] = [dr.unix_to_date(price_data['t'][i]), price_data['c'][i], 'big_short_close']
                    in_trade = False
                    short = False
                    price_closed = price_data['c'][i]
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
        elif df['buy/sell/hold'][i] == 'big_sell':
            if num_stocks > 0:
                money += df['price'][i]*num_stocks*(1-sc.transaction_fee)
                num_stocks = 0
            real_money = money
            if prev_money < money:
                wins += 1
            else:
                losses += 1
        elif df['buy/sell/hold'][i] == 'short_open':
            prev_money = money
            money += sc.investment * (1-sc.transaction_fee)
            num_short_stocks_owed += sc.investment/df['price'][i]
        elif df['buy/sell/hold'][i] == 'big_short_close':
            if num_short_stocks_owed > 0:
                money -= df['price'][i]*num_short_stocks_owed*(1+sc.transaction_fee)
                num_short_stocks_owed = 0
            real_money = money
            if prev_money < real_money:
                wins += 1
            else:
                losses += 1
        if return_chart and df['buy/sell/hold'][i] != 'hold':
            money_history_df.loc[i] = [df['time'][i], real_money, stop_loss, short_stop_loss]
        short_stop_loss = False
        stop_loss = False            
    # at the end of the simulation, sell all stocks, and pay off all short stocks
    money += num_stocks * df['price'][len(df)-1]
    money -= num_short_stocks_owed * df['price'][len(df)-1]
    if wins + losses > 0:
        win_rate = wins/(wins+losses)
    else:
        win_rate = 0
    if return_chart:
        money_history_df.loc[len(money_history_df)] = [df['time'][len(df)-1], money, stop_loss, short_stop_loss]
        st.write('win rate: ', win_rate * 100, '%')
        st.write('total trades: ', wins + losses)
    if return_chart:
        return money_history_df
    return money, win_rate

if sc.use_crypto:
    price_data = get_crypto_price_data(sc.crypto, sc.interval)
else:
    price_data = get_price_data(sc.ticker, sc.interval)

indicator_data = add_all_indicators(price_data)
st.write('loaded all indicators')

def ichimoku_objective(trial):
    risk_reward = trial.suggest_float('risk_reward', 1, 3)
    atr_multiplier = trial.suggest_float('atr_multiplier', 1, 7)
    atr_percent = trial.suggest_float('atr_percent', 0, 0.5)
    df = ichimoku_strat(price_data, risk_reward, atr_multiplier, atr_percent)
    profit = simulate_buying_and_selling(df)[0]
    return profit

def macd_vwap_objective(trial):
    risk_reward = trial.suggest_float('risk_reward', 1, 3)
    atr_multiplier = trial.suggest_float('atr_multiplier', 1, 7)
    vwap_percent = trial.suggest_float('vwap_percent', 0, 0.5)
    add_vwap_data(price_data, vwap_percent)
    df = macd_vwap_strat(price_data, risk_reward, atr_multiplier)
    profit = simulate_buying_and_selling(df)[0]
    return profit

if sc.optimize_params:
    study = optuna.create_study(direction='maximize')
    study.optimize(macd_vwap_objective, n_trials=sc.optimization_depth)
    add_vwap_data(price_data, study.best_params['vwap_percent'])
    df1 = macd_vwap_strat(price_data, study.best_params['risk_reward'], study.best_params['atr_multiplier'])
else:
    df1 = macd_vwap_strat(price_data, 1.5, 3)

st.write('loaded all strategies')

# plot the prices over time, highlighting the buy and sell points/short opens and closes on streamlit
def plot_buy_and_sell_points(price_data, df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in price_data['t']], y=price_data['c'], mode='lines', name='Price'))
    # if it is a buy, make the marker color green, if it is a big sell, make the marker color red, if it is a short open, make the marker color blue and if it is a big short close, make the marker color purple
    fig.add_trace(go.Scatter(x=[t for t in df['time']], y=df['price'], mode='markers', name='Buy/Sell/Short', marker_color=[('green' if x == 'buy' else ('red' if x == 'big_sell' else ('blue' if x == 'short_open' else ('purple' if x == 'big_short_close' else 'black')))) for x in df['buy/sell/hold']]))
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
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['sma'], mode='lines', name='moving average 200'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['sma50'], mode='lines', name='moving average 50'))
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['sma500'], mode='lines', name='moving average 500'))
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
    fig.add_trace(go.Scatter(x=[dr.unix_to_date(t) for t in indicator_data['t']], y=indicator_data['atr500'], mode='lines', name='atr moving average'))
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

st.header('ichimoku strategy buy and sell points')
plot_buy_and_sell_points(price_data, df1)
st.header('ichimoku strategy change in liquidity')
plot_investments(simulate_buying_and_selling(df1, True))
st.write('ichimoku strategy profitability: ', (simulate_buying_and_selling(df1)[0]/(sc.starting_money) * 100 - 100), '%')
st.header('Real Change')
st.write('change in price: ' , (indicator_data['c'][-1] - indicator_data['c'][0]) / indicator_data['c'][0] * 100, '%')
plot_vwap(indicator_data)
plot_atr_trailing_stop(indicator_data)
plot_moving_average(indicator_data)
plot_stochastic_data(indicator_data)
plot_atr(indicator_data)
plot_bollinger_bands(indicator_data)
plot_volume(indicator_data)
plot_macd(indicator_data)