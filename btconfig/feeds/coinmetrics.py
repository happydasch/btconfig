from __future__ import division, absolute_import, print_function

import os
import backtrader as bt

from btconfig import BTConfigDataloader
from btconfig.helper import get_data_dates
from btconfig.feeds.misc import (
    CSVAdjustTime, CSVAdjustTimeMVRVData, CSVAdjustTimeCloseOnly)
from btconfig.utils.dataloader import CoinMetricsDataloaderApp
from btconfig.utils.dataloader import CoinMetricsDataDataloaderApp


class CoinMetricsDataloader(BTConfigDataloader):

    PREFIX = 'COINMETRICS'

    def _prepare(self):
        self._cls = CSVAdjustTime
        self.client = CoinMetricsDataloaderApp(debug=debug)

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
            debug = self._cfg.get('debug', False)
            return self.client.request(
                dataname, timeframe, compression, fromdate, todate)


class CoinMetricsMVRVDataloader(BTConfigDataloader):

    PREFIX = 'COINMETRICS_MVRV'

    def _prepare(self):
        use_base_asset = self._cfg.get('use_base_asset', True)
        self._additional.append('BASE' if use_base_asset else 'QUOTE')
        self._cls = CSVAdjustTimeMVRVData
        self.loader = CoinMetricsDataloaderApp(debug=debug)

    def _loadData(self):
        dataname = self._cfg['dataname']
        timeframe = bt.TimeFrame.TFrame(self._cfg['granularity'][0])
        compression = self._cfg['granularity'][1]
        fromdate, todate = get_data_dates(
            self._cfg.get('backfill_days'),
            self._cfg.get('fromdate'),
            self._cfg.get('todate'))
        use_base_asset = self._cfg.get('use_base_asset', True)
        if self._filedate:
            fromdate = self._filedate
        if not os.path.isfile(self._filename) or not todate:
            debug = self._cfg.get('debug', False)
            data = self.loader.request(
                dataname, timeframe, compression, fromdate, todate,
                add_mvrv=True, use_base_asset=use_base_asset)
            return data


class CoinMetricsDataDataloader(BTConfigDataloader):

    PREFIX = 'COINMETRICS'

    def _prepare(self):
        self._cls = CSVAdjustTimeCloseOnly
        self.dropna = self._cfg.get('dropna', False)
        if self.dropna:
            self._additional.append('CLEAN')
        self.client = CoinMetricsDataDataloaderApp()

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
            data = self.client.request(
                dataname, timeframe, compression, fromdate, todate)
            if self.dropna:
                return data.dropna()
            return data
