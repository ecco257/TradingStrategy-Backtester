import Configuration.config as cfg
from DataTypes import State
import os
from datetime import datetime as dt

def getMaxBuyQuantity(state: State) -> float:
    return cfg.POSITION_LIMIT - state.position if cfg.POSITION_LIMIT > 0 else 100

def getMaxSellQuantity(state: State) -> float:
    return -(state.position + cfg.POSITION_LIMIT) if cfg.POSITION_LIMIT > 0 else -100

def log(msg: str, log_file_name: str):
    # write the message to the log file
    f = open('Logs/Backtest/' + log_file_name + ".log", "a")
    f.write('[' + dt.now().strftime("%m/%d/%Y %H:%M:%S:%f") + '] ' + msg + '\n')

