import Configuration.Config as cfg
from DataTypes import State
from datetime import datetime as dt
import os

def getMaxBuyQuantity(state: State) -> float:
    return cfg.POSITION_LIMIT - state.position if cfg.POSITION_LIMIT > 0 else 100

def getMaxSellQuantity(state: State) -> float:
    return -(state.position + cfg.POSITION_LIMIT) if cfg.POSITION_LIMIT > 0 else -100

def log(msg: str, log_file_name: str):
    # write the message to the log file
    if not os.path.exists('Logs/Backtest'):
        os.makedirs('Logs/Backtest')
    f = open('Logs/Backtest/' + log_file_name + ".log", "a")
    f.write('[' + dt.now().strftime("%m/%d/%Y %H:%M:%S:%f") + '] ' + msg + '\n')
