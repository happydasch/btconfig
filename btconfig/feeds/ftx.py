
from __future__ import division, absolute_import, print_function

import os
import btconfig
import backtrader as bt

from btconfig.helper import get_data_dates
from btconfig.feeds.misc import (
    CSVAdjustTime, CSVAdjustTimeCloseOnly)
from btconfig.utils.dataloader import FTXDataloaderApp


# src: https://github.com/ccxt/ccxt/blob/master/python/ccxt/ftx.py
# hard limit of 7 requests per 200ms
# => 35 requests per 1000ms
# => 1000ms / 35 = 28.5714 ms between requests
# => 0.0285714 s


class FTXDataloader(btconfig.BTConfigDataloader):

    PREFIX = 'FTX'

    def _prepare(self):
        self._cls = CSVAdjustTime
        pause = self._cfg.get('pause', 0.0285714)
        debug = self._cfg.get('debug', False)
        api_key = self._cfg.get('api_key', '')
        api_secret = self._cfg.get('api_secret', '')
        self.loader = FTXDataloaderApp(
            api_key=api_key, api_secret=api_secret,
            pause=pause, debug=debug)

    def _loadData(self):
        dataname = self._cfg['dataname']
        timeframe = bt.TimeFrame.TFrame(self._cfg['granularity'][0])
        compression = self._cfg['granularity'][1]
        fromdate, todate = get_data_dates(
            self._cfg.get('backfill_days'),
            self._cfg.get('fromdate'),
            self._cfg.get('todate'))
        if self._filedate:
            fromdate = self._filedate
        if not os.path.isfile(self._filename) or not todate:
            data = self.loader.getMarketCandles(
                dataname, timeframe, compression, fromdate, todate)
            return data


class FTXFundingRatesDataloader(btconfig.BTConfigDataloader):

    PREFIX = 'FTX_FR'

    def _prepare(self):
        self._cls = CSVAdjustTimeCloseOnly
        api_key = self._cfg.get('api_key', '')
        api_secret = self._cfg.get('api_secret', '')
        pause = self._cfg.get('pause', 0.0285714)
        debug = self._cfg.get('debug', False)
        self.loader = FTXDataloaderApp(
            api_key=api_key, api_secret=api_secret,
            pause=pause, debug=debug)

    def _loadData(self):
        dataname = self._cfg['dataname']
        fromdate, todate = get_data_dates(
            self._cfg.get('backfill_days'),
            self._cfg.get('fromdate'),
            self._cfg.get('todate'))
        if self._filedate:
            fromdate = self._filedate
        if not os.path.isfile(self._filename) or not todate:
            data = self.loader.getFundingRates(dataname, fromdate, todate)
            return data
