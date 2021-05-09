from __future__ import division, absolute_import, print_function

import backtrader as bt
from datetime import timedelta
from backtrader.utils import date2num

import os
import btconfig

from btconfig.helper import get_data_params
from btconfig.feeds.csv import CSVAdjustTime
from btconfig.utils.date import getstarttime
from btconfig.utils.download import IBDownloadApp


class IBDataAdjustTime(bt.feeds.IBData):

    def _load_rtbar(self, rtbar, hist=False):
        res = super(IBDataAdjustTime, self)._load_rtbar(rtbar, hist)
        if res and hist:
            new_date = getstarttime(
                self._timeframe,
                self._compression,
                self.datetime.datetime(0),
                self.p.sessionstart,
                -1) - timedelta(microseconds=100)
            self.lines.datetime[0] = date2num(new_date)
        return res


class IBDownload(btconfig.BTConfigDataloader):

    PREFIX = 'IB'

    def prepare(self):
        what = self._cfg['params'].get('what', 'MIDPOINT')
        self._additional.append(what)
        self._cls = CSVAdjustTime

    def _loadData(self):
        store = self._cfg.get('store')
        if not store:
            raise Exception('Store not defined')
        params = get_data_params(self._cfg, self._tz)
        dataname = self._cfg['dataname']
        timeframe = bt.TimeFrame.TFrame(self._cfg['granularity'][0])
        compression = self._cfg['granularity'][1]
        fromdate = params.get('fromdate')
        todate = params.get('todate')
        what = self._cfg['params'].get('what', 'MIDPOINT')
        useRTH = self._cfg['params'].get('useRTH', False)
        if not os.path.isfile(self._filename) or not todate:
            app = IBDownloadApp(
                self._instance.config['stores'][store]['params']['host'],
                self._instance.config['stores'][store]['params']['port'],
                self._instance.config['stores'][store]['params']['clientId'])
            app.download(
                self._filename, dataname, timeframe, compression,
                fromdate, todate, what, useRTH)
