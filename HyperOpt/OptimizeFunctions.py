import pandas as pd
import numpy as np

#--------------------------------------------------
# Below are functions that can prioritize different things when hyperparameter optimizing
# You can create your own functions here depending on what you want to optimize for
# Basic format: takes in a dataframe of results and returns a float (an int may work too, just needs to be a number)
# This float will be maximized, so if you want to minimize something, return the negative of the value you want to minimize.
# You could also edit the study direction in HyperparamOptimizer.py 
#--------------------------------------------------

def byProfit(df: pd.DataFrame) -> float:
    # return the profit of the last row
    return df.iloc[-1]['pnl']

def byMinDrawdown(df: pd.DataFrame) -> float:
    # calculate the sharpe ratio
    max_drawdown = 0
    pnl = df['pnl']

    # insert a 0 at the beginning of the pnl list so that the first value is 0
    pnl = [0] + pnl.tolist()

    for i in range(1, len(pnl)):
        try:
            current_drawdown = min(0, pnl[i] - max(pnl[:i]))
        except ZeroDivisionError:
            current_drawdown = 0
        if current_drawdown < max_drawdown:
            max_drawdown = current_drawdown

    # max drawdown will either be 0 or negative, and since the optuna study is maximizing, we return the drawdown as is, because we want the least negative value
    return max_drawdown

def byNumTrades(df: pd.DataFrame) -> float:
    num_trades = 0
    for i in range(1, len(df)):
        if round(df.loc[i, 'position'], 2) != round(df.loc[i-1, 'position'], 2):
            num_trades += 1
    return num_trades

# counts the number of times at which the pnl vs the starting capital is greater than the current close vs the first close
def beatBenchmarkRate(df: pd.DataFrame) -> int:
    starting_capital = df['pnl'].iloc[0]
    assert starting_capital != 0
    benchmark_returns = []
    strat_returns = []
    for i in range(len(df['c'])):
        benchmark_returns.append(df['c'].iloc[i] / df['c'].iloc[0] - 1)
        strat_returns.append(df['pnl'].iloc[i] / starting_capital - 1)

    num_times_better = 0
    for i in range(len(benchmark_returns)):
        if strat_returns[i] > benchmark_returns[i]:
            num_times_better += 1
    return num_times_better

# counts the amount in percent that the pnl vs the starting capital is greater than the current close vs the first close
# essentially integrates the difference between the two curves
def beatBenchmarkAmount(df: pd.DataFrame) -> int:
    starting_capital = df['pnl'].iloc[0]
    assert starting_capital != 0
    benchmark_returns = []
    strat_returns = []
    for i in range(len(df['c'])):
        benchmark_returns.append(df['c'].iloc[i] / df['c'].iloc[0] - 1)
        strat_returns.append(df['pnl'].iloc[i] / starting_capital - 1)

    amount_better = 0
    for i in range(len(benchmark_returns)):
        amount_better += strat_returns[i] - benchmark_returns[i]
    return amount_better

optimization_functions = [ 
    beatBenchmarkAmount,
]