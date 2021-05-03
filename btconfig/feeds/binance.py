from __future__ import division, absolute_import, print_function

from btconfig.parts.data import get_data_params
from btconfig.feeds.csv import CSVAdjustTime
from btconfig.utils.date import parse_dt
from btconfig.utils.download import BinanceDownloadApp

import backtrader as bt

import os
import btconfig


class BinanceDownload(btconfig.BTConfigDataloader):

    def load(self):
        commoncfg = self._instance.config.get('common', {})
        path = commoncfg.get('data_path', './data')
        dataname = self._cfg['dataname']
        # params for filename
        fromdate = self._cfg.get('fromdate', None)
        todate = self._cfg.get('todate', None)
        backfill_days = self._cfg.get('backfill_days', None)
        if backfill_days:
            fromdate = None
            todate = None
        filename = 'BINANCE_{}_{}_{}_{}_{}_{}.csv'.format(
            dataname,
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
        timeframe = bt.TimeFrame.TFrame(self._cfg['granularity'][0])
        compression = self._cfg['granularity'][1]
        # download data into csv file
        if not fromdate or not todate or not os.path.isfile(filename):
            api_key = self._cfg.get('api_key', '')
            api_secret = self._cfg.get('api_secret', '')
            client = BinanceDownloadApp(api_key, api_secret)
            client.download(
                filename, dataname, timeframe, compression,
                fromdate, todate)
        # set csv file from download
        for i in ['fromdate', 'todate']:
            if i in params:
                del params[i]
        params['dataname'] = filename
        params['headers'] = True
        params['dtformat'] = parse_dt
        data = CSVAdjustTime(**params)
        return data
