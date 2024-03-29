from DataTypes import State, LimitOrder, MarketOrder
from typing import List, Union, Tuple, Dict, Any
import Configuration.Config as cfg
from TradingFunctions import getMaxBuyQuantity, getMaxSellQuantity, log
import pandas as pd
from ta import trend, momentum, volatility
# ^ if you want to use other indicators, you can import them here. refer to https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html

# this is an example market order strategy that trades in a market with momentum
# NOTE: you must name your strategy function "strategy"
def strategy(states: Dict[str, State], data: pd.DataFrame, params: Union[Dict[str, Any], None] = None) -> Tuple[List[Union[LimitOrder, MarketOrder]], pd.DataFrame]:
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

    data.loc[len(data)] = [states['BTC/USDT'].close, 50]

    rsi = momentum.RSIIndicator(data['close_history'], params['rsi_lookback'], fillna=False).rsi()
    current_rsi = rsi[len(rsi)-1]
    log('RSI: ' + str(current_rsi) + ' at ' + str(states['BTC/USDT'].timestamp), cfg.STRATEGY_NAME)
    data['rsi'][len(data)-1] = current_rsi

    # ---------------------------------------------------------------------------------------------
    # Step 3: Make your trading decisions
    # ---------------------------------------------------------------------------------------------
    orders: List[Union[LimitOrder, MarketOrder]] = []
    if data['rsi'][len(data)-1] is not None and data['rsi'][len(data)-1] < params['rsi_buy_threshold']:
        orders.append(MarketOrder('BTC/USDT', states['BTC/USDT'].timestamp, getMaxBuyQuantity(states['BTC/USDT'])))
    elif data['rsi'][len(data)-1] is not None and data['rsi'][len(data)-1] > params['rsi_sell_threshold']:
        orders.append(MarketOrder('BTC/USDT', states['BTC/USDT'].timestamp, -states['BTC/USDT'].position))

    return orders, data
