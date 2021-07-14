from __future__ import division, absolute_import, print_function

import backtrader as bt
import pandas as pd

from btconfig import BTConfigApiClient


class CoinMetricsClient(BTConfigApiClient):

    '''
    CoinMetrics Client

    https://docs.coinmetrics.io/api
    '''

    FMT = "%Y-%m-%dT%H:%M:%S"  # e.g. 2016-01-01T00:00:00
    FREQUENCY = {
        (bt.TimeFrame.Days, 1): '1d'
    }

    def __init__(self, **kwargs):
        super(CoinMetricsClient, self).__init__(
            base_url='https://community-api.coinmetrics.io/v4/',
            **kwargs)

    def getAssetMetrics(
            self, assets, metrics, start_time=None, end_time=None,
            frequency='1d'):
        path = 'timeseries/asset-metrics'
        kwargs = {
            'assets': assets,
            'metrics': metrics,
            'page_size': 10000,
            'frequency': frequency}
        if start_time:
            kwargs['start_time'] = start_time
        if end_time:
            kwargs['end_time'] = end_time
        res = []
        url = self._getUrl(path, **kwargs)
        while True:
            response = self._requestUrl(url)
            if response.status_code == 200:
                tmp = response.json()
                if not len(tmp['data']):
                    break
                res += tmp['data']
                if 'next_page_url' in tmp:
                    url = tmp['next_page_url']
                    continue
            else:
                raise Exception(f'{response.url}: {response.text}')
            break
        return res

    def getMarketCandles(
            self, markets, start_time=None, end_time=None, frequency='1d'):
        path = 'timeseries/market-candles'
        kwargs = {
            'markets': markets,
            'page_size': 10000,
            'frequency': frequency}
        if start_time:
            kwargs['start_time'] = start_time
        if end_time:
            kwargs['end_time'] = end_time
        res = []
        url = self._getUrl(path, **kwargs)
        while True:
            response = self._requestUrl(url)
            if response.status_code == 200:
                tmp = response.json()
                if not len(tmp['data']):
                    break
                res += tmp['data']
                if 'next_page_url' in tmp:
                    url = tmp['next_page_url']
                    continue
            else:
                raise Exception(f'{response.url}: {response.text}')
            break
        return res

    def getAssets(self, assets=''):
        # Available assets
        path = 'catalog/assets'
        kwargs = {'assets': assets}
        res = self._request(
            path, exceptions=True, json=True, **kwargs)
        return res['data']

    def getPairs(self, pairs=''):
        # Available pairs
        path = 'catalog/pairs'
        kwargs = {'pairs': pairs}
        res = self._request(
            path, exceptions=True, json=True, **kwargs)
        return res['data']

    def getMetrics(self, metrics=''):
        # Available metrics
        path = 'catalog/metrics'
        kwargs = {'metrics': metrics}
        res = self._request(
            path, exceptions=True, json=True, **kwargs)
        return res['data']

    def getExchanges(self, exchanges=''):
        # Available exchanges
        path = 'catalog/exchanges'
        kwargs = {'exchanges': exchanges}
        res = self._request(
            path, exceptions=True, json=True, **kwargs)
        return res['data']

    def getMarkets(self, markets=''):
        # Available markets
        path = 'catalog/markets'
        kwargs = {'markets': markets}
        res = self._request(
            path, exceptions=True, json=True, **kwargs)
        return res['data']

    def getIndexes(self, indexes=''):
        # Available indexes
        path = 'catalog/indexes'
        kwargs = {'indexes': indexes}
        res = self._request(
            path, exceptions=True, json=True, **kwargs)
        return res['data']

    def getMarketCapitalization(self, assets):
        return self.getAssetMetrics(assets, 'CapMrktCurUSD')

    def getRealizedMarketCapitalization(self, assets):
        return self.getAssetMetrics(assets, 'CapRealUSD')

    def getMVRVRatio(self, assets):
        return self.getAssetMetrics(assets, 'CapMVRVCur')


class CoinMetricsDataClient(BTConfigApiClient):

    '''
    CoinMetrics Data Client
    '''

    def __init__(self, **kwargs):
        super(CoinMetricsDataClient, self).__init__(
            base_url='https://asset-data-proxy.coinmetrics.io/traditionalAssetData/v4/',
            **kwargs)

    def getLibor(self):  # Libor USD
        '''
        LIBOR USD
        metrics: ReferenceRateLondon1100am
        '''
        path = 'libor'
        return self._request(path, exceptions=True, json=True)['data']

    def getDollar(self):  # U.S. Dollar Index
        '''
        U.S. Dollar Index
        metrics: ReferenceRateNewYork1200pm
        '''
        path = 'dollar'
        return self._request(path, exceptions=True, json=True)['data']

    def getGold(self):  # Gold
        '''
        Gold
        metrics: ReferenceRateLondon1030am
        '''
        path = 'gold'
        return self._request(path, exceptions=True, json=True)['data']

    def getSP500(self):  # S&P 500
        '''
        S&P 500
        metrics: ReferenceRateNewYork0400pm
        '''
        path = 'sp500'
        return self._request(path, exceptions=True, json=True)['data']

    def getVix(self):  # CBOE Volatility Index
        '''
        CBOE Volatility Index
        metrics: ReferenceRateChicago0315pm
        '''
        path = 'vix'
        return self._request(path, exceptions=True, json=True)['data']


def create_data_df(data):
    if data is None:
        return
    res = pd.DataFrame(data)
    res['time'] = pd.to_datetime(res['time'])
    for c in ['price_open', 'price_close', 'price_high',
              'price_low', 'volume']:
        res[c] = pd.to_numeric(res[c])
    res.rename(
        columns={'price_open': 'open', 'price_close': 'close',
                 'price_high': 'high', 'price_low': 'low',
                 'time': 'datetime'},
        inplace=True)
    res.drop(columns=['market', 'vwap'], inplace=True)
    res['datetime'] = res['datetime'].dt.tz_localize(None)
    return res[['datetime', 'open', 'high', 'low', 'close', 'volume']]


def create_metrics_df(data, metrics_cols):
    if data is None:
        return
    res = pd.DataFrame(data)
    res['time'] = pd.to_datetime(res['time'])
    for m in metrics_cols.keys():
        res[m] = pd.to_numeric(res[m])
    res.rename(columns={'time': 'datetime'}, inplace=True)
    res.rename(columns=metrics_cols, inplace=True)
    res.drop(columns=['asset'], inplace=True)
    res['datetime'] = res['datetime'].dt.tz_localize(None)
    return res


def create_traditionaldata_df(data):
    if data is None:
        return
    res = pd.DataFrame(data)
    res['time'] = pd.to_datetime(res['time'])
    res['close'] = pd.to_numeric(res['PriceUSD'])
    res.rename(columns={'time': 'datetime'}, inplace=True)
    res.drop(columns=['asset', 'PriceUSD'], inplace=True)
    res['datetime'] = res['datetime'].dt.tz_localize(None)
    return res


def get_market_name(exchange='bitstamp', base='btc', quote='usd', type='spot'):
    market = f'{exchange}-{base}-{quote}-{type}'.lower()
    return market


def get_market_parts(market):
    exchange, base, quote, type = market.lower().split('-')
    return exchange, base, quote, type
