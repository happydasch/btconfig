from __future__ import division, absolute_import, print_function

import os
import btconfig
import backtrader as bt

from datetime import timedelta, timezone
from backtrader.utils import date2num
from btconfig.helper import get_data_dates, get_starttime
from btconfig.feeds.misc import CSVAdjustTime
from btconfig.utils.dataloader import IBDataloaderApp


class IBDataAdjustTime(bt.feeds.IBData):

    def _load_rtbar(self, rtbar, hist=False):
        res = super(IBDataAdjustTime, self)._load_rtbar(rtbar, hist)
        if res and hist:
            new_date = get_starttime(
                self._timeframe,
                self._compression,
                self.datetime.datetime(0, tz=timezone.utc),
                self.p.sessionstart,
                -1) - timedelta(microseconds=100)
            self.lines.datetime[0] = date2num(new_date)
        return res


class IBDataloader(btconfig.BTConfigDataloader):

    PREFIX = 'IB'

    def prepare(self):
        what = self._cfg['params'].get('what', 'MIDPOINT')
        self._additional.append(what)
        self._cls = CSVAdjustTime

    def _loadData(self):
        store = self._cfg.get('store')
        if not store:
            raise Exception('Store not defined')
        dataname = self._cfg['dataname']
        timeframe = bt.TimeFrame.TFrame(self._cfg['granularity'][0])
        compression = self._cfg['granularity'][1]
        fromdate, todate = get_data_dates(
            self._cfg.get('backfill_days'),
            self._cfg.get('fromdate'),
            self._cfg.get('todate'))
        if self._filedate:
            fromdate = self._filedate
        what = self._cfg['params'].get('what', 'MIDPOINT')
        useRTH = self._cfg['params'].get('useRTH', False)
        if not os.path.isfile(self._filename) or not todate:
            storecfg = self._instance.config['stores'].get(store, {})
            pause = self._cfg.get('pause', None)
            debug = self._cfg.get('debug', False)
            loader = IBDataloaderApp(
                storecfg['params']['host'],
                storecfg['params']['port'],
                storecfg['params']['clientId'],
                pause=pause,
                debug=debug)
            data = loader.request(
                dataname, timeframe, compression, fromdate, todate,
                what, useRTH)
            return data
