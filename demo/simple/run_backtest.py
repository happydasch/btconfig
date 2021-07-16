import btconfig
from simple_strategy import SimpleStrategy
from pandas_datareader import data as web
import pandas as pd
import os
from datetime import datetime

if os.path.isfile("sp500_prices.csv"):
    sp500_df = pd.read_csv("sp500_prices.csv", parse_dates=True)
else:
    sp500_df = web.DataReader("^GSPC", "yahoo", datetime.datetime(1950,1,1), datetime.datetime(2019,12,19))
    sp500_df.to_csv("sp500_prices.csv")


if __name__ == '__main__':
    res = btconfig.run(btconfig.MODE_BACKTEST, "config.json")