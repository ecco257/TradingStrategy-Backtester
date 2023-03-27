import Configuration.config as cfg
from DataTypes import State
import os
from datetime import datetime as dt

def getMaxBuyQuantity(state: State) -> float:
    return cfg.POSITION_LIMIT - state.position

def getMaxSellQuantity(state: State) -> float:
    return -(state.position + cfg.POSITION_LIMIT)

def log(msg: str, log_file_name: str):
    # first check if the log file exists in backtest results
    if not os.path.exists('BacktestResults/' + log_file_name + "Log.log"):
        # if it doesn't exist, create it
        f = open('BacktestResults/' + log_file_name + "Log.log", "w")
        f.close()

    # write the message to the log file
    f = open('BacktestResults/' + log_file_name + "Log.log", "a")
    f.write('[' + dt.now().strftime("%m/%d/%Y %H:%M:%S") + '] ' + msg + '\n')

