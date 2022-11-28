import yfinance as yf
import streamlit
from plotly import graph_objs as go
msft = yf.Ticker("AMD")
msft_hist = msft.history(period="max")

import os
import pandas as pd

DATA_PATH = "AMD.json"

if os.path.exists(DATA_PATH):
    # Read from file if we've already downloaded the data.
    with open(DATA_PATH) as f:
        msft_hist = pd.read_json(DATA_PATH)
else:
    msft = yf.Ticker("AMD")
    msft_hist = msft.history(period="max")

    # Save file to json in case we need it later.  This prevents us from having to re-download it every time.
    msft_hist.to_json(DATA_PATH)

# Ensure we know the actual closing price
data = msft_hist[["Close"]]
data = data.rename(columns = {'Close':'Actual_Close'})

# Setup our target.  This identifies if the price went up or down
data["Target"] = msft_hist.rolling(2).apply(lambda x: x.iloc[1] > x.iloc[0])["Close"]

# Shift stock prices forward one day, so we're predicting tomorrow's stock prices from today's prices.
msft_prev = msft_hist.copy()
msft_prev = msft_prev.shift(1)

# Create our training data
predictors = ["Close", "Volume", "Open", "High", "Low"]
data = data.join(msft_prev[predictors]).iloc[1:]

from sklearn.ensemble import RandomForestClassifier
import numpy as np

# Create a random forest classification model.  Set min_samples_split high to ensure we don't overfit.
model = RandomForestClassifier(n_estimators=100, min_samples_split=200, random_state=1)

# Create a train and test set
train = data.iloc[:-100]
test = data.iloc[-100:]

model.fit(train[predictors], train["Target"])

from sklearn.metrics import precision_score

# Evaluate error of predictions
preds = model.predict(test[predictors])
preds = pd.Series(preds, index=test.index)
precision_score(test["Target"], preds)

combined = pd.concat({"Target": test["Target"],"Predictions": preds}, axis=1)

i = 1000
step = 750

def backtest(data, model, predictors, start=1000, step=750):
    predictions = []
    # Loop over the dataset in increments
    for i in range(start, data.shape[0], step):
        # Split into train and test sets
        train = data.iloc[0:i].copy()
        test = data.iloc[i:(i+step)].copy()

        # Fit the random forest model
        model.fit(train[predictors], train["Target"])

        # Make predictions
        preds = model.predict_proba(test[predictors])[:,1]
        preds = pd.Series(preds, index=test.index)
        # preds[preds > .6] = 1
        # preds[preds<=.6] = 0

        # Combine predictions and test values
        combined = pd.concat({"Target": test["Target"],"Predictions": preds}, axis=1)

        predictions.append(combined)

    return pd.concat(predictions)

predictions = backtest(data, model, predictors)

# add a column for the closing price
predictions["Close"] = data["Actual_Close"]

#plot buy and sell signals over price history on streamlit
fig = go.Figure()
fig.add_trace(go.Scatter(x=predictions.index, y=predictions["Close"], name="Price"))
fig.update_layout(title="Buy and Sell Signals", xaxis_title="Date", yaxis_title="Price")
streamlit.plotly_chart(fig)

#plot buy and sell signals over price history on streamlit
fig = go.Figure()
fig.add_trace(go.Scatter(x=predictions.index, y=predictions["Predictions"], name="Predictions"))
fig.update_layout(title="Buy and Sell Signals", xaxis_title="Date", yaxis_title="Price")
streamlit.plotly_chart(fig)