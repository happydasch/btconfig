from __future__ import division, absolute_import, print_function

from btconfig.utils.api.coinapi import CoinApiClient, create_data_df


class CoinAPIDataloaderApp:

    def __init__(self, api_key, **kwargs):
        self.client = CoinApiClient(api_key, **kwargs)

    def request(self, symbol, timeframe, compression, fromdate, todate):
        '''
        :param symbol:
        :param timeframe:
        :param compression:
        :param fromdate:
        :param todate:
        :return pd.DataFrame | None:
        '''
        if (timeframe, compression) not in CoinApiClient.PERIODS:
            raise Exception(
                f'Unsupported ({timeframe}-{compression})'
                + ' granularity provided')
        period = CoinApiClient.PERIODS[(timeframe, compression)]
        fromdate_str = fromdate.strftime(CoinApiClient.FMT)
        todate_str = None
        if todate:
            todate_str = todate.strftime(CoinApiClient.FMT)
        data = self.client.getOHLCVHistory(
            symbol, period, fromdate_str,  todate_str)
        data_df = create_data_df(data)
        return data_df
