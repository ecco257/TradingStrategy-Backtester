import sys
# add the parent directory to the path so that we can import Config.py when running this file directly 
# (in terminal with current directory set to HMMTraining)
sys.path[0] += '/..'
import Configuration.Config as cfg
from Backtester import getDataForSymbol
import os
from HMMTraining.TrainingMethods import training_methods
import numpy as np
from hmmlearn.hmm import GaussianHMM
import pickle

def trainModel():

    if not os.path.exists('Models'):
        os.makedirs('Models')

    price_data = getDataForSymbol(cfg.SYMBOL_TO_TRAIN)

    training_data = [training_methods[i](price_data) for i in range(len(training_methods))]

    packed_data = np.column_stack(training_data)

    model = GaussianHMM(n_components=cfg.NUMBER_OF_HIDDEN_STATES, covariance_type=cfg.COVARIANCE_TYPE, n_iter=cfg.NUMBER_OF_TRAINING_ITERATIONS).fit(packed_data)

    # save the model
    i = 0
    while os.path.exists('Models/' + cfg.STRATEGY_NAME + '_' + cfg.SYMBOL_TO_TRAIN.replace('/', '_') + '_' + str(i) + '.pkl'):
        i += 1
    with open('Models/' + cfg.STRATEGY_NAME + '_' + cfg.SYMBOL_TO_TRAIN.replace('/', '_') + '_' + str(i) + '.pkl', 'wb') as file:
        pickle.dump(model, file)

if __name__ == '__main__':
    trainModel()