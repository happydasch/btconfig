from __future__ import division, absolute_import, print_function

import os
import btconfig
import backtrader as bt

from btconfig.helper import get_data_params
from btconfig.feeds.csv import CSVBidAskAdjustTime
from btconfig.utils.dataloader import OandaV20DataloaderApp


class OandaV20Dataloader(btconfig.BTConfigDataloader):

    PREFIX = 'OANDA'

    def prepare(self):
        bidask = self._cfg['params'].get('bidask', True)
        useask = self._cfg['params'].get('useask', False)
        if bidask and useask:
            ctype = 'ASK'
        elif bidask:
            ctype = 'BID'
        else:
            ctype = 'MID'
        self._additional.append(ctype)
        self._cls = CSVBidAskAdjustTime

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
        bidask = self._cfg['params'].get('bidask', True)
        useask = self._cfg['params'].get('useask', False)
        if not os.path.isfile(self._filename) or not todate:
            loader = OandaV20DataloaderApp(
                self._instance.config['stores'][store]['params']['token'],
                self._instance.config['stores'][store]['params']['practice'])
            return loader.request(
                dataname, timeframe, compression, fromdate, todate,
                bidask, useask)
