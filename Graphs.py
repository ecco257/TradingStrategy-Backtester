import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# each graph function should take in a dataframe which contains the data obtained from the strategy
# and return a plotly figure that can be displayed through st.plotly_chart(fig)
def rsiWithThresholds(price_data: pd.DataFrame) -> go.Figure:
    assert 'timestamp' in price_data
    assert 'rsi' in price_data

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=price_data['timestamp'], y=price_data['rsi'], name='RSI'), secondary_y=False)
    fig.add_trace(go.Scatter(x=price_data['timestamp'], y=[30] * len(price_data['timestamp']), name='RSI Buy Threshold'), secondary_y=False)
    fig.add_trace(go.Scatter(x=price_data['timestamp'], y=[70] * len(price_data['timestamp']), name='RSI Sell Threshold'), secondary_y=False)
    fig.update_layout(title_text='RSI With Thresholds')
    fig.update_yaxes(title_text='RSI', secondary_y=False)
    return fig

# here you can choose which graphs you want to display by adding the function(s) to this list
graphs = []