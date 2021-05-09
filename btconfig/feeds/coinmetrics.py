from __future__ import division, absolute_import, print_function

import os
import backtrader as bt

from btconfig import BTConfigDataloader
from btconfig.helper import get_data_dates
from btconfig.feeds.csv import CSVAdjustTime, CSVMVRVData
from btconfig.utils.download import CoinMetricsDownloadApp


class CoinMetricsDownload(BTConfigDataloader):

    PREFIX = 'COINMETRICS'

    def prepare(self):
        self._cls = CSVAdjustTime

    def _loadData(self):
        dataname = self._cfg['dataname']
        timeframe = bt.TimeFrame.TFrame(self._cfg['granularity'][0])
        compression = self._cfg['granularity'][1]
        fromdate, todate = get_data_dates(
            self._cfg['backfill_days'],
            self._cfg['fromdate'],
            self._cfg['todate'])
        if not os.path.isfile(self._filename) or not todate:
            api_key = self._cfg.get('api_key', '')
            client = CoinMetricsDownloadApp(api_key)
            client.download(
                self._filename, dataname, timeframe, compression,
                fromdate, todate)


class CoinMetricsMVRVDownload(BTConfigDataloader):

    PREFIX = 'COINMETRICS_MVRV'

    def prepare(self):
        self._cls = CSVMVRVData

    def _loadData(self):
        dataname = self._cfg['dataname']
        timeframe = bt.TimeFrame.TFrame(self._cfg['granularity'][0])
        compression = self._cfg['granularity'][1]
        fromdate, todate = get_data_dates(
            self._cfg['backfill_days'],
            self._cfg['fromdate'],
            self._cfg['todate'])
        if not os.path.isfile(self._filename) or not todate:
            api_key = self._cfg.get('api_key', '')
            client = CoinMetricsDownloadApp(api_key)
            client.download(
                self._filename, dataname, timeframe, compression,
                fromdate, todate, add_mvrv=True,
                use_base_asset=True)
