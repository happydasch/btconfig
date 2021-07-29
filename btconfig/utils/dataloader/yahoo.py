from __future__ import division, absolute_import, print_function

import yfinance
import requests
import pandas as pd
import backtrader as bt


class YahooDataloaderApp:

    INTERVALS = {
        (bt.TimeFrame.Minutes, 1): '1m',
        (bt.TimeFrame.Minutes, 2): '2m',
        (bt.TimeFrame.Minutes, 5): '5m',
        (bt.TimeFrame.Minutes, 15): '15m',
        (bt.TimeFrame.Minutes, 30): '30m',
        (bt.TimeFrame.Minutes, 60): '60m',
        (bt.TimeFrame.Minutes, 90): '90m',
        (bt.TimeFrame.Days, 1): '1d',
        (bt.TimeFrame.Days, 5): '5d',
        (bt.TimeFrame.Weeks, 1): '1wk',
        (bt.TimeFrame.Months, 1): '1mo',
        (bt.TimeFrame.Months, 3): '3mo'
    }

    def __init__(self, debug=False, **kwargs):
        self.debug = debug

    def request(self, instrument, timeframe, compression, fromdate, todate):
        if (timeframe, compression) not in self.INTERVALS:
            raise Exception(
                f'Unsupported ({timeframe}-{compression})'
                + ' granularity provided')
        interval = self.INTERVALS[(timeframe, compression)]
        sess = requests.Session()
        sess.headers['User-Agent'] = 'backtrader'
        ticker = yfinance.Ticker(instrument, session=sess)
        data_df = ticker.history(
            start=fromdate,
            end=todate,
            interval=interval,
            debug=self.debug)
        if data_df is not None:
            data_df.index.name = 'datetime'
            data_df.rename(
                columns={
                    'Open': 'open', 'High': 'high',
                    'Low': 'low', 'Close': 'close',
                    'Volume': 'volume'},
                inplace=True)
            data_df.drop(
                columns=['Dividends', 'Stock Splits'],
                inplace=True)
            data_df.reset_index(inplace=True)
        return data_df
