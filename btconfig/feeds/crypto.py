from __future__ import division, absolute_import, print_function

from datetime import datetime
from dateutil import parser
from btconfig.parts.data import get_data_params
from btconfig.feeds.csv import CSVAdjustTime
from btconfig.utils.date import parse_dt
from binance.client import Client

import backtrader as bt
import numpy as np
import pandas as pd

import os
import time
import logging
import pytz
import btconfig


class BinanceDownload(btconfig.BTConfigDataloader):

    # https://github.com/pratikpv/cryptocurrency_data_downloader/blob/master/download_data_from_binance.py

    FMT = "%Y-%m-%d %H:%M:%S"  # e.g. 2019-11-16 23:16:15
    ORG_COLS = ['open', 'high', 'low', 'close', 'volume', 'close_time', 
                'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore']
    COLS = ['open', 'high', 'low', 'close', 'volume']
    INTERVALS = {
        (bt.TimeFrame.Minutes, 1): '1m',
        (bt.TimeFrame.Minutes, 3): '3m',
        (bt.TimeFrame.Minutes, 5): '5m',
        (bt.TimeFrame.Minutes, 15): '15m',
        (bt.TimeFrame.Minutes, 30): '30m',
        (bt.TimeFrame.Minutes, 60): '1h',
        (bt.TimeFrame.Minutes, 120): '2h',
        (bt.TimeFrame.Minutes, 240): '4h',
        (bt.TimeFrame.Minutes, 360): '6h',
        (bt.TimeFrame.Minutes, 480): '8h',
        (bt.TimeFrame.Minutes, 720): '12h',
        (bt.TimeFrame.Days, 1): '1d',
        (bt.TimeFrame.Days, 3): '3d',
        (bt.TimeFrame.Weeks, 1): '1w',
        (bt.TimeFrame.Months, 1): '1M'
    }

    def prepare(self):
        self.api_key = self._cfg.get('binance_api_key', '')
        self.api_secret = self._cfg.get('binance_api_secret', '')
        self.client = Client(
            api_key=self.api_key, api_secret=self.api_secret)

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
        if (timeframe, compression) not in self.INTERVALS:
            gran = self._cfg['granularity']
            raise Exception(
                f'Unsupported ({gran[0]}-{gran[1]}) granularity provided')
        # download data into csv file
        if not fromdate or not todate or not os.path.isfile(filename):
            self._download(
                filename, dataname, self.INTERVALS[(timeframe, compression)],
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

    def _download(self, filename, symbol, interval, from_date, to_date, pause=-1):
        """
        :param filename:
        :param symbol:
        :param interval:
        :param from_date:
        :param to_date:
        :param pause: pause seconds before downloading next batch.
            if pause == -1 --> random sleep(2,5)
            if pause == 0 --> no sleep
            if pause == num--> sleep for num of seconds
        :return:
        """
        try:
            data = pd.read_csv(filename)
            data_len = len(data)
            from_date = parser.parse(data.iloc[-1].time, ignoretz=True)
        except IOError:
            data_len = 0
        from_millis = self._toUnixMillis(from_date)
        from_millis_str = str(from_millis)
        to_millis = None
        to_millis_str = None
        if to_date:
            to_millis = self._toUnixMillis(to_date)
            to_millis_str = str(from_millis)

        count = 0
        while True:
            # download data
            self.log(f'Fetching binance historical data for {symbol}'
                     + f' {from_date} ({count + 1})', logging.DEBUG)
            klines = self.client.get_historical_klines(
                symbol, interval, from_millis_str, to_millis_str)
            new_columns = self.ORG_COLS.copy()
            new_columns.insert(0, 'time')
            if len(klines) > 0:
                data_df = pd.DataFrame(
                    klines, columns=new_columns)
            else:
                break
            for i in self.ORG_COLS:
                if i not in self.COLS:
                    del data_df[i]
            data_df['time'] = pd.to_datetime(
                data_df['time'], unit='ms')

            # if first line then output also headers
            if data_len == 0:
                data_df.to_csv(filename, index=False)
            else:
                data_df[1:].to_csv(filename, header=None,
                                   index=False, mode='a')
            data_len += len(data_df)

            # check for exit
            if to_millis and from_millis >= to_millis:
                break
            if from_date == data_df.iloc[-1].time:
                break
            # move to next step of batches
            from_date = data_df.iloc[-1].time
            from_millis = self._toUnixMillis(from_date)
            count = count + 1
            if pause == -1:
                pause = np.random.randint(2, 5)
            time.sleep(pause)

    def _convertTimeToUtc(self, pst_time):
        utc = pytz.utc
        pst = pytz.timezone('America/Los_Angeles')
        datetime1 = datetime.strptime(pst_time, self.FMT)
        pst_time = pst.localize(datetime1)
        return pst_time.astimezone(utc).strftime(self.FMT)

    def _convertTimeToPst(self, utc_time):
        datetime_obj = datetime.strptime(utc_time, self.FMT)
        return datetime_obj.replace(
            tzinfo=time.timezone('UTC')).strftime(self.FMT)

    def _toUnixMillis(self, from_date):
        past = datetime(1970, 1, 1, tzinfo=from_date.tzinfo)
        return int((from_date - past).total_seconds() * 1000.0)

    def _toDatetime(self, ms):
        return datetime.fromtimestamp(int(float(ms) / 1000.0))
