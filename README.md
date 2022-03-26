# BTConfig

BTConfig is a configureable backtrader execution helper. It is using
JSON-formatted config files.

It supports different execution modes:

* LIVE: Executes live trading mode
* BACKTEST: Executes backtest mode
* OPTIMIZE: Executes optimization mode
* OPTIMIZEGENETIC: Executes genetic optimization mode

## Modes

Btconfig can be executed in different run modes.

### Mode: LIVE

Executes backtrader in live mode with live plotting support

### Mode: BACKTEST

Executes backtrader in backtest mode with web plotting support

### Mode: OPTIMIZE

Executes backtrader in optimization mode
using backtrader built-in `optstrategy` with
optimization results browseable in a browser

### Mode: OPTIMIZEGENETIC

Executes backtrader in optimization mode
using `Gradient-Free-Optimizers` [https://github.com/SimonBlanke/Gradient-Free-Optimizers]
with optimization results browseable in a browser

## Features

* Execution of strategies without code
* Configuration of backtrader components using config files
* Data downloader for Oanda, Interactive Brokers, Binance, Yahoo included
* Additional Dataloader: CoinMetrics, CoinAPI
* API Clients for: CoinAPI, CoinMetrics, CoinGecko, CoinMarketCap, CoinGlass (WIP)
* Custom feeds with time correction (useful for resample and replay)
* Custom feeds with data rounding
* Live Plotting, Optimization Browser, Backtest Results using btplotting
* Prototype Strategies for Forex Trading with functionality to work with
  pips, market hours, logging etc.
* Tearsheet support using QuantStats
* Additional Analysers for Backtesting
* Optimization using the built-in bruteforce method or using genetic algorithms

## Contribute

We are looking for contributors: if you are interested to join us please contact us.

## Sponsoring

If you want to support the development of btoandav20, consider to support this project.

* BTC: 39BJtPgUv6UMjQvjguphN7kkjQF65rgMMF
* ETH: 0x06d6f3134CD679d05AAfeA6e426f55805f9B395D
* <https://liberapay.com/happydasch>
