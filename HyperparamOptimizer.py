import optuna
from Backtester import getResults
import Configuration.config as cfg
from typing import Dict, Any
import logging

def objective(trial):
    # get the hyperparameters
    for param in cfg.STRATEGY_HYPERPARAMETERS:
        lower_bound = cfg.STRATEGY_HYPERPARAMETER_RANGES[param][0]
        upper_bound = cfg.STRATEGY_HYPERPARAMETER_RANGES[param][1]
        if type(cfg.STRATEGY_HYPERPARAMETERS[param]) == int:
            cfg.STRATEGY_HYPERPARAMETERS[param] = trial.suggest_int(param, lower_bound, upper_bound)
        elif type(cfg.STRATEGY_HYPERPARAMETERS[param]) == float:
            cfg.STRATEGY_HYPERPARAMETERS[param] = trial.suggest_float(param, lower_bound, upper_bound)
    # get the results
    df = getResults(cfg.STRATEGY_NAME)
    
    # return the final PnL
    return df['pnl'].iloc[-1]

def optimizeHyperparameters(n_trials: int = cfg.HYPER_OPT_TRIALS):

    logger = logging.getLogger()
    
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.FileHandler('Logs/HyperOpt/' + cfg.STRATEGY_NAME + 'Opt.log', mode='w'))

    optuna.logging.enable_propagation()  # Propagate logs to the root logger.
    optuna.logging.disable_default_handler()  # Stop showing logs in sys.stderr.

    # optimize the hyperparameters
    study = optuna.create_study(direction='maximize')

    logger.info('Optimizing hyperparameters for ' + cfg.STRATEGY_NAME)
    study.optimize(objective, n_trials)

    # print the results and format it so that it can be copied and pasted into the config file
    logger.info('Best hyperparameters:')
    params = study.best_params

    logger.info('STRATEGY_HYPERPARAMETERS = {')
    for param in params:
        logger.info('    \'' + param + '\': ' + str(params[param]) + ',')
    logger.info('}')

if __name__ == '__main__':
    optimizeHyperparameters()