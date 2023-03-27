import Configuration.config as cfg
from typing import List
from TradingFunctions import log
import finnhub as fh
import pandas as pd
import Configuration.date_range as dr
from DataTypes import State, LimitOrder, MarketOrder, Trade
import matplotlib.pyplot as plt

# Set up the API
finnhub_client = fh.Client(api_key=cfg.API_KEY)

# Get OHLCV data
def getOHLCV() -> pd.DataFrame:
    if cfg.USE_CRYPTO:
        return pd.DataFrame(finnhub_client.crypto_candles(cfg.CRYPTO_PAIR, cfg.INTERVAL, dr.FROM_DATE_UNIX, dr.TO_DATE_UNIX))
    else:
        return pd.DataFrame(finnhub_client.stock_candles(cfg.STOCK_TICKER, cfg.INTERVAL, dr.FROM_DATE_UNIX, dr.TO_DATE_UNIX))
    
# get the results of the backtest
# NOTE: the strategy must be in the strategies folder, and strategy_name excludes the .py extension
def getResults(strategy_name: str, log_messages: bool = False) -> pd.DataFrame:
    # get the OHLCV data
    df = getOHLCV()

    # import the strategy
    strategy = __import__('Strategies.' + strategy_name, fromlist=['strategy'])

    # initialize the data
    df['orders'] = [[] for i in range(len(df))]
    df['trades'] = [[] for i in range(len(df))]
    df['position'] = [0 for i in range(len(df))]
    df['pnl'] = [0 for i in range(len(df))]

    strat_data = pd.DataFrame()

    if log_messages:
        log("Starting backtest for " + strategy_name, strategy_name)

    for i in range(len(df)):

        if i > 1:
            # update the position
            df['position'][i] = df['position'][i-1]

            # update the PnL
            df['pnl'][i] = df['pnl'][i-1] + df['position'][i-1] * (df['c'][i] - df['c'][i-1])


        # get the current state
        state = State(df['t'][i], df['position'][i], df['o'][i], df['h'][i], df['l'][i], df['c'][i], df['v'][i])

        # get the orders
        orders, strat_data = strategy.strategy(state, strat_data, cfg.STRATEGY_HYPERPARAMETERS)

        short_limit = state.position
        long_limit = state.position

        # execute the orders
        for order in orders:
            if isinstance(order, MarketOrder):
                # execute the market order
                
                # check to make sure the order does not exceed the position limit
                if cfg.POSITION_LIMIT > 0 and ((order.quantity < 0 and short_limit + order.quantity < -cfg.POSITION_LIMIT) or \
                    (order.quantity > 0 and long_limit + order.quantity > cfg.POSITION_LIMIT)):
                    if log_messages:
                        log("Order exceeds position limit: " + str(order), strategy_name)
                else:
                    # execute the order
                    if order.quantity < 0:
                        short_limit += order.quantity
                    else:
                        long_limit += order.quantity

                    df['orders'][i].append(order)
                    df['trades'][i].append(Trade(order.timestamp, order.quantity, df['c'][i]))                    

            elif isinstance(order, LimitOrder):
                # execute the limit order
                if cfg.POSITION_LIMIT > 0 and ((order.quantity < 0 and state.position + order.quantity < -cfg.POSITION_LIMIT) or \
                    (order.quantity > 0 and state.position + order.quantity > cfg.POSITION_LIMIT)):
                    if log_messages:
                        log("Order exceeds position limit: " + str(order), strategy_name)
                else:
                    if order.quantity < 0:
                        short_limit += order.quantity
                    else:
                        long_limit += order.quantity

                    # check if the limit order is filled, if it is filled, then this is a market order with taker fees
                    if (order.quantity < 0 and df['c'][i] <= order.price) or \
                        (order.quantity > 0 and df['c'][i] >= order.price):
                        df['orders'][i].append(order)
                        df['trades'][i].append(Trade(order.timestamp, order.quantity, df['c'][i]))
                    else:
                        # if the limit order is not filled, then it is a limit order with maker fees
                        df['orders'][i].append(order)
                        df['trades'][i].append(Trade(order.timestamp, order.quantity, order.price, is_taker=False))
            else:
                raise Exception("Invalid order type: " + str(order))
        
        # update the position
        for trade in df['trades'][i]:
            if trade.is_taker:
                if log_messages:
                    log("Market order filled (or immediately filled limit order): " + str(trade), strategy_name)
                df['position'][i] += trade.quantity * (1 - cfg.TAKER_FEE)
        for trade_list in df['trades'][:i]:
            for trade in trade_list:
                if not trade.is_taker and ((trade.quantity < 0 and df['c'][i] >= trade.price) or (trade.quantity > 0 and df['c'][i] <= trade.price)):
                    if cfg.POSITION_LIMIT > 0 and not ((trade.quantity < 0 and df['position'][i] + trade.quantity * (1 - cfg.MAKER_FEE) < -cfg.POSITION_LIMIT) or \
                    (trade.quantity > 0 and df['position'][i] + trade.quantity * (1 - cfg.MAKER_FEE) > cfg.POSITION_LIMIT)):
                        if log_messages:
                            log("Limit order filled: " + str(trade), strategy_name)
                        df['position'][i] += trade.quantity * (1 - cfg.MAKER_FEE)
                    elif trade.quantity < 0 and df['position'][i] + trade.quantity * (1 - cfg.MAKER_FEE) < -cfg.POSITION_LIMIT and not df['position'][i] <= -cfg.POSITION_LIMIT:
                        if log_messages:
                            log("Limit order partially filled: " + str(trade), strategy_name)
                        df['position'][i] = -cfg.POSITION_LIMIT
                    elif trade.quantity > 0 and df['position'][i] + trade.quantity * (1 - cfg.MAKER_FEE) > cfg.POSITION_LIMIT and not df['position'][i] >= cfg.POSITION_LIMIT:
                        if log_messages:
                            log("Limit order partially filled: " + str(trade), strategy_name)
                        df['position'][i] = cfg.POSITION_LIMIT
                    elif cfg.POSITION_LIMIT <= 0:
                        if log_messages:
                            log("Limit order filled (no position limit): " + str(trade), strategy_name)
                        df['position'][i] += trade.quantity * (1 - cfg.MAKER_FEE)
                    else:
                        if log_messages:
                            log("Limit order not filled, exceeds position limit: " + str(trade), strategy_name)

    return df

# save the results of the backtest
def saveResults(df: pd.DataFrame, strategy_name: str):
    df.to_csv('BacktestResults/' + strategy_name + 'Results.csv')

# plot the results of the backtest
def plotResults(df: pd.DataFrame):
    fig, ax1 = plt.subplots()

    color = 'tab:green'
    ax1.set_xlabel('timestamp')
    ax1.set_ylabel('position', color=color)
    ax1.plot(df['t'], df['position'], color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('PNL', color=color)  # we already handled the x-label with ax1
    ax2.plot(df['t'], df['pnl'], color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    ax3 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:red'
    ax3.set_ylabel('price', color=color)  # we already handled the x-label with ax1
    ax3.plot(df['t'], df['c'], color=color)
    ax3.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()

# run the backtest
def run(strategy_name: str, log_messages: bool = False):
    df = getResults(strategy_name, log_messages)
    saveResults(df, strategy_name)
    plotResults(df)

# run the backtest
run(cfg.STRATEGY_NAME, log_messages=True)
        

            

            
    