from __future__ import division, absolute_import, print_function

import hmac
import pandas as pd
import backtrader as bt

from datetime import datetime
from requests import Request

from btconfig import BTConfigApiClient


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

    def __init__(self, api_key='', api_secret='', **kwargs):
        self.api_key = api_key
        self.api_secret = api_secret
        super(FTXClient, self).__init__(
            base_url='https://ftx.com/api/', headers={}, **kwargs
        )

    def _request(self, path, exceptions=True, json=False,
                 authenticate=False, **kwargs):
        '''
        Runs a request to the given api path
        '''
        url = self._getUrl(path, **kwargs)
        response = self._requestUrl(url, authenticate=authenticate)
        if response.status_code == 200:
            if json:
                return response.json()
        else:
            if exceptions:
                raise Exception(f'{url}: {response.text}')
            if json:
                return []
        return response

    def _requestUrl(self, url, authenticate=False):
        if not authenticate:
            response = super(FTXClient, self)._requestUrl(url)
        else:
            ts = int(datetime.utcnow().timestamp() * 1000)
            request = Request('GET', url)
            prepared = request.prepare()
            signature_payload = f'{ts}{prepared.method}{prepared.path_url}'
            if prepared.body:
                signature_payload += prepared.body
            signature_payload = signature_payload.encode()
            signature = hmac.new(
                self.api_secret.encode(),
                signature_payload,
                'sha256').hexdigest()
            request.headers = self.headers.copy()
            request.headers['FTX-KEY'] = self.api_key
            request.headers['FTX-SIGN'] = signature
            request.headers['FTX-TS'] = str(ts)
            response = request.get(url, headers=request.headers)
        return response

    def getMarkets(self):
        # https://docs.ftx.com/#get-markets
        path = 'markets'
        response = self._request(path, json=True)
        return response['result']

    def getMarketCandles(self, symbol, start_time=None, end_time=None,
                         resolution=3600):
        # https://docs.ftx.com/#get-historical-prices
        path = f'markets/{symbol}/candles'
        kwargs = {'resolution': resolution}
        if start_time:
            kwargs['start_time'] = int(start_time)
        if end_time:
            kwargs['end_time'] = int(end_time)
        res = []
        while True:
            response = self._request(path, **kwargs)
            if response.status_code != 200:
                raise Exception(f'{response.url}: {response.text}')
            tmp = response.json()
            if not len(tmp['result']):
                break
            first_dt = int(tmp['result'][0]['time'] / 1000)
            last_dt = int(tmp['result'][-1]['time'] / 1000)
            if not len(res):
                res = tmp['result']
            else:
                # if data did not move backwards don't continue
                if (first_dt == int(res[0]['time'] / 1000)):
                    break
                res = tmp['result'][:-1] + res
            if not start_time and not end_time:
                break
            if start_time and start_time >= first_dt:
                break
            if start_time and start_time < first_dt:
                kwargs['end_time'] = first_dt
                prev_first_dt = first_dt
            else:
                break
        return res

    def getAllFundingRates(self, start_time=None, end_time=None):
        # https://docs.ftx.com/#get-funding-rates
        return self.getFundingRates(start_time=start_time, end_time=end_time)

    def getFundingRates(self, future=None, start_time=None, end_time=None):
        # https://docs.ftx.com/#get-funding-rates
        path = 'funding_rates'
        kwargs = {}
        if future:
            kwargs['future'] = future
        if start_time:
            kwargs['start_time'] = int(start_time)
        if end_time:
            kwargs['end_time'] = int(end_time)
        res = []
        while True:
            response = self._request(path, **kwargs)
            if response.status_code != 200:
                raise Exception(f'{response.url}: {response.text}')
            tmp = response.json()
            if not len(tmp['result']):
                break
            first_dt = int(datetime.fromisoformat(
                tmp['result'][-1]['time']).timestamp())
            if not len(res):
                res = tmp['result']
            else:
                if (first_dt == int(datetime.fromisoformat(
                        res[-1]['time']).timestamp())):
                    break
                for i in tmp['result']:
                    if i['time'] == res[0]['time']:
                        continue
                    res.append(i)
            if not kwargs.get('start_time') and not kwargs.get('end_time'):
                break
            if (kwargs.get('start_time')
                    and kwargs.get('start_time', 0) >= first_dt):
                break
            if first_dt > kwargs.get('start_time', first_dt):
                kwargs['end_time'] = first_dt
            else:
                break
        return res

    def listFuturesInfo(self):
        '''
        https://docs.ftx.com/#futures
        retrieve info for all avaialable futures
        '''
        path = 'futures'
        response = self._request(path, json=True)
        return response['result']


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
    if not data:
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
    if not data:
        return
    res = pd.DataFrame(data)
    res['time'] = pd.to_datetime(res['time'])
    res.rename(columns={'time': 'datetime', 'rate': 'close'}, inplace=True)
    res['datetime'] = res['datetime'].dt.tz_localize(None)
    return res[['datetime', 'close', 'future']].sort_values(
        by='datetime', ignore_index=True)


def list_futures_df(data, type=None) -> pd.DataFrame:
    '''
    Returns a df of all the available futures info
    types: perpetual, future, prediction, move
    '''
    if not data:
        return

    df = pd.DataFrame.from_dict(data)
    df.set_index('name', inplace=True)

    if type is not None:
        df = df[df['type'] == type]

    return df
