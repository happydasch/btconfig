from __future__ import division, absolute_import, print_function

import backtrader as bt
from dateutil import parser
from datetime import timedelta
from backtrader.utils import date2num

import os
import btconfig

from btconfig.utils.date import getstarttime
from btconfig.feeds.csv import CSVAdjustTime
from btconfig.parts.data import get_data_params
from btconfig.utils.ib import IBDownloadApp


class IBDataAdjustTime(bt.feeds.IBData):

    def _load_rtbar(self, rtbar, hist=False):
        res = super(IBDataAdjustTime, self)._load_rtbar(rtbar, hist)
        if res and hist:
            new_date = getstarttime(
                self._timeframe,
                self._compression,
                self.datetime.datetime(0),
                self.sessionstart,
                -1) - timedelta(microseconds=100)
            self.lines.datetime[0] = date2num(new_date)
        return res


class IBDownload(btconfig.BTConfigDataloader):

    def load(self):
        commoncfg = self._instance.config.get('common', {})
        path = commoncfg.get('data_path', './data')
        dataname = self._cfg['dataname']
        store = self._cfg.get('store')
        if not store:
            raise Exception('Store not defined')
        # params for filename
        what = self._cfg['params'].get('what', 'MIDPOINT')
        fromdate = self._cfg.get('fromdate', None)
        todate = self._cfg.get('todate', None)
        backfill_days = self._cfg.get('backfill_days', None)
        if backfill_days:
            fromdate = None
            todate = None
        filename = 'IB_CSV_DATA_{}_{}_{}_{}_{}_{}_{}.csv'.format(
            what, dataname,
            self._cfg['granularity'][0],
            self._cfg['granularity'][1],
            fromdate, todate, backfill_days
        )
        filename = os.path.join(path, filename)
        # get params for data
        params = get_data_params(self._cfg, self._tz)
        fromdate = params.get('fromdate')
        todate = params.get('todate')
        if fromdate is None and todate is None:
            raise Exception('fromdate and todate is not set')
        # download data into csv file
        if not fromdate or not todate or not os.path.isfile(filename):
            timeframe = bt.TimeFrame.TFrame(self._cfg['granularity'][0])
            compression = self._cfg['granularity'][1]
            useRTH = self._cfg['params'].get('useRTH', False)
            app = IBDownloadApp(
                self._instance.config['stores'][store]['params']['host'],
                self._instance.config['stores'][store]['params']['port'],
                self._instance.config['stores'][store]['params']['clientId'])
            app.download(
                filename, dataname, timeframe, compression,
                fromdate, todate, what, useRTH)
        # set csv file from download
        for i in ['fromdate', 'todate']:
            if i in params:
                del params[i]
        params['dataname'] = filename
        params['headers'] = True
        params['dtformat'] = parse_dt
        data = CSVAdjustTime(**params)
        return data


def parse_dt(dt):
    return parser.parse(dt)
