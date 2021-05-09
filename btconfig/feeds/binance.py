from __future__ import division, absolute_import, print_function

import os
import btconfig
import backtrader as bt

from btconfig.helper import get_data_dates
from btconfig.utils.download import BinanceDownloadApp
from btconfig.feeds.csv import CSVAdjustTime


class BinanceDownload(btconfig.BTConfigDataloader):

    PREFIX = 'IB'

    def prepare(self):
        self._cls = CSVAdjustTime

    def _loadData(self):
        dataname = self._cfg['dataname']
        fromdate, todate = get_data_dates(
            self._cfg['backfill_days'],
            self._cfg['fromdate'],
            self._cfg['todate'])
        timeframe = bt.TimeFrame.TFrame(self._cfg['granularity'][0])
        compression = self._cfg['granularity'][1]
        if not os.path.isfile(self._filename) or not todate:
            api_key = self._cfg.get('api_key', '')
            api_secret = self._cfg.get('api_secret', '')
            client = BinanceDownloadApp(api_key, api_secret)
            client.download(
                self._filename, dataname, timeframe, compression,
                fromdate, todate)
