from DataTypes import State, LimitOrder, MarketOrder
from typing import List, Union, Tuple, Dict, Any
import Configuration.Config as cfg
from TradingFunctions import getMaxBuyQuantity, getMaxSellQuantity, log
import pandas as pd
from ta import trend, momentum, volatility
# ^ if you want to use other indicators, you can import them here. refer to https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html

# this is an example limit order strategy to market make in a liquid market that oscillates around a mean
# this strategy uses a hyperparameter called spread_pct, which controls how far away from the mean the limit orders are placed
# NOTE: you must name your strategy function "strategy"
def strategy(states: Dict[str, State], data: pd.DataFrame, params: Dict[str, Any]) -> Tuple[List[Union[LimitOrder, MarketOrder]], pd.DataFrame]:
    # ---------------------------------------------------------------------------------------------
    # Step 1: Set up the data you want to use for your strategy
    # ---------------------------------------------------------------------------------------------
    if 'close_history' not in data:
        data.insert(0, 'close_history', [])
    if 'ema' not in data:
        data.insert(1, 'ema', [])

    # ---------------------------------------------------------------------------------------------
    # Step 2: Update the data you want to use for your strategy
    # ---------------------------------------------------------------------------------------------

    data.loc[len(data)] = [states['BINANCE:BTCUSDT'].close, states['BINANCE:BTCUSDT'].close]

    ema = trend.EMAIndicator(data['close_history'], 9, fillna=True).ema_indicator()
    current_ema = ema[len(ema)-1]
    data['ema'][len(data)-1] = current_ema

    # ---------------------------------------------------------------------------------------------
    # Step 3: Make your trading decisions
    # ---------------------------------------------------------------------------------------------
    orders: List[Union[LimitOrder, MarketOrder]] = []

    # basic ping pong strategy
    if states['BINANCE:BTCUSDT'].position >= 0:
        orders.append(LimitOrder('BINANCE:BTCUSDT', states['BINANCE:BTCUSDT'].timestamp, getMaxSellQuantity(states['BINANCE:BTCUSDT']), data['ema'][len(data)-1]*(1+params['spread_pct'])))
    elif states['BINANCE:BTCUSDT'].position < 0:
        orders.append(LimitOrder('BINANCE:BTCUSDT', states['BINANCE:BTCUSDT'].timestamp, getMaxBuyQuantity(states['BINANCE:BTCUSDT']), data['ema'][len(data)-1]*(1-params['spread_pct'])))

    return orders, data
