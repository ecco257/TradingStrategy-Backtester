import optuna
from Backtester import getResults
import Configuration.config as cfg
from typing import Dict, Any

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
    # optimize the hyperparameters
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials)

    # print the results
    print('Best trial:')
    trial = study.best_trial
    
    print('  Value: {}'.format(trial.value))
    
    print('  Params: ')
    for key, value in trial.params.items():
        print('    {}: {}'.format(key, value))

if __name__ == '__main__':
    optimizeHyperparameters()