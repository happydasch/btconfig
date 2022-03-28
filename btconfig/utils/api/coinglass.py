from __future__ import division, absolute_import, print_function

from btconfig import BTConfigApiClient


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
