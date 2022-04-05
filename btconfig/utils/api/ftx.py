from __future__ import division, absolute_import, print_function

from btconfig import BTConfigApiClient
from datetime import datetime

import backtrader as bt
import pandas as pd


class FTXClient(BTConfigApiClient):
    '''
    FTX Client

    https://docs.ftx.com/#overview
    '''
    RESOLUTIONS = {
        (bt.TimeFrame.Seconds, 15): 15,
        (bt.TimeFrame.Minutes, 1): 60,
        (bt.TimeFrame.Minutes, 5): 300,
        (bt.TimeFrame.Minutes, 15): 900,
        (bt.TimeFrame.Minutes, 60): 3600,
        (bt.TimeFrame.Minutes, 240): 14400,
        # 86400 or any multiple of 86400 up to 30*86400
        (bt.TimeFrame.Days, 1): 86400,
    }

    def __init__(self, **kwargs):
        # FIXME ftx uses authentification, see https://blog.ftx.com/blog/api-authentication/
        super(FTXClient, self).__init__(
            base_url='https://ftx.com/api/',
            headers={},
            **kwargs)

    def _requestUrl(self, url):
        # FIXME auth details can be added here
        return super(FTXClient, self)._requestUrl(url)

    def _requestPaginated(self, path, exceptions=False, **kwargs):
        '''
        Custom implementation of the request param for requests using pagination
        If no start_time and end_time is given only one request will be made
        will always return json
        '''
        res = []
        while True:
            url = self._getUrl(path, **kwargs)
            response = self._requestUrl(url)
            if response.status_code == 200:
                tmp = response.json()
                if not len(tmp['result']):
                    break
                if not len(res):
                    res = tmp['result']
                else:
                    # skip last entry if already fetched something
                    # to prevent double entries
                    res += tmp['result'][:-1]
                if isinstance(tmp['result'][-1]['time'], str):
                    last_dt = int(datetime.fromisoformat(tmp['result'][-1]['time']).timestamp())
                else:
                    last_dt = int(tmp['result'][-1]['time'] / 1000)
                if kwargs.get('start_time', 0) and kwargs.get('start_time', 0) >= last_dt:
                    break
                if kwargs.get('end_time', 0) and kwargs.get('end_time', 0) <= last_dt:
                    break
                if not kwargs.get('start_time') and not kwargs.get('end_time'):
                    break
                kwargs['end_time'] = last_dt
                continue
            else:
                if exceptions:
                    raise Exception(f'{response.url}: {response.text}')
            break
        return res

    def getMarketCandles(
            self, symbol, start_time=None, end_time=None, resolution=3600):
        # https://docs.ftx.com/#get-historical-prices
        path = f'markets/{symbol}/candles'
        kwargs = {'resolution': resolution}
        if end_time:
            kwargs['end_time'] = int(end_time)
        if start_time:
            kwargs['start_time'] = int(start_time)
        res = self._requestPaginated(path, **kwargs)
        return res

    def getAllFundingRates(self):
        # https://docs.ftx.com/#get-funding-rates
        return self.getFundingRates()

    def getFundingRates(self, future=None, start_time=None, end_time=None):
        # https://docs.ftx.com/#get-funding-rates
        path = 'funding_rates'
        kwargs = {}
        if future:
            kwargs['future'] = future
            if end_time:
                kwargs['end_time'] = int(end_time)
            if start_time:
                kwargs['start_time'] = int(start_time)
        res = self._requestPaginated(path, **kwargs)
        return res


def create_data_df(data):
    '''
    Market Data

    Creates and returns a DataFrame created from data (returned from api)

    Ex. format:
    [
        {'startTime': '2022-03-26T21:00:00+00:00', 'time': 1648328400000.0, 'open': 10.485, 'high': 10.521, 'low': 10.434, 'close': 10.519, 'volume': 204233.9143},
        {'startTime': '2022-03-26T22:00:00+00:00', 'time': 1648332000000.0, 'open': 10.519, 'high': 10.559, 'low': 10.515, 'close': 10.516, 'volume': 202234.9195},
        {'startTime': '2022-03-26T23:00:00+00:00', 'time': 1648335600000.0, 'open': 10.516, 'high': 10.654, 'low': 10.516, 'close': 10.634, 'volume': 884336.7059},
        ...
    ]
    '''
    if data is None:
        return
    res = pd.DataFrame(data)
    res['time'] = pd.to_datetime(res['time'], unit='ms')
    res.rename(columns={'time': 'datetime'}, inplace=True)
    res.drop(columns=['startTime'], inplace=True)
    res['datetime'] = res['datetime'].dt.tz_localize(None)
    return res


def create_funding_rates_df(data):
    '''
    Funding Rates

    Creates and returns a DataFrame created from data (returned from api)

    Ex. format:
    [
        {'future': 'UNI-PERP', 'rate': 4e-06, 'time': '2022-04-05T14:00:00+00:00'},
        {'future': 'UNI-PERP', 'rate': 1.4e-05, 'time': '2022-04-05T13:00:00+00:00'},
        {'future': 'UNI-PERP', 'rate': 3e-06, 'time': '2022-04-05T12:00:00+00:00'},
        ...
    ]
    '''
    if data is None:
        return
    res = pd.DataFrame(data)
    res['time'] = pd.to_datetime(res['time'])
    res.sort
    res.rename(columns={'time': 'datetime', 'rate': 'close'}, inplace=True)
    res['datetime'] = res['datetime'].dt.tz_localize(None)
    return res[['datetime', 'close', 'future']].sort_values(by='datetime')
