import Configuration.Config as cfg
import os
import finnhub as fh
import pandas as pd
import Configuration.DateRange as dr
from DataTypes import State, LimitOrder, MarketOrder, Trade
import matplotlib.pyplot as plt
import logging
from typing import Union, Dict

# Set up the API
finnhub_client = fh.Client(api_key=cfg.API_KEY)

# Set the timeout to 2 minutes to stop from timeout errors with lots of data
finnhub_client.DEFAULT_TIMEOUT = 120

# Get OHLCV data
def getOHLCV() -> Dict[str, pd.DataFrame]:
    if cfg.USE_CRYPTO:
        return {pair: pd.DataFrame(finnhub_client.crypto_candles(pair, cfg.INTERVAL, dr.FROM_DATE_UNIX, dr.TO_DATE_UNIX)) for pair in cfg.CRYPTO_PAIRS}
    else:
        return {ticker: pd.DataFrame(finnhub_client.stock_candles(ticker, cfg.INTERVAL, dr.FROM_DATE_UNIX, dr.TO_DATE_UNIX)) for ticker in cfg.STOCK_TICKERS}

# get the results of the backtest
# NOTE: the strategy must be in the strategies folder, and strategy_name excludes the .py extension
def getResults(strategy_name: str, log_messages: bool = False, price_data: Union[Dict[str, pd.DataFrame], None] = cfg.PRICE_DATA) -> pd.DataFrame:
    if log_messages:
        if not os.path.exists('Logs/Backtest'):
            os.makedirs('Logs/Backtest')
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(logging.FileHandler('Logs/Backtest/' + strategy_name + 'Backtest.log', mode='w'))
        logger.info('Starting backtest for ' + strategy_name + ' on ' + str(dr.unix_to_date(dr.FROM_DATE_UNIX)) + ' to ' + str(dr.unix_to_date(dr.TO_DATE_UNIX)))
    
    # get the OHLCV data
    if price_data is None:
        if log_messages:
            logger.info('Getting OHLCV data from Finnhub')
        dataframes = getOHLCV()
    else:
        if log_messages:
            logger.info('Using OHLCV data from passed DataFrame')
        dataframes = price_data

    # import the strategy
    strategy = __import__('Strategies.' + strategy_name, fromlist=['strategy'])

    # initialize the data

    for symbol in dataframes:
        dataframes[symbol]['orders'] = [[] for i in range(len(dataframes[symbol]))]
        dataframes[symbol]['trades'] = [[] for i in range(len(dataframes[symbol]))]
        dataframes[symbol]['position'] = [0 for i in range(len(dataframes[symbol]))]
        dataframes[symbol]['pnl'] = [0 for i in range(len(dataframes[symbol]))]

    strat_data = pd.DataFrame()

    for symbol in dataframes:
        if symbol in cfg.SYMBOLS_TO_BE_TRADED:
            if log_messages:
                logger.info('Starting backtest for ' + symbol)

            for i in range(len(dataframes[symbol])):

                if i > 1:
                    # update the position
                    dataframes[symbol].loc[i, 'position'] = dataframes[symbol].loc[i-1, 'position']

                    # update the PnL
                    dataframes[symbol].loc[i, 'pnl'] = dataframes[symbol].loc[i-1, 'pnl'] + dataframes[symbol].loc[i, 'position'] * (dataframes[symbol].loc[i, 'c'] - dataframes[symbol].loc[i-1, 'c'])

                states = {symbol: State(symbol, dataframes[symbol].loc[i, 't'], dataframes[symbol].loc[i, 'position'], dataframes[symbol].loc[i, 'o'], dataframes[symbol].loc[i, 'h'], dataframes[symbol].loc[i, 'l'], dataframes[symbol].loc[i, 'c'], dataframes[symbol].loc[i, 'v']) for symbol in dataframes}

                # get the orders
                orders, strat_data = strategy.strategy(states, strat_data, cfg.STRATEGY_HYPERPARAMETERS)

                short_limit = states[symbol].position
                long_limit = states[symbol].position

                # execute the orders
                for order in orders:
                    if isinstance(order, MarketOrder):
                        # execute the market order
                        
                        # check to make sure the order does not exceed the position limit
                        if cfg.POSITION_LIMITS[symbol] > 0 and ((order.quantity < 0 and short_limit + order.quantity < -cfg.POSITION_LIMITS[symbol]) or \
                            (order.quantity > 0 and long_limit + order.quantity > cfg.POSITION_LIMITS[symbol])):
                            if log_messages:
                                logger.warning("Order exceeds position limit: " + str(order))
                        else:
                            # execute the order
                            if order.quantity < 0:
                                short_limit += order.quantity
                            else:
                                long_limit += order.quantity

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
                                short_limit += order.quantity
                            else:
                                long_limit += order.quantity

                            # check if the limit order is filled, if it is filled, then this is a market order with taker fees
                            if (order.quantity < 0 and dataframes[symbol]['c'][i] <= order.price) or \
                                (order.quantity > 0 and dataframes[symbol]['c'][i] >= order.price):
                                dataframes[symbol]['orders'][i].append(order)
                                dataframes[symbol]['trades'][i].append(Trade(symbol, order.timestamp, order.quantity, dataframes[symbol]['c'][i]))
                            else:
                                # if the limit order is not filled, then it is a limit order with maker fees
                                dataframes[symbol]['orders'][i].append(order)
                                dataframes[symbol]['trades'][i].append(Trade(symbol, order.timestamp, order.quantity, order.price, is_taker=False))
                    else:
                        raise Exception("Invalid order type: " + str(order))
                
                # update the position
                for trade in dataframes[symbol]['trades'][i]:
                    if trade.is_taker:
                        if log_messages:
                            logger.info("Market order filled (or immediately filled limit order): " + str(trade))
                        dataframes[symbol].loc[i, 'position'] += trade.quantity * (1 - cfg.TAKER_FEE)
                for trade_list in dataframes[symbol]['trades'][:i]:
                    for trade in trade_list:
                        if not trade.is_taker and ((trade.quantity < 0 and dataframes[symbol]['c'][i] >= trade.price) or (trade.quantity > 0 and dataframes[symbol]['c'][i] <= trade.price)):
                            if cfg.POSITION_LIMITS[symbol] > 0 and not ((trade.quantity < 0 and dataframes[symbol]['position'][i] + trade.quantity * (1 - cfg.MAKER_FEE) < -cfg.POSITION_LIMITS[symbol]) or \
                            (trade.quantity > 0 and dataframes[symbol]['position'][i] + trade.quantity * (1 - cfg.MAKER_FEE) > cfg.POSITION_LIMITS[symbol])):
                                if log_messages:
                                    logger.info("Limit order filled: " + str(trade))
                                dataframes[symbol].loc[i, 'position'] += trade.quantity * (1 - cfg.MAKER_FEE)
                            elif trade.quantity < 0 and dataframes[symbol]['position'][i] + trade.quantity * (1 - cfg.MAKER_FEE) < -cfg.POSITION_LIMITS[symbol] and not dataframes[symbol]['position'][i] <= -cfg.POSITION_LIMITS[symbol]:
                                if log_messages:
                                    logger.warning("Limit order partially filled: " + str(trade))
                                dataframes[symbol].loc[i, 'position'] = -cfg.POSITION_LIMITS[symbol]
                            elif trade.quantity > 0 and dataframes[symbol]['position'][i] + trade.quantity * (1 - cfg.MAKER_FEE) > cfg.POSITION_LIMITS[symbol] and not dataframes[symbol]['position'][i] >= cfg.POSITION_LIMITS[symbol]:
                                if log_messages:
                                    logger.warning("Limit order partially filled: " + str(trade))
                                dataframes[symbol].loc[i, 'position'] = cfg.POSITION_LIMITS[symbol]
                            elif cfg.POSITION_LIMITS[symbol] <= 0:
                                if log_messages:
                                    logger.info("Limit order filled: " + str(trade))
                                dataframes[symbol].loc[i, 'position'] += trade.quantity * (1 - cfg.MAKER_FEE)
                            else:
                                if log_messages:
                                    logger.warning("Limit order not filled, exceeds position limit: " + str(trade))
    return dataframes

