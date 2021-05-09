from __future__ import division, absolute_import, print_function

import time
import pytz
import numpy as np
import pandas as pd
import backtrader as bt

from datetime import datetime
from dateutil import parser
from binance.client import Client


class BinanceDownloadApp:

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

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = Client(self.api_key, self.api_secret)

    def download(self, filename, symbol, timeframe, compression,
                 from_date, to_date, pause=-1):
        """
        :param filename:
        :param symbol:
        :param timeframe:
        :param compression:
        :param from_date:
        :param to_date:
        :param pause: pause seconds before downloading next batch.
            if pause == -1 --> random sleep(2,5)
            if pause == 0 --> no sleep
            if pause == num--> sleep for num of seconds
        :return:
        """
        if (timeframe, compression) not in self.INTERVALS:
            raise Exception(
                f'Unsupported ({timeframe}-{compression})'
                + ' granularity provided')
        interval = self.INTERVALS[(timeframe, compression)]
        try:
            data = pd.read_csv(filename)
            data_len = len(data)
            from_date = parser.parse(data.iloc[-1].time, ignoretz=True)
        except IOError:
            data_len = 0
        from_millis = self._toUnixMillis(from_date)
        to_millis = None
        if to_date:
            to_millis = self._toUnixMillis(to_date)
        count = 0
        while True:
            klines = self.client.get_historical_klines(
                symbol, interval, str(from_millis), str(to_millis))
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
