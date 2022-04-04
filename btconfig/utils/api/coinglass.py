from __future__ import division, absolute_import, print_function

from btconfig import BTConfigApiClient

import pandas as pd


class CoinGlassClient(BTConfigApiClient):
    '''
    CoinGlass Client

    https://coinglass.github.io/API-Reference/
    '''

    def __init__(self, secret, **kwargs):
        self.secret = secret
        super(CoinGlassClient, self).__init__(
            base_url='https://open-api.coinglass.com/api/pro/v1/',
            headers={'coinglassSecret': secret},
            **kwargs)

    def getFundingRates(self, symbol, type='C'):
        path = 'futures/funding_rates_chart'
        kwargs = {
            'symbol': symbol,
            'type': type
        }
        rates = self._request(path, exceptions=True, json=True, **kwargs)
        return rates['data']


def create_funding_rates_df(data):
    df = pd.DataFrame()
    df['datetime'] = pd.to_datetime(data['dateList'], unit='ms')
    df['price'] = pd.to_numeric(data['priceList'])
    for d, d_cols in [['data', 'dataMap'], ['fr_data', 'frDataMap']]:
        cols = []
        for col in data[d_cols]:
            c_name = f'{d}_{col}'
            cols.append(c_name)
            df[c_name] = pd.Series(pd.to_numeric(data[d_cols][col]))
        df[d] = df[cols].mean(axis=1)
    return df
