from __future__ import division, absolute_import, print_function
import pandas as pd

from dateutil import parser

from btconfig.utils.api import CoinMetricsClient


class CoinMetricsDownloadApp:

    def __init__(self, api_key):
        self.client = CoinMetricsClient(api_key)

    def download(self, filename, symbol, timeframe, compression, from_date,
                 to_date):
        """
        :param filename:
        :param symbol:
        :param timeframe:
        :param compression:
        :param from_date:
        :param to_date:
        :return:
        """
        if (timeframe, compression) not in CoinMetricsClient.FREQUENCY:
            raise Exception(
                f'Unsupported ({timeframe}-{compression})'
                + ' granularity provided')
        frequency = CoinMetricsClient.FREQUENCY[(timeframe, compression)]
        try:
            data = pd.read_csv(filename)
            data_len = len(data)
            from_date = parser.parse(data.iloc[-1].time, ignoretz=True)
        except IOError:
            data_len = 0

        from_date_str = from_date.strftime(CoinMetricsClient.FMT)
        to_date_str = None
        if to_date:
            to_date_str = to_date.strftime(CoinMetricsClient.FMT)
        data = self.client.getMarketCandles(
            symbol, from_date_str, to_date_str, frequency)
        data_df = create_data_df(data)
        # if first line then output also headers
        if data_len == 0:
            data_df.to_csv(filename, index=False)
        else:
            data_df[1:].to_csv(filename, header=None,
                               index=False, mode='a')


def create_data_df(data):
    res = pd.DataFrame(data)
    res.time = pd.to_datetime(res.time)
    for c in ['price_open', 'price_close', 'price_high',
              'price_low', 'volume']:
        res[c] = pd.to_numeric(res[c])
    res.rename(
        columns={'price_open': 'open', 'price_close': 'close',
                 'price_high': 'high', 'price_low': 'low'},
        inplace=True)
    res.drop(columns=['market', 'vwap'], inplace=True)
    return res[['time', 'open', 'high', 'low', 'close', 'volume']]
