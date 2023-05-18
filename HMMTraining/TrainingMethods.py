import pandas as pd
import numpy as np
from typing import Dict
import sys

def returns(price_data: pd.DataFrame) -> np.ndarray:
    """
    Calculates the returns for a symbol based on its closes as seen in result data for the symbol to be trained
    """
    # get the closes for the symbol to be trained

    if 'HMMTraining' in sys.path[0]: # we are running GenModel.py and have access to result data
        pct_change = price_data['c'].pct_change().fillna(0).to_numpy()
    else: # we are running Backtester.py and have access to strategy data
        pct_change = price_data['close_history'].pct_change().fillna(0).to_numpy()
    
    # return the returns
    # make sure the data aligns with the price data
    assert len(pct_change) == len(price_data)
    return pct_change

def volumes(price_data: pd.DataFrame) -> np.ndarray:
    """
    Calculates the volumes for a symbol based on its volumes as seen in result data for the symbol to be trained
    """
    # get the volumes for the symbol to be trained

    if 'HMMTraining' in sys.path[0]: # we are running GenModel.py and have access to result data
        volumes = price_data['v'].to_numpy()
    else: # we are running Backtester.py and have access to strategy data
        volumes = price_data['volume_history'].to_numpy()
    
    # return the volumes
    # make sure the data aligns with the price data
    assert len(volumes) == len(price_data)
    return volumes

# (high / low) - 1
def ranges(price_data: pd.DataFrame) -> np.ndarray:
    """
    Calculates the ranges for a symbol based on its highs and lows as seen in result data for the symbol to be trained
    """
    # get the highs and lows for the symbol to be trained

    if 'HMMTraining' in sys.path[0]: # we are running GenModel.py and have access to result data
        highs = price_data['h'].to_numpy()
        lows = price_data['l'].to_numpy()
    else: # we are running Backtester.py and have access to strategy data
        highs = price_data['high_history'].to_numpy()
        lows = price_data['low_history'].to_numpy()
    
    # calculate the ranges
    ranges = (highs / lows) - 1
    # return the ranges
    # make sure the data aligns with the price data
    assert len(ranges) == len(price_data)
    return ranges

training_methods = [
    returns,
    ranges,
]