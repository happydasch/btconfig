from __future__ import division, absolute_import, print_function

import pandas as pd

from btconfig import BTConfigApiClient


class CoinGeckoClient(BTConfigApiClient):

    '''
    CoinGecko Client

    API rate limit of 100 calls per minute - if
    you exceed that limit you will be blocked
    until the next 1 minute window. Do revise
    your queries to ensure that you do not
    exceed our limits should that happen.

    https://www.coingecko.com/en/api#explore-api
    '''

    def __init__(self, **kwargs):
        super(CoinGeckoClient, self).__init__(
            base_url='https://api.coingecko.com/api/v3',
            **kwargs)

    def getCoinsList(self):
        path = '/coins/list'
        coins = self._request(path, exceptions=True, json=True)
        return coins

    def getCoinsMarkets(self, vs_currency='usd', coin_ids=''):
        path = '/coins/markets'
        kwargs = {
            'vs_currency': vs_currency,
            'ids': coin_ids,
            'page': 1,
            'per_page': 250
        }
        coins = []
        while True:
            tmp = self._request(
                path, exceptions=True, json=True, **kwargs)
            if not len(tmp):
                break
            coins.extend(tmp)
            kwargs['page'] += 1
        return coins

    def getCoinsTickers(self, id, exchange_ids=''):
        path = f'/coins/{id}/tickers'
        kwargs = {
            'exchange_ids': exchange_ids,
            'page': 1
        }
        tickers = []
        while True:
            tmp = self._request(
                path, exceptions=True, json=True, **kwargs)
            if not len(tmp):
                break
            if 'tickers' not in tmp or not len(tmp['tickers']):
                break
            tickers.extend(tmp['tickers'])
            kwargs['page'] += 1
        return tickers

    def getCoinsHistory(self, coin_id, date, localization=False):
        path = f'/coins/{coin_id}/history'
        kwargs = {
            'date': date,
            'localization': 'false' if not localization else 'true'
        }
        history = self._request(path, exceptions=True, json=True, **kwargs)
        return history

    def getCoinsMarketChart(self, coin_id, vs_currency, days):
        path = f'/coins/{coin_id}/market_chart'
        kwargs = {
            'vs_currency': vs_currency,
            'days': days
        }
        mchart = self._request(path, exceptions=True, json=True, **kwargs)
        return mchart

    def getCoinsMarketChartRange(self, coin_id, vs_currency, date_from, date_to):
        # date: timestamp ex: 1422577232
        path = f'/coins/{coin_id}/market_chart/range'
        kwargs = {
            'vs_currency': vs_currency,
            'from': date_from,
            'to': date_to
        }
        mchart = self._request(path, exceptions=True, json=True, **kwargs)
        return mchart

    def getExchanges(self):
        path = '/exchanges'
        exchanges = self._request(path, exceptions=True, json=True)
        return exchanges

    def getExchangeTickers(self, exchange_id, coin_id=''):
        path = f'/exchanges/{exchange_id}/tickers'
        kwargs = {
            'coin_ids': coin_id,
            'page': 1
        }
        tickers = []
        while True:
            tmp = self._request(
                path, exceptions=True, json=True, **kwargs)
            if 'tickers' not in tmp or not len(tmp['tickers']):
                break
            tickers.extend(tmp['tickers'])
            kwargs['page'] += 1
        return tickers

    def getIndexes(self):
        path = '/indexes'
        indexes = self._request(path, exceptions=True, json=True)
        return indexes

    def getGlobal(self):
        path = '/global'
        glob = self._request(path, exceptions=True, json=True)
        return glob


def create_metrics_df(data, metrics_cols):
    if data is None:
        return
    tmp = {}
    df = None
    for x in metrics_cols.keys():
        tmp = pd.DataFrame(data[x])
        tmp.rename(columns={0: 'datetime', 1: x}, inplace=True)
        if df is None:
            df = tmp
        else:
            df[x] = tmp[x]
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    for m in metrics_cols.keys():
        df[m] = pd.to_numeric(df[m])
    df.rename(columns=metrics_cols, inplace=True)
    df['datetime'] = df['datetime'].dt.tz_localize(None)
    return df
