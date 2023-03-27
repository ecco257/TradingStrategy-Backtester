from DataTypes import State, LimitOrder, MarketOrder
from typing import List, Union, Tuple
import Configuration.config as cfg
import pandas as pd
from TradingFunctions import getMaxBuyQuantity, getMaxSellQuantity
from ta import trend, momentum, volatility
# ^ if you want to use other indicators, you can import them here. refer to https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html

# this is an example market order strategy that trades in a market with momentum
# NOTE: you must name your strategy function "strategy"
def strategy(state: State, data: pd.DataFrame) -> Tuple[List[Union[LimitOrder, MarketOrder]], pd.DataFrame]:
    # ---------------------------------------------------------------------------------------------
    # Step 1: Set up the data you want to use for your strategy
    # ---------------------------------------------------------------------------------------------
    if 'close_history' not in data:
        data.insert(0, 'close_history', [])
    if 'rsi' not in data:
        data.insert(1, 'rsi', [])

    # ---------------------------------------------------------------------------------------------
    # Step 2: Update the data you want to use for your strategy
    # ---------------------------------------------------------------------------------------------

    if len(data) > 0:
        rsi = momentum.RSIIndicator(data['close_history'], 14, fillna=True).rsi()
        current_rsi = rsi[len(rsi)-1]
    else:
        current_rsi = 50

    data.loc[len(data)] = [state.close, current_rsi]

    # ---------------------------------------------------------------------------------------------
    # Step 3: Make your trading decisions
    # ---------------------------------------------------------------------------------------------
    orders: List[Union[LimitOrder, MarketOrder]] = []
    if data['rsi'][len(data)-1] < 30:
        orders.append(MarketOrder(state.timestamp, getMaxBuyQuantity(state)))
    elif data['rsi'][len(data)-1] > 70:
        orders.append(MarketOrder(state.timestamp, -state.position))

    return orders, data
