import Configuration.Config as cfg
import os
import finnhub as fh
import pandas as pd
import Configuration.DateRange as dr
from DataTypes import State, LimitOrder, MarketOrder, Trade
import logging
from typing import Union, Dict, Tuple
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ccxt
import time
import sys
from HyperOpt.OptimizeFunctions import byNumTrades
from Graphs import graphs

# Get OHLCV data
def getOHLCV(ticker: str) -> pd.DataFrame:
    # if there isnt a finnhub client, create one. this means we are calling this function outside of the backtester
    if 'finnhub_client' not in globals():
        print('Creating finnhub client because it doesnt exist')
        finnhub_client = fh.Client(api_key=cfg.API_KEY)
    return pd.DataFrame(finnhub_client.stock_candles(ticker, cfg.INTERVAL, dr.FROM_DATE_UNIX, dr.TO_DATE_UNIX))

def alignDataframes(dataframes: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    # Find the set of timestamps that are shared across all dataframes
    common_timestamps = sorted(set.intersection(*[set(df['t']) for df in dataframes.values()]))

    # Filter out any rows in each dataframe that don't have a timestamp in the common set
    aligned_dataframes = {}
    for key, df in dataframes.items():
        aligned_df = df[df['t'].isin(common_timestamps)].reset_index(drop=True)
        aligned_dataframes[key] = aligned_df

    return aligned_dataframes

# get the results of the backtest
# NOTE: the strategy must be in the strategies folder, and strategy_name excludes the .py extension
def getResults(strategy_name: str, log_messages: bool = False, price_data: Dict[str, pd.DataFrame] = cfg.PRICE_DATA) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
    if log_messages:
        if not os.path.exists('Logs/Backtest'):
            os.makedirs('Logs/Backtest')
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(logging.FileHandler('Logs/Backtest/' + strategy_name + 'Backtest.log', mode='w'))
        logger.info('Starting backtest for ' + strategy_name + ' on ' + str(dr.unix_to_date(dr.FROM_DATE_UNIX)) + ' to ' + str(dr.unix_to_date(dr.TO_DATE_UNIX)))
    
    # get the OHLCV data
    dataframes = price_data

    # align the timestamps and remove any timestamps that are not shared across all dataframes
    dataframes = alignDataframes(dataframes)

    # import the strategy
    strategy = __import__('Strategies.' + strategy_name, fromlist=['strategy'])

    # initialize the data

    for symbol in dataframes:
        dataframes[symbol]['orders'] = [[] for i in range(len(dataframes[symbol]))]
        dataframes[symbol]['trades'] = [[] for i in range(len(dataframes[symbol]))]
        dataframes[symbol]['position'] = [0 for i in range(len(dataframes[symbol]))]
        dataframes[symbol]['pnl'] = [0 for i in range(len(dataframes[symbol]))]

    strat_data = pd.DataFrame()

    for i in range(len(dataframes[cfg.SYMBOLS_TO_BE_TRADED[0]])):
        if i > 1:
            # update the positions and PnL
            for symbol in dataframes:
                # update the position
                dataframes[symbol].loc[i, 'position'] = dataframes[symbol].loc[i-1, 'position']

                # update the PnL
                dataframes[symbol].loc[i, 'pnl'] = dataframes[symbol].loc[i-1, 'pnl'] + dataframes[symbol].loc[i, 'position'] * (dataframes[symbol].loc[i, 'c'] - dataframes[symbol].loc[i-1, 'c'])
            
        states = {symbol: State(symbol, dataframes[symbol].loc[i, 't'], dataframes[symbol].loc[i, 'position'], dataframes[symbol].loc[i, 'o'], dataframes[symbol].loc[i, 'h'], dataframes[symbol].loc[i, 'l'], dataframes[symbol].loc[i, 'c'], dataframes[symbol].loc[i, 'v']) for symbol in dataframes}

        # get the orders
        orders, strat_data = strategy.strategy(states, strat_data, cfg.STRATEGY_HYPERPARAMETERS)

        short_limits = {symbol: states[symbol].position for symbol in states}
        long_limits = {symbol: states[symbol].position for symbol in states}

        # execute the orders
        for order in orders:
            symbol = order.security
            if isinstance(order, MarketOrder):
                # execute the market order
                
                # check to make sure the order does not exceed the position limit
                if cfg.POSITION_LIMITS[symbol] > 0 and ((order.quantity < 0 and short_limits[symbol] + order.quantity < -cfg.POSITION_LIMITS[symbol]) or \
                    (order.quantity > 0 and long_limits[symbol] + order.quantity > cfg.POSITION_LIMITS[symbol])):
                    if log_messages:
                        logger.warning("Order exceeds position limit: " + str(order))
                else:
                    # execute the order
                    if order.quantity < 0:
                        short_limits[symbol] += order.quantity
                    else:
                        long_limits[symbol] += order.quantity

                    dataframes[symbol]['orders'][i].append(order)
                    dataframes[symbol]['trades'][i].append(Trade(symbol, order.timestamp, order.quantity, dataframes[symbol]['c'][i]))                    

            elif isinstance(order, LimitOrder):
                # execute the limit order
                if cfg.POSITION_LIMITS[symbol] > 0 and ((order.quantity < 0 and states[symbol].position + order.quantity < -cfg.POSITION_LIMITS[symbol]) or \
                    (order.quantity > 0 and states[symbol].position + order.quantity > cfg.POSITION_LIMITS[symbol])):
                    if log_messages:
                        logger.warning("Order exceeds position limit: " + str(order))
                else:
                    if order.quantity < 0:
                        short_limits[symbol] += order.quantity
                    else:
                        long_limits[symbol] += order.quantity

                    # check if the limit order is filled, if it is filled, then this is a market order with taker fees
                    if (order.quantity < 0 and dataframes[symbol]['c'][i] <= order.price) or \
                        (order.quantity > 0 and dataframes[symbol]['c'][i] >= order.price):
                        dataframes[symbol]['orders'][i].append(order)
                        dataframes[symbol]['trades'][i].append(Trade(symbol, order.timestamp, order.quantity, dataframes[symbol]['c'][i]))
                    else:
                        # if the limit order is not filled, then it is a limit order with maker fees
                        dataframes[symbol]['orders'][i].append(order)
                        dataframes[symbol]['trades'][i].append(Trade(symbol, order.timestamp, order.quantity, order.price, is_taker=False, filled=0))
            else:
                raise Exception("Invalid order type: " + str(order))
        
        # update the position
        for symbol in dataframes:
            for trade in dataframes[symbol]['trades'][i]:
                if trade.is_taker:
                    if log_messages:
                        logger.info("Market order filled (or immediately filled limit order): " + str(trade))
                    dataframes[symbol].loc[i, 'position'] += trade.quantity * (1 - cfg.TAKER_FEE)
            for trade_list in dataframes[symbol]['trades'][:i]:
                for trade in trade_list:
                    if not trade.is_taker and abs(trade.filled) < abs(trade.quantity) and ((trade.quantity < 0 and dataframes[symbol]['c'][i] >= trade.price) or (trade.quantity > 0 and dataframes[symbol]['c'][i] <= trade.price)):
                        if cfg.POSITION_LIMITS[symbol] > 0:
                            if not ((trade.quantity < 0 and dataframes[symbol]['position'][i] + (trade.quantity - trade.filled) * (1 - cfg.MAKER_FEE) < -cfg.POSITION_LIMITS[symbol]) or \
                            (trade.quantity > 0 and dataframes[symbol]['position'][i] + (trade.quantity - trade.filled) * (1 - cfg.MAKER_FEE) > cfg.POSITION_LIMITS[symbol])):
                                trade.filled = trade.quantity
                                dataframes[symbol].loc[i, 'position'] += (trade.quantity - trade.filled) * (1 - cfg.MAKER_FEE)
                                if log_messages:
                                    logger.info("Limit order filled: " + str(trade))
                            elif trade.quantity < 0 and dataframes[symbol]['position'][i] + (trade.quantity - trade.filled) * (1 - cfg.MAKER_FEE) < -cfg.POSITION_LIMITS[symbol] and dataframes[symbol]['position'][i] > -cfg.POSITION_LIMITS[symbol]:
                                trade.filled = -cfg.POSITION_LIMITS[symbol] - dataframes[symbol]['position'][i]
                                dataframes[symbol].loc[i, 'position'] = -cfg.POSITION_LIMITS[symbol]
                                if log_messages:
                                    logger.warning("Limit order partially filled: " + str(trade))
                            elif trade.quantity > 0 and dataframes[symbol]['position'][i] + (trade.quantity - trade.filled) * (1 - cfg.MAKER_FEE) > cfg.POSITION_LIMITS[symbol] and dataframes[symbol]['position'][i] < cfg.POSITION_LIMITS[symbol]:
                                trade.filled = cfg.POSITION_LIMITS[symbol] - dataframes[symbol]['position'][i]
                                dataframes[symbol].loc[i, 'position'] = cfg.POSITION_LIMITS[symbol]
                                if log_messages:
                                    logger.warning("Limit order partially filled: " + str(trade))
                            else:
                                if log_messages:
                                    logger.warning("Limit order not filled, exceeds position limit: " + str(trade))
                        elif cfg.POSITION_LIMITS[symbol] <= 0:
                            trade.filled = trade.quantity
                            dataframes[symbol].loc[i, 'position'] += trade.quantity * (1 - cfg.MAKER_FEE)
                            if log_messages:
                                logger.info("Limit order filled: " + str(trade))
    return dataframes, strat_data

# save the results of the backtest
def saveResults(dfs: Dict[str, pd.DataFrame], strategy_name: str):
    if not os.path.exists('BacktestResults'):
        os.mkdir('BacktestResults')
    for symbol in dfs:
        if symbol in cfg.SYMBOLS_TO_BE_TRADED:
            if '/' in symbol:
                symbol_in_file = symbol.replace('/', '_')
            else:
                symbol_in_file = symbol
            dfs[symbol].to_csv('BacktestResults/' + strategy_name + '_' + symbol_in_file + '.csv')

# plot the results of the backtest
def plotResults(df: pd.DataFrame, symbol: str):
    if ':' in symbol:
        symbol = symbol.split(':')[1]
    st.header('Results for ' + symbol)
    fig = go.Figure()
    if '/' in symbol:
        fig.add_trace(go.Scatter(x=[dr.unix_ms_to_date_time(time) for time in df['t']], y=df['position'], name='Position', line=dict(color='green')))
        fig.add_trace(go.Scatter(x=[dr.unix_ms_to_date_time(time) for time in df['t']], y=df['c'], name='Closing Price', line=dict(color='red'), yaxis='y2'))
        fig.add_trace(go.Scatter(x=[dr.unix_ms_to_date_time(time) for time in df['t']], y=df['pnl'], name='PNL', line=dict(color='blue'), yaxis='y3'))
    else:
        fig.add_trace(go.Scatter(x=[dr.unix_to_date_time(time) for time in df['t']], y=df['position'], name='Position', line=dict(color='green')))
        fig.add_trace(go.Scatter(x=[dr.unix_to_date_time(time) for time in df['t']], y=df['c'], name='Closing Price', line=dict(color='red'), yaxis='y2'))
        fig.add_trace(go.Scatter(x=[dr.unix_to_date_time(time) for time in df['t']], y=df['pnl'], name='PNL', line=dict(color='blue'), yaxis='y3'))
    fig.update_layout(
        title='Position, Close, and PNL for ' + symbol, 
        xaxis_title='Timestamp', 
        yaxis=dict(title='Position', titlefont=dict(color='green'), tickfont=dict(color='green'), side='left'), 
        yaxis2=dict(title='Close', titlefont=dict(color='red'), tickfont=dict(color='red'), overlaying='y', side='right', anchor='x'), 
        yaxis3=dict(title='PNL', titlefont=dict(color='blue'), tickfont=dict(color='blue'), overlaying='y', side='right', anchor='free', autoshift=True), 
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    st.plotly_chart(fig)

def getIntervalMS() -> int:
    num_part = cfg.CRYPTO_INTERVAL[:-1]
    assert(num_part.isdigit())
    letter_part = cfg.CRYPTO_INTERVAL[-1]

    if letter_part == 'm':
        return int(num_part) * 60000
    elif letter_part == 'h':
        return int(num_part) * 3600000
    elif letter_part == 'd':
        return int(num_part) * 86400000
    elif letter_part == 'w':
        return int(num_part) * 604800000
    else:
        raise ValueError(f"Invalid interval '{cfg.CRYPTO_INTERVAL}'")

def getIntervalSeconds() -> int:
    return int(getIntervalMS() / 1000)

def roundToIntervalMS(timestamp: int) -> int:
    # round up or down to the nearest interval
    interval_ms = getIntervalMS()
    if timestamp % interval_ms < interval_ms / 2:
        return timestamp - (timestamp % interval_ms)
    else:
        return timestamp + (interval_ms - (timestamp % interval_ms))

def roundToIntervalSeconds(timestamp: int) -> int:
    return int(roundToIntervalMS(timestamp * 1000) / 1000)

def getPandasFrequency() -> str:
    
    timeframe = cfg.CRYPTO_INTERVAL

    num_part = int(timeframe[:-1])
    letter_part = timeframe[-1]
    
    if letter_part == 'm':
        freq_letter = 'T'
    elif letter_part == 'h':
        freq_letter = 'H'
    elif letter_part == 'd':
        freq_letter = 'D'
    elif letter_part == 'w':
        freq_letter = 'W'
    else:
        raise ValueError(f"Invalid timeframe '{timeframe}'")
    
    return f'{num_part}{freq_letter}'

def downloadCryptoData(exchange: ccxt.Exchange, pair: str) -> pd.DataFrame:
    df = pd.DataFrame(columns=['t', 'o', 'h', 'l', 'c', 'v'])
    
    if os.path.exists('BacktestData/' + pair.replace('/', '_') + '.csv'):
        df = pd.read_csv('BacktestData/' + pair.replace('/', '_') + '.csv')

    missing_data = set()
    from_date_ms = roundToIntervalMS(dr.FROM_DATE_MS)
    to_date_ms = dr.TO_DATE_MS

    if not df.empty:
        # extract a set of all the dates that are missing from the data
        date_range = pd.date_range(start=dr.unix_ms_to_date_time(roundToIntervalMS(dr.FROM_DATE_MS)), end=dr.unix_ms_to_date_time(dr.TO_DATE_MS), freq=getPandasFrequency())

        date_range = set([dr.date_to_unix_ms(date) for date in date_range])

        missing_data = date_range - set(df['t'])

        if len(missing_data) == 0:
            print('No missing data')
            return df

        from_date_ms = min(missing_data)
        to_date_ms = max(missing_data)

    exchange.load_markets()

    if exchange.has['fetchOHLCV']:
        time_range = to_date_ms - from_date_ms
        interval_ms = getIntervalMS()
        print('Fetching data in chunks...')
        new_from_date_ms = roundToIntervalMS(from_date_ms)
        while new_from_date_ms < to_date_ms:
            print('progress: ' + str(round((new_from_date_ms - from_date_ms) / time_range * 100, 2)) + '%')
            time.sleep(exchange.rateLimit / 1000)
            try:
                ohlcv = pd.DataFrame(exchange.fetch_ohlcv(pair, cfg.CRYPTO_INTERVAL, since=new_from_date_ms), columns=['t', 'o', 'h', 'l', 'c', 'v'])
            except:
                print('rate limit probably exceeded, waiting 3 seconds')
                time.sleep(3)
                ohlcv = pd.DataFrame(exchange.fetch_ohlcv(pair, cfg.CRYPTO_INTERVAL, since=new_from_date_ms), columns=['t', 'o', 'h', 'l', 'c', 'v'])
            df = pd.concat([df, ohlcv], ignore_index=True)
            new_from_date_ms = df.loc[len(df) - 1, 't'] + interval_ms
        # remove duplicates
        df = df.drop_duplicates(subset=['t'])
        # sort by time
        df = df.sort_values(by=['t'])
    else:
        raise Exception('fetchOHLCV not supported by exchange')

    return df

def getDataForSymbol(symbol: str) -> pd.DataFrame:
    df = pd.DataFrame(columns=['t', 'o', 'h', 'l', 'c', 'v'])
    if '/' in symbol:
        # make sure the data is downloaded
        # if we are calling this from the backtester, we want to see if BacktestData exists, otherwise we want to see if ../BacktestData exists
        if str(os.getcwd().split(os.sep)[-1]) != 'HyperOpt':
            if not os.path.exists('BacktestData/' + symbol.replace('/', '_') + '.csv'):
                print('Data not downloaded for ' + symbol)
                exit(1)
            # load the data
            df = pd.read_csv('BacktestData/' + symbol.replace('/', '_') + '.csv')
            # extract the data for the time period we want
            df = df[(df['t'] >= roundToIntervalMS(dr.FROM_DATE_MS)) & (df['t'] <= dr.TO_DATE_MS)]
            # remove data that is not in the interval
            df = df[df['t'] % getIntervalMS() == 0]
            # sort by time
            df = df.sort_values(by=['t'])
            # reset the index
            df = df.reset_index(drop=True)
        else:
            if not os.path.exists('../BacktestData/' + symbol.replace('/', '_') + '.csv'):
                print('Data not downloaded for ' + symbol)
                exit(1)
            # load the data
            df = pd.read_csv('../BacktestData/' + symbol.replace('/', '_') + '.csv')
            # extract the data for the time period we want
            df = df[(df['t'] >= roundToIntervalMS(dr.FROM_DATE_MS)) & (df['t'] <= dr.TO_DATE_MS)]
            # remove data that is not in the interval
            df = df[df['t'] % getIntervalMS() == 0]
            # sort by time
            df = df.sort_values(by=['t'])
            # reset the index
            df = df.reset_index(drop=True)
    else:
        df = getOHLCV(symbol)
    return df

# run the backtest
if __name__ == "__main__":

    # there will be 1 argument, [ download | test ]
    if len(sys.argv) != 2 or sys.argv[1] not in ['download', 'test']:
        print('Usage: python3 Backtester.py [ download | test ]')
        exit(1)

    # Set up the crypto API
    exchange = ccxt.kucoin({ 'enableRateLimit': True })
    # Set up the stock API
    finnhub_client = fh.Client(api_key=cfg.API_KEY)

    # Set the timeout to 2 minutes to stop from timeout errors with lots of data
    finnhub_client.DEFAULT_TIMEOUT = 120

    if sys.argv[1] == 'download':
        for symbol in cfg.SYMBOLS_TO_BE_TRADED:
            if '/' in symbol:
                df = downloadCryptoData(exchange, symbol)
                if not os.path.exists('BacktestData'):
                    os.mkdir('BacktestData')
                df.to_csv('BacktestData/' + symbol.replace('/', '_') + '.csv', index=False)
    else:
        dfs = {}
        for symbol in cfg.SYMBOLS_TO_BE_TRADED:
            dfs[symbol] = getDataForSymbol(symbol)
        # run the backtest
        st.title('Backtest Results for ' + cfg.STRATEGY_NAME)
        results = getResults(cfg.STRATEGY_NAME, False, dfs)
        result_dfs = results[0]
        strat_data = results[1]
        saveResults(result_dfs, cfg.STRATEGY_NAME)
        for symbol in result_dfs:
            if symbol in cfg.SYMBOLS_TO_BE_TRADED:
                plotResults(result_dfs[symbol], symbol)
                st.write('number of trades: ' + str(byNumTrades(result_dfs[symbol])))
        st.write(strat_data)
        for graph_fn in graphs:
            # each graph function returns a plotly figure, so we can just pass it to streamlit
            st.plotly_chart(graph_fn(strat_data))
