from __future__ import division, absolute_import, print_function

from btconfig import BTConfigApiClient


class CoinMarketCapClient(BTConfigApiClient):

    def __init__(self, api_key, **kwargs):
        self.api_key = api_key
        super(CoinMarketCapClient, self).__init__(
            base_url='https://pro-api.coinmarketcap.com',
            headers={'X-CMC_PRO_API_KEY': api_key},
            **kwargs)

    def getCryptoList(self):
        path = '/v1/cryptocurrency/map'
        response = self._request(path, exceptions=True, json=True)
        return response['data']

    def getExchangeList(self):
        path = '/v1/exchange/map'
        response = self._request(path, exceptions=True, json=True)
        return response['data']
