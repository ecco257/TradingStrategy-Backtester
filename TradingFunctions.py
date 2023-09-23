import Configuration.Config as cfg
from DataTypes import State
from datetime import datetime as dt
import os

def getMaxBuyQuantity(state: State) -> float: # this only obeys the position limits, not the cash limits
    # works for market orders only at the moment
    return (cfg.POSITION_LIMITS[state.security] - state.position) * (1 - cfg.TAKER_FEE) if cfg.POSITION_LIMITS[state.security] > 0 else 100

def getMaxSellQuantity(state: State) -> float: # this only obeys the position limits, not the cash limits
    return -(state.position + cfg.POSITION_LIMITS[state.security]) if cfg.POSITION_LIMITS[state.security] > 0 else -100

def getMaxBuyQuantityUsingCash(state: State) -> float: # this assumes that we are only allowed to buy what we can afford with our cash
    minimum = min(state.cash / state.close, getMaxBuyQuantity(state))
    return minimum if minimum > 0 else 0

def getMaxSellQuantityUsingPosition(state: State) -> float: # this assumes that we are only allowed to sell the positive positions we have, i.e. no shorting
    return -state.position if state.position > 0 else 0

def log(msg: str, log_file_name: str):
    # write the message to the log file
    if not os.path.exists('Logs/Backtest'):
        os.makedirs('Logs/Backtest')
    f = open('Logs/Backtest/' + log_file_name + ".log", "a")
    f.write('[' + dt.now().strftime("%m/%d/%Y %H:%M:%S:%f") + '] ' + msg + '\n')
