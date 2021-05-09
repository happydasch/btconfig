from __future__ import division, absolute_import, print_function

from btconfig.helper import get_data_params
from btconfig.utils.download import BinanceDownloadApp

import backtrader as bt

import os
import btconfig

from btconfig.feeds.csv import CSVAdjustTime


class BinanceDownload(btconfig.BTConfigDataloader):

    PREFIX = 'IB'

    def prepare(self):
        self._cls = CSVAdjustTime

    def _loadData(self):
        params = get_data_params(self._cfg, self._tz)
        dataname = self._cfg['dataname']
        fromdate = params.get('fromdate')
        todate = params.get('todate')
        timeframe = bt.TimeFrame.TFrame(self._cfg['granularity'][0])
        compression = self._cfg['granularity'][1]
        if not os.path.isfile(self._filename) or not todate:
            api_key = self._cfg.get('api_key', '')
            api_secret = self._cfg.get('api_secret', '')
            client = BinanceDownloadApp(api_key, api_secret)
            client.download(
                self._filename, dataname, timeframe, compression,
                fromdate, todate)
