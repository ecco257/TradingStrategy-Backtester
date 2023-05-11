import Configuration.Config as cfg
from DataTypes import State
from datetime import datetime as dt
import os

def getMaxBuyQuantity(state: State) -> float: # this only obeys the position limits, not the cash limits
    return cfg.POSITION_LIMITS[state.security] - state.position if cfg.POSITION_LIMITS[state.security] > 0 else 100

def getMaxSellQuantity(state: State) -> float: # this only obeys the position limits, not the cash limits
    return -(state.position + cfg.POSITION_LIMITS[state.security]) if cfg.POSITION_LIMITS[state.security] > 0 else -100

def getMaxBuyQuantityUsingCash(state: State) -> float: # this assumes that we are only allowed to buy what we can afford with our cash
    if state.pnl > 0:
        return min(state.pnl / state.close, getMaxBuyQuantity(state))
    else:
        return 0

def getMaxSellQuantityUsingPosition(state: State) -> float: # this assumes that we are only allowed to sell the positive positions we have, i.e. no shorting
    if state.position > 0:
        return -state.position
    else:
        return 0

def log(msg: str, log_file_name: str):
    # write the message to the log file
    if not os.path.exists('Logs/Backtest'):
        os.makedirs('Logs/Backtest')
    f = open('Logs/Backtest/' + log_file_name + ".log", "a")
    f.write('[' + dt.now().strftime("%m/%d/%Y %H:%M:%S:%f") + '] ' + msg + '\n')
