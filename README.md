# TradingStrategy-Backtester

Trading Strategy backtester and hyperparameter optimizer for crypto and stocks (soon to add regime detection training and forward testing). 

## Getting Started

### Dependencies

* Python version 3.10.9 has been tested and works, other versions may also work. I used an [Anaconda](https://www.anaconda.com) environment to manage the packages needed. 

### Installing

* Clone this repository in the directory of your choice. 
* In the project directory with python and pip installed, enter `pip install -r requirements.txt` in terminal.

### How to make a strategy

* First set up your configuration in `Configuration/config.py`. This includes making a .env file to store your api key to connect to the [finnhub](https://finnhub.io) API.
* All strategies are kept in the strategies folder.
* Create a strategy file and follow the template for imports.
* Import any modules you may need for technical analysis. You can also create your own technical analysis functions. For more information, visit the [documentation for ta](https://technical-analysis-library-in-python.readthedocs.io/en/latest/index.html).
* Follow the template to create the strategy function.
  * Step 1: Set the columns of any data you want to keep track of throughout the course of backtesting.
  * Step 2: Update your data (i.e. add on to price history and/or technical indicators data).
  * Step 3: Use your data to decide which orders to place on this tick.
* Now you can run 1. `python Backtester.py download` (if trading a cryptocurrency, otherwise skip to 2), then 2. `streamlit run Backtester.py test`. Make sure you are in the project directory in terminal, then enter `python Backtester.py`. On a localhost using [Streamlit](https://streamlit.io), it will generate a graph of position over profit/loss over close price, as well as log messages for the strategy in the logs folder and save the results to a csv. 

### How to graph additional information

* Add a graph function to `Graphs.py`
* This function must take in a pandas dataframe and return a plotly object that can be plotted after the PNL on streamlit using `st.plotly_chart(your_figure)`
* It is a good idea to, for whichever graph functions you plan to be using, assert that the data exists, as does the RSI example (the pandas dataframe that is passed in consists of all the data obtained from whichever strategy was run)
* At the end of the `Graphs.py` file, add to the `graphs` list whichever graphs you want and are applicable to the strategy to be backtested.
* Run `Backtester.py` with the argument `test`, as follows: `streamlit run Backtester.py test`. If you are testing with a cryptocurrency, this assumes you have downloaded the neccessary data for the given `CRYPTO_INTERVAL` and time range with `python Backtester.py download`. Otherwise, for stocks, finnhub allows for a decent amount of data to be queried on the spot (for the day interval or greater, a very large range can be queried (i.e. 2000+ days), and for an interval less than a day it is about a month maximum). 

### Hyperparameter optimization

* this uses a module called [optuna](https://optuna.org). 
* First you must have a strategy that utilizes its `params` argument. For example, in Step 3 of creating a strategy (the rules to place orders on a given tick), you place a market buy order if `params['rsi_buy_threshold'] < 30`
* Next you must give a default value for these parameters in `Configuration/Config.py` under `STRATEGY_HYPERPARAMETERS`, and give a range for the parameters under `STRATEGY_HYPERPARAMETER_RANGES`.
* You can also specify the functions by which the parameters will be optimized by editing which functions are in the list `optimization_functions` found in `OptimizeFunctions.py`. For example, if using `byProfit` only, after optimizing hyperparameters, the trial with the highest profit will be logged. You can make your own hyper opt functions in `HyperOpt/OptimizeFunctions.py`
* You must also specify the number of trials under `HYPER_OPT_TRIALS` (more trials, better results and longer wait, vice versa) and the symbol, of the symbols to be traded, that will be optimized (`SYMBOL_TO_OPTIMIZE`). 
* Then, from the project directory, 1. `cd HyperOpt` 2. `python HyperparamOptimizer.py` (assuming that, if using crypto, you have already downloaded data using `python Backtester.py download`)
* Logs will be saved to `Logs/HyperOpt`

### Working with HMMs

* If you want to include Hidden Markov Models in your strategy, there is a two step process: Train a model, then test the model. 
* The first thing you must do to train the model is to make sure the configuration is set up properly
  * In `Configuration/Config.py`, set up the time range and interval you want to train the model on (`DELTA_TIME`, `TO_DATE_LESS`, and either `INTERVAL` (for stocks) or `CRYPTO_INTERVAL` (for crypto)). Note: Make sure to download data with `python Backtester.py download` in main project directory if using crypto. 
  * Configure the `NUMBER_OF_HIDDEN_STATES`, `COVARIANCE_TYPE`, and `NUMBER_OF_TRAINING_ITERATIONS` that will be used to train the model.
  * Configure which functions will be used to train the model in `HMMTraining/TrainingMethods.py`, and add the ones you want to the `training_methods` list at the bottom of the file. You can follow the example of `returns` in creating your own training method. Note that when testing, strategy data will be used (i.e. the data stored by the strategy), and when training a model, just price data from api will be used. 
* `cd` into `HMMTraining` and run `python GenModel.py`. This will generate a `.pkl` file of the model in `HMMTraining/Models`. 
* Now that you have the model saved, find the name of the file in `HMMTraining/Models` and set `MODEL_TO_USE` to the name of that file without the `.pkl` extension
* Now you can run the strategy in the main project directory with `streamlit run Backtester.py test`. It is recommended to make use of the closeColoredByState function by adding it to the `graphs` list in `Graphs.py` to see the resulting hidden states predicted by the trained model. This is to see if the model is working as indended and which states mean what (i.e. if `NUMBER_OF_HIDDEN_STATES` is 2, what do states 0 and 1 represent?). 

## Other configuration notes

* You must create `Configuration/.env` and store your api key for finnhub there as described in `Configuration/Config.py`. 
* `DELTA_TIME` is the range of time in days, while `TO_DATE_LESS` is how many days since today that the range will end. For example, with `DELTA_TIME = 30` and `TO_DATE_LESS = 5` the data that will be tested is 30 days long, ending 5 days ago. 
* `INTERVAL` is for stocks, `CRYPTO_INTERVAL` is for cryptocurrencies. 
* `TAKER_FEE` is for market orders, `MAKER_FEE` is for limit orders that don't immediately fill. These are in decimal percents (i.e. 0.01 = 1%)

## TODO

* Add the option to start with initial capital, instead of just having position limits
* Implement a trainer, so that things such as a hidden markov model for regime detection can be trained on lots of data and then used for backtesting/forward testing
* Implement forward testing, probably through a discord bot which makes a notification when trades are made, etc.

## Authors

[ecco257](https://github.com/ecco257)

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details