# save the results of the backtest
def saveResults(dfs: Dict[str, pd.DataFrame], strategy_name: str):
    if not os.path.exists('BacktestResults'):
        os.mkdir('BacktestResults')
    for symbol in dfs:
        if symbol in cfg.SYMBOLS_TO_BE_TRADED:
            dfs[symbol].to_csv('BacktestResults/' + strategy_name + '_' + symbol + '.csv')

# plot the results of the backtest
def plotResults(df: pd.DataFrame):
    fig, ax1 = plt.subplots()

    color = 'tab:green'
    ax1.set_xlabel('timestamp')
    ax1.set_ylabel('position', color=color)
    ax1.plot([dr.unix_to_date_time(time) for time in df['t']], df['position'], color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('PNL', color=color)  # we already handled the x-label with ax1
    ax2.plot([dr.unix_to_date_time(time) for time in df['t']], df['pnl'], color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    ax3 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:red'
    ax3.set_ylabel('price', color=color)  # we already handled the x-label with ax1
    ax3.plot([dr.unix_to_date_time(time) for time in df['t']], df['c'], color=color)
    ax3.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()

# run the backtest
def run(strategy_name: str, log_messages: bool = False):
    dfs = getResults(strategy_name, log_messages)
    saveResults(dfs, strategy_name)
    for symbol in dfs:
        if symbol in cfg.SYMBOLS_TO_BE_TRADED:
            plotResults(dfs[symbol])

# run the backtest
if __name__ == "__main__":
    run(cfg.STRATEGY_NAME, log_messages=True)
