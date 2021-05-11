from __future__ import division, absolute_import, print_function

import backtrader as bt
import pandas as pd

from btconfig import BTConfigApiClient


class CoinApiClient(BTConfigApiClient):

    '''
    CoinAPI Client

    https://docs.coinapi.io/
    '''

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
        (bt.TimeFrame.Seconds, 1): '1SEC',
        (bt.TimeFrame.Seconds, 2): '2SEC',
        (bt.TimeFrame.Seconds, 3): '3SEC',
        (bt.TimeFrame.Seconds, 4): '4SEC',
        (bt.TimeFrame.Seconds, 5): '5SEC',
        (bt.TimeFrame.Seconds, 6): '6SEC',
        (bt.TimeFrame.Seconds, 10): '10SEC',
        (bt.TimeFrame.Seconds, 15): '15SEC',
        (bt.TimeFrame.Seconds, 20): '20SEC',
        (bt.TimeFrame.Seconds, 30): '30SEC',
        # 1MIN, 2MIN, 3MIN, 4MIN, 5MIN, 6MIN, 10MIN, 15MIN, 20MIN, 30MIN
        (bt.TimeFrame.Minutes, 1): '1MIN',
        (bt.TimeFrame.Minutes, 2): '2MIN',
        (bt.TimeFrame.Minutes, 3): '3MIN',
        (bt.TimeFrame.Minutes, 4): '4MIN',
        (bt.TimeFrame.Minutes, 5): '5MIN',
        (bt.TimeFrame.Minutes, 6): '6MIN',
        (bt.TimeFrame.Minutes, 10): '10MIN',
        (bt.TimeFrame.Minutes, 15): '15MIN',
        (bt.TimeFrame.Minutes, 20): '20MIN',
        (bt.TimeFrame.Minutes, 30): '30MIN',
        # 1HRS, 2HRS, 3HRS, 4HRS, 6HRS, 8HRS, 12HRS
        (bt.TimeFrame.Minutes, 60): '1HRS',
        (bt.TimeFrame.Minutes, 120): '2HRS',
        (bt.TimeFrame.Minutes, 180): '3HRS',
        (bt.TimeFrame.Minutes, 240): '4HRS',
        (bt.TimeFrame.Minutes, 360): '6HRS',
        (bt.TimeFrame.Minutes, 480): '8HRS',
        (bt.TimeFrame.Minutes, 720): '12HRS',
        # 1DAY, 2DAY, 3DAY, 5DAY, 7DAY, 10DAY
        (bt.TimeFrame.Days, 1): '1DAY',
        (bt.TimeFrame.Days, 2): '2DAY',
        (bt.TimeFrame.Days, 3): '3DAY',
        (bt.TimeFrame.Days, 5): '5DAY',
        (bt.TimeFrame.Days, 7): '7DAY',
        (bt.TimeFrame.Days, 10): '10DAY',
        # 1MTH, 2MTH, 3MTH, 4MTH, 6MTH
        (bt.TimeFrame.Months, 1): '1MTH',
        (bt.TimeFrame.Months, 2): '2MTH',
        (bt.TimeFrame.Months, 3): '3MTH',
        (bt.TimeFrame.Months, 4): '4MTH',
        (bt.TimeFrame.Months, 6): '6MTH',
        # 1YRS, 2YRS, 3YRS, 4YRS, 5YRS
        (bt.TimeFrame.Years, 1): '1YRS'
    }

    def __init__(self, api_key, debug=False):
        self.api_key = api_key
        super(CoinApiClient, self).__init__(
            base_url='https://rest.coinapi.io',
            headers={'X-CoinAPI-Key': api_key},
            debug=debug)

    def getOHLCVHistory(self, symbol, period, time_start, time_end=None):
        path = f'/v1/ohlcv/{symbol}/history'
        res = []
        while True:
            kwargs = {
                'limit': 1000,
                'period_id': period,
                'time_start': time_start
            }
            if time_end:
                kwargs['time_end'] = time_end
            response = self._request(path, exceptions=True, **kwargs)
            if response.status_code == 200:
                tmp = response.json()
                if not len(tmp):
                    break
                res.extend(tmp)
                time_start = tmp[-1]['time_period_end']
                continue
            else:
                raise Exception(f'{response.url}: {response.text}')
        return res

    def getExchanges(self):
        path = '/v1/exchanges'
        exchanges = self._request(path, exceptions=True, json=True)
        return exchanges

    def getAssets(self):
        path = '/v1/exchanges'
        assets = self._request(path, exceptions=True, json=True)
        return assets

    def getSymbols(self):
        path = '/v1/symbols'
        symbols = self._request(path, exceptions=True, json=True)
        return symbols


def create_data_df(data):
    if data is None:
        return
    data_df = pd.DataFrame(data)
    data_df['time_period_start'] = pd.to_datetime(
        data_df['time_period_start'])
    data_df.drop(['time_period_end', 'time_open', 'time_close',
                  'trades_count'], inplace=True)
    data_df.rename(
        columns={
            'time_period_start': 'time', 'price_open': 'open',
            'price_high': 'high', 'price_low': 'low',
            'price_close': 'close', 'volume_traded': 'volume'},
        inplace=True)
    for i in ['open', 'high', 'low', 'close', 'volume']:
        data_df[i] = pd.to_numeric(data_df[i])
    return data_df[['time', 'open', 'high', 'low', 'close', 'volume']]
