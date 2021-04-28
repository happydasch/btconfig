from __future__ import division, absolute_import, print_function

from dateutil import parser
from urllib.parse import urlencode

from btconfig.parts.data import get_data_params
from btconfig.feeds.csv import CSVAdjustTime
from btconfig.utils.date import parse_dt

import backtrader as bt
import numpy as np
import pandas as pd

import os
import time
import logging
import requests
import btconfig


class CoinAPIDownload(btconfig.BTConfigDataloader):

    FMT = "%Y-%m-%dT%H:%M:%S"  # e.g. 2016-01-01T00:00:00

    '''
    https://docs.coinapi.io/#list-all-periods
    Second 	1SEC, 2SEC, 3SEC, 4SEC, 5SEC, 6SEC, 10SEC, 15SEC, 20SEC, 30SEC
    Minute 	1MIN, 2MIN, 3MIN, 4MIN, 5MIN, 6MIN, 10MIN, 15MIN, 20MIN, 30MIN
    Hour 	1HRS, 2HRS, 3HRS, 4HRS, 6HRS, 8HRS, 12HRS
    Day 	1DAY, 2DAY, 3DAY, 5DAY, 7DAY, 10DAY
    Month 	1MTH, 2MTH, 3MTH, 4MTH, 6MTH
    Year 	1YRS, 2YRS, 3YRS, 4YRS, 5YRS
    '''

    PERIODS = {
        # 1SEC, 2SEC, 3SEC, 4SEC, 5SEC, 6SEC, 10SEC, 15SEC, 20SEC, 30SEC
        (bt.TimeFrame.Seconds, 1): '1SEC', (bt.TimeFrame.Seconds, 2): '2SEC',
        (bt.TimeFrame.Seconds, 3): '3SEC', (bt.TimeFrame.Seconds, 4): '4SEC',
        (bt.TimeFrame.Seconds, 5): '5SEC', (bt.TimeFrame.Seconds, 6): '6SEC',
        (bt.TimeFrame.Seconds, 10): '10SEC', (bt.TimeFrame.Seconds, 15): '15SEC',
        (bt.TimeFrame.Seconds, 20): '20SEC', (bt.TimeFrame.Seconds, 30): '30SEC',
        # 1MIN, 2MIN, 3MIN, 4MIN, 5MIN, 6MIN, 10MIN, 15MIN, 20MIN, 30MIN
        (bt.TimeFrame.Minutes, 1): '1MIN', (bt.TimeFrame.Minutes, 2): '2MIN',
        (bt.TimeFrame.Minutes, 3): '3MIN', (bt.TimeFrame.Minutes, 4): '4MIN',
        (bt.TimeFrame.Minutes, 5): '5MIN', (bt.TimeFrame.Minutes, 6): '6MIN',
        (bt.TimeFrame.Minutes, 10): '10MIN', (bt.TimeFrame.Minutes, 15): '15MIN',
        (bt.TimeFrame.Minutes, 20): '20MIN', (bt.TimeFrame.Minutes, 30): '30MIN',
        # 1HRS, 2HRS, 3HRS, 4HRS, 6HRS, 8HRS, 12HRS
        (bt.TimeFrame.Minutes, 60): '1HRS', (bt.TimeFrame.Minutes, 120): '2HRS',
        (bt.TimeFrame.Minutes, 180): '3HRS', (bt.TimeFrame.Minutes, 240): '4HRS',
        (bt.TimeFrame.Minutes, 360): '6HRS', (bt.TimeFrame.Minutes, 480): '8HRS',
        (bt.TimeFrame.Minutes, 720): '12HRS',
        # 1DAY, 2DAY, 3DAY, 5DAY, 7DAY, 10DAY
        (bt.TimeFrame.Days, 1): '1DAY', (bt.TimeFrame.Days, 2): '2DAY',
        (bt.TimeFrame.Days, 3): '3DAY', (bt.TimeFrame.Days, 5): '5DAY',
        (bt.TimeFrame.Days, 7): '7DAY', (bt.TimeFrame.Days, 10): '10DAY',
        # 1MTH, 2MTH, 3MTH, 4MTH, 6MTH
        (bt.TimeFrame.Months, 1): '1MTH', (bt.TimeFrame.Months, 2): '2MTH',
        (bt.TimeFrame.Months, 3): '3MTH', (bt.TimeFrame.Months, 4): '4MTH',
        (bt.TimeFrame.Months, 6): '6MTH',
        # 1YRS, 2YRS, 3YRS, 4YRS, 5YRS
        (bt.TimeFrame.Years, 1): '1YRS'
    }

    def prepare(self):
        self.api_key = self._cfg.get('api_key', '')
        self.headers = {'X-CoinAPI-Key': self.api_key}
        self.url = 'https://rest.coinapi.io/v1/ohlcv/%s/history?'

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
        filename = 'COINAPI_{}_{}_{}_{}_{}_{}.csv'.format(
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
        if (timeframe, compression) not in self.PERIODS:
            gran = self._cfg['granularity']
            raise Exception(
                f'Unsupported ({gran[0]}-{gran[1]}) granularity provided')
        # download data into csv file
        if not fromdate or not todate or not os.path.isfile(filename):
            self._download(
                filename, dataname, self.PERIODS[(timeframe, compression)],
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

    def _download(self, filename, symbol, period, from_date, to_date, pause=-1):
        """
        :param filename:
        :param symbol:
        :param period:
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

        count = 0
        while True:
            params = {
                'limit': 1000,
                'period_id': period,
                'time_start': from_date.strftime(self.FMT)
            }
            if to_date:
                params['time_end'] = to_date.strftime(self.FMT)
            # download data
            self.log(f'Fetching coinAPI historical data for {symbol}'
                     + f' {from_date} ({count + 1})', logging.DEBUG)
            url = self.url % symbol + urlencode(params)

            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
            else:
                print(f'Invalid response code {response.status_code} recieved')
                data = []
            if len(data) > 0:
                data_df = pd.DataFrame(data)
            else:
                break
            data_df['time_period_start'] = pd.to_datetime(data_df['time_period_start'])
            for x in ['time_period_end', 'time_open', 'time_close', 'trades_count']:
                del data_df[x]
            data_df.rename(
                columns={
                    'time_period_start': 'time', 'price_open': 'open', 'price_high': 'high',
                    'price_low': 'low', 'price_close': 'close', 'volume_traded': 'volume'}, 
                inplace=True)

            # if first line then output also headers
            if data_len == 0:
                data_df.to_csv(filename, index=False)
            else:
                data_df[1:].to_csv(filename, header=None,
                                   index=False, mode='a')
            data_len += len(data_df)

            # check for exit
            if to_date and from_date >= to_date:
                break
            if from_date == data_df.iloc[-1].time:
                break
            # move to next step of batches
            from_date = data_df.iloc[-1].time
            count = count + 1
            if pause == -1:
                pause = np.random.randint(2, 5)
            time.sleep(pause)
