import optuna
import sys
# add the parent directory to the path so that we can import Backtester.py and config.py when running this file directly 
# (in terminal with current directory set to HyperOpt)
sys.path[0] += '/..'
from Backtester import getResults, getDataForSymbol
import Configuration.Config as cfg
from typing import Any, Callable, Tuple, List, Dict
import logging
import pandas as pd
import os
from HyperOpt.OptimizeFunctions import optimization_functions
from time import time
from Configuration.DateRange import unix_to_date

def objective(trial, optimize_functions: List[Callable[[pd.DataFrame], Any]], price_data: Dict[str, pd.DataFrame]):
    # get the hyperparameters
    for param in cfg.STRATEGY_HYPERPARAMETERS:
        lower_bound = cfg.STRATEGY_HYPERPARAMETER_RANGES[param][0]
        upper_bound = cfg.STRATEGY_HYPERPARAMETER_RANGES[param][1]
        if type(cfg.STRATEGY_HYPERPARAMETERS[param]) == int:
            cfg.STRATEGY_HYPERPARAMETERS[param] = trial.suggest_int(param, lower_bound, upper_bound)
        elif type(cfg.STRATEGY_HYPERPARAMETERS[param]) == float:
            cfg.STRATEGY_HYPERPARAMETERS[param] = trial.suggest_float(param, lower_bound, upper_bound)
        elif type(cfg.STRATEGY_HYPERPARAMETERS[param]) == bool:
            cfg.STRATEGY_HYPERPARAMETERS[param] = trial.suggest_categorical(param, [True, False])
        else:
            raise Exception('Hyperparameter type not supported.')
    # get the results
    df = getResults(strategy_name=cfg.STRATEGY_NAME, price_data=price_data)[0][cfg.SYMBOL_TO_OPTIMIZE]
    
    optimize_results: Tuple[Any, ...] = tuple([optimize_function(df) for optimize_function in optimize_functions])

    # return the value to optimize by
    return optimize_results

def optimizeHyperparameters(n_trials: int = cfg.HYPER_OPT_TRIALS):

    if not os.path.exists('../Logs/HyperOpt'):
        os.makedirs('../Logs/HyperOpt')

    logger = logging.getLogger()
    
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.FileHandler('../Logs/HyperOpt/' + cfg.STRATEGY_NAME + 'Opt.log', mode='w'))

    optuna.logging.enable_propagation()  # Propagate logs to the root logger.
    optuna.logging.disable_default_handler()  # Stop showing logs in sys.stderr.

    logger.info('Optimizing hyperparameters for ' + cfg.STRATEGY_NAME)
    logger.info('Time: ' + str(unix_to_date(time())))

    price_data = {}
    for symbol in cfg.SYMBOLS_TO_BE_TRADED:
        price_data[symbol] = getDataForSymbol(symbol)

    # set the objective function to use the intended optimization function
    objective_with_args = lambda trial: objective(trial, optimization_functions, price_data)

    # optimize the hyperparameters
    study = optuna.create_study(directions=['maximize' for _ in range(len(optimization_functions))])

    study.optimize(objective_with_args, n_trials)

    # print the results and format it so that it can be copied and pasted into the config file
    logger.info('Best hyperparameters:')
    if len(optimization_functions) == 1:
        params = study.best_params

        logger.info('STRATEGY_HYPERPARAMETERS = {')
        for param in params:
            logger.info('    \'' + param + '\': ' + str(params[param]) + ',')
        logger.info('}')
    else:
        for trial in study.best_trials:
            logger.info('Results for trial ' + str(trial.number) + ':' + str(trial.values))
            logger.info('STRATEGY_HYPERPARAMETERS = {')
            for param in trial.params:
                logger.info('    \'' + param + '\': ' + str(trial.params[param]) + ',')
            logger.info('}')

if __name__ == '__main__':
    optimizeHyperparameters()