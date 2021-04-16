from __future__ import division, absolute_import, print_function

import backtrader as bt
from dateutil import parser

import os
import btconfig

from btconfig.feeds.csv import CSVBidAskAdjustTime
from btconfig.parts.data import get_data_params
from btconfig.utils.oandav20 import OandaV20DownloadApp


class OandaV20Download(btconfig.BTConfigDataloader):

    def load(self):
        commoncfg = self._instance.config.get('common', {})
        path = commoncfg.get('data_path', './data')
        dataname = self._cfg['dataname']
        store = self._cfg.get('store')
        if not store:
            raise Exception('Store not defined')
        # params for filename
        bidask = self._cfg['params'].get('bidask', True)
        useask = self._cfg['params'].get('useask', False)
        if bidask and useask:
            ctype = 'ASK'
        elif bidask:
            ctype = 'BID'
        else:
            ctype = 'MID'
        fromdate = self._cfg.get('fromdate', None)
        todate = self._cfg.get('todate', None)
        backfill_days = self._cfg.get('backfill_days', None)
        if backfill_days:
            fromdate = None
            todate = None
        filename = 'OANDA_CSV_DATA_{}_{}_{}_{}_{}_{}_{}.csv'.format(
            ctype, dataname,
            self._cfg['granularity'][0],
            self._cfg['granularity'][1],
            fromdate, todate, backfill_days
        )
        filename = os.path.join(path, filename)
        # download data into csv file
        if not fromdate or not todate or not os.path.isfile(filename):
            timeframe = bt.TimeFrame.TFrame(self._cfg['granularity'][0])
            compression = self._cfg['granularity'][1]
            app = OandaV20DownloadApp(
                self._instance.config['stores'][store]['params']['token'],
                self._instance.config['stores'][store]['params']['practice'])
            app.download(
                filename, dataname, timeframe, compression,
                fromdate, todate, bidask, useask)
        # set csv file from download
        params = get_data_params(self._cfg, self._tz)
        for i in ['fromdate', 'todate']:
            if i in params:
                del params[i]
        params['dataname'] = filename
        params['headers'] = True
        params['dtformat'] = parse_dt
        data = CSVBidAskAdjustTime(**params)
        return data


def parse_dt(dt):
    return parser.parse(dt)
