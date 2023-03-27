# TradingStrategy-Backtester

Trading Strategy backtester and hyperparameter optimizer for crypto and stocks. 

## Getting Started

### Dependencies

* Python version 3.10.9 has been tested and works, other versions may also work.

### Installing

* In the project directory with python and pip installed, enter `pip install -r requirements.txt` in terminal.

### How to make a strategy

* First set up your configuration in Configuration/config.py. This includes making a .env file to store your api key to connect to the [finnhub](https://finnhub.io) API.
* All strategies are kept in the strategies folder.
* Create a strategy file and follow the template for imports.
* Import any modules you may need for technical analysis. You can also create your own technical analysis functions. For more information, visit the [documentation for ta](https://technical-analysis-library-in-python.readthedocs.io/en/latest/index.html).
* Follow the template to create the strategy function.
  * Step 1: Set the columns of any data you want to keep track of throughout the course of backtesting.
  * Step 2: Update your data (i.e. add on to price history and/or technical indicators data).
  * Step 3: Use your data to decide which orders to place on this tick.
* Now you can run Backtester.py. Make sure you are in the project directory in terminal, then enter `python3 Backtester.py`. It will generate a graph of position over profit/loss over close price, as well as log messages for the strategy and save the results to a csv. 

## WIP

* Still need to test Limit orders
* Add hyper optimization using [optuna](https://optuna.org)

## Authors

[ecco257](https://github.com/ecco257)

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details
