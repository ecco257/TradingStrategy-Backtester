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

training_methods = [
    returns,
]