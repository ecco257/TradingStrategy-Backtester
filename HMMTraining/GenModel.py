import sys
# add the parent directory to the path so that we can import Config.py when running this file directly 
# (in terminal with current directory set to HMMTraining)
sys.path[0] += '/..'
import Configuration.Config as cfg
import Configuration.DateRange as dr
from Backtester import getDataForSymbol
import os
from HMMTraining.TrainingMethods import training_methods
import numpy as np
from hmmlearn.hmm import GaussianHMM
import pickle
import matplotlib.pyplot as plt

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

def plotModel():

    with open('Models/' + str(cfg.MODEL_TO_USE) + '.pkl', 'rb') as file:
        model = pickle.load(file)

    price_data = getDataForSymbol(cfg.SYMBOL_TO_TRAIN)

    training_data = [training_methods[i](price_data) for i in range(len(training_methods))]

    packed_data = np.column_stack(training_data)

    hidden_states = model.predict(packed_data)

    fig = plt.figure(figsize=(15, 8))
    # plot the data as a scatter plot with x being the date and y being the close price, colored by the hidden state
    ax = fig.add_subplot(111)
    ax.scatter([dr.unix_to_date(x) for x in price_data['t']], price_data['c'], c=hidden_states, cmap='viridis')
    ax.set_title('Hidden States Over Time')
    ax.set_xlabel('Date')
    ax.set_ylabel('Close Price')
    plt.show()

if __name__ == '__main__':
    # if the argument is train, train the model, if it is plot, plot the model
    if sys.argv[1] == 'train':
        trainModel()
    elif sys.argv[1] == 'plot':
        plotModel()
    else:
        raise ValueError('Argument must be either train or plot')