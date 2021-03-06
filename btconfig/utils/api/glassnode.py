from __future__ import division, absolute_import, print_function

import backtrader as bt
import pandas as pd

from btconfig import BTConfigApiClient


class GlassnodeClient(BTConfigApiClient):

    '''
    Glassnode Client

    https://docs.glassnode.com/api/
    '''

    INTERVALS = {
        (bt.TimeFrame.Minutes, 60): '1h',
        (bt.TimeFrame.Days, 1): '24h'
    }

    def __init__(self, api_key, **kwargs):
        self.api_key = api_key
        super(GlassnodeClient, self).__init__(
            base_url='https://api.glassnode.com/v1/',
            **kwargs)

    def _request(self, path, exceptions=True, json=False, **kwargs):
        kwargs['api_key'] = self.api_key
        return super()._request(
            path, exceptions=exceptions, json=json, **kwargs)

    def getIndicator(self, ind, asset, since='', until='', interval=''):
        path = f'metrics/indicators/{ind}'
        kwargs = {'a': asset, 's': since, 'u': until, 'i': interval}
        res = self._request(path, json=True, **kwargs)
        return res


def create_indicator_df(data):
    if data is None:
        return
    res = pd.DataFrame(data)
    res['t'] = pd.to_datetime(res['t'], unit='s')
    res['v'] = pd.to_numeric(res['v'])
    res.rename(
        columns={'t': 'datetime', 'v': 'close'},
        inplace=True)
    return res[['datetime', 'close']]
