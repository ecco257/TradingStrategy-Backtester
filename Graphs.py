import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict
import Configuration.Config as cfg
import Configuration.DateRange as dr

# each graph function should take in a dataframe which contains the data obtained from the strategy
# and return a plotly figure that can be displayed through st.plotly_chart(fig)
# the graph functions can also take in the result data, which includes all the data that is logged for the strategy in BacktestResults
def kamaOverClose(strat_data: pd.DataFrame, result_data: Dict[str, pd.DataFrame]) -> go.Figure:
    assert 'timestamp' in strat_data
    assert 'close_history' in strat_data
    assert 'kama' in strat_data

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=[dr.unix_to_date_time(x) for x in strat_data['timestamp']], y=strat_data['close_history'], name='Close'), secondary_y=False)
    fig.add_trace(go.Scatter(x=[dr.unix_to_date_time(x) for x in strat_data['timestamp']], y=strat_data['kama'], name='KAMA'), secondary_y=False)
    fig.update_layout(title_text='KAMA Over Close')
    fig.update_yaxes(title_text='Close', secondary_y=False)
    fig.update_yaxes(title_text='KAMA', secondary_y=True)
    return fig

def rsiWithThresholds(strat_data: pd.DataFrame, result_data: Dict[str, pd.DataFrame]) -> go.Figure:
    assert 'timestamp' in strat_data
    assert 'rsi' in strat_data

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=[dr.unix_to_date_time(x) for x in strat_data['timestamp']], y=strat_data['rsi'], name='RSI'), secondary_y=False)
    fig.add_trace(go.Scatter(x=[dr.unix_to_date_time(x) for x in strat_data['timestamp']], y=[30] * len(strat_data['timestamp']), name='RSI Buy Threshold'), secondary_y=False)
    fig.add_trace(go.Scatter(x=[dr.unix_to_date_time(x) for x in strat_data['timestamp']], y=[70] * len(strat_data['timestamp']), name='RSI Sell Threshold'), secondary_y=False)
    fig.update_layout(title_text='RSI With Thresholds')
    fig.update_yaxes(title_text='RSI', secondary_y=False)
    return fig

# state our return and the return of the security we are trading against as metrics
def returnsVsBenchmark(strat_data: pd.DataFrame, result_data: Dict[str, pd.DataFrame]) -> go.Figure:
    strat_return = result_data[cfg.SYMBOLS_TO_BE_TRADED[0]]['pnl'].iloc[-1] / result_data[cfg.SYMBOLS_TO_BE_TRADED[0]]['pnl'].iloc[0] - 1
    benchmark_return = result_data[cfg.SYMBOLS_TO_BE_TRADED[0]]['c'].iloc[-1] / result_data[cfg.SYMBOLS_TO_BE_TRADED[0]]['c'].iloc[0] - 1
    fig = go.Figure(data=[go.Bar(x=['Strategy', 'Benchmark'], y=[strat_return*100, benchmark_return*100])])
    fig.update_layout(title_text='Return vs Buy and Hold', barmode='stack')
    return fig

# for each timestamp, plot the pct change of the close from the first timestamp
# do this for the strategy and the asset we are trading against
def returnsVsBenchmarkOverTime(strat_data: pd.DataFrame, result_data: Dict[str, pd.DataFrame]) -> go.Figure:
    first_price = result_data[cfg.SYMBOLS_TO_BE_TRADED[0]]['c'].iloc[0]
    starting_capital = result_data[cfg.SYMBOLS_TO_BE_TRADED[0]]['pnl'].iloc[0]
    assert starting_capital != 0
    assert 'timestamp' in strat_data
    assert len(strat_data['timestamp']) == len(result_data[cfg.SYMBOLS_TO_BE_TRADED[0]]['c'])
    benchmark_returns = []
    strat_returns = []
    for i in range(len(result_data[cfg.SYMBOLS_TO_BE_TRADED[0]]['c'])):
        benchmark_returns.append(result_data[cfg.SYMBOLS_TO_BE_TRADED[0]]['c'].iloc[i] / first_price - 1)
        strat_returns.append(result_data[cfg.SYMBOLS_TO_BE_TRADED[0]]['pnl'].iloc[i] / starting_capital - 1)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    # make the units in terms of percent
    fig.add_trace(go.Scatter(x=[dr.unix_to_date_time(x) for x in strat_data['timestamp']], y=[x*100 for x in benchmark_returns], name='Benchmark'), secondary_y=False)
    fig.add_trace(go.Scatter(x=[dr.unix_to_date_time(x) for x in strat_data['timestamp']], y=[x*100 for x in strat_returns], name='Strategy'), secondary_y=False)
    fig.update_layout(title_text='Return vs Buy and Hold Over Time')
    fig.update_yaxes(title_text='Return', secondary_y=False)
    return fig

# plot the close data colored by the hidden state, as a scatter plot
def closeColoredByState(strat_data: pd.DataFrame, result_data: Dict[str, pd.DataFrame]) -> go.Figure:
    states = strat_data['hidden_state'].to_list()
    closes = strat_data['close_history'].to_list()
    fig = go.Figure(data=go.Scatter(
        x=[dr.unix_to_date_time(x) for x in strat_data['timestamp']],
        y=closes,
        mode='markers',
        marker=dict(
            color=states,
            colorscale='Viridis',
            showscale=True
        )
    ))
    fig.update_layout(title_text='Close Colored By Hidden State')
    return fig

def returns(strat_data: pd.DataFrame, result_data: Dict[str, pd.DataFrame]) -> go.Figure:
    pct_change = strat_data['close_history'].pct_change().to_numpy()
    fig = go.Figure(data=go.Scatter(
        x=[dr.unix_to_date_time(x) for x in strat_data['timestamp']][1:],
        y=pct_change,
        mode='lines'
    ))
    fig.update_layout(title_text='Returns')
    return fig

def drawdown(strat_data: pd.DataFrame, result_data: Dict[str, pd.DataFrame]) -> go.Figure:
    # calculate drawdowns
    equity_curve = result_data[cfg.SYMBOLS_TO_BE_TRADED[0]]['pnl']
    running_max = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - running_max) / running_max

    fig = go.Figure(data=go.Scatter(
        x=[dr.unix_to_date_time(x) for x in strat_data['timestamp']],
        y=drawdown,
        mode='lines'
    ))
    fig.update_layout(title_text='Drawdown')
    return fig

# here you can choose which graphs you want to display by adding the function(s) to this list
graphs = []