from __future__ import division, absolute_import, print_function
import pandas as pd

from dateutil import parser

from btconfig.utils.api import CoinApiClient


class CoinAPIDownloadApp:

    def __init__(self, api_key):
        self.client = CoinApiClient(api_key)

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
        if (timeframe, compression) not in CoinApiClient.PERIODS:
            raise Exception(
                f'Unsupported ({timeframe}-{compression})'
                + ' granularity provided')
        period = CoinApiClient.PERIODS[(timeframe, compression)]
        try:
            data = pd.read_csv(filename)
            data_len = len(data)
            from_date = parser.parse(data.iloc[-1].time, ignoretz=True)
        except IOError:
            data_len = 0

        from_date_str = from_date.strftime(CoinApiClient.FMT)
        to_date_str = None
        if to_date:
            to_date_str = to_date.strftime(CoinApiClient.FMT)
        data = self.client.getOHLCVHistory(
            symbol, period, from_date_str,  to_date_str)
        data_df = create_data_df(data)
        # if first line then output also headers
        if data_len == 0:
            data_df.to_csv(filename, index=False)
        else:
            data_df[1:].to_csv(filename, header=None,
                               index=False, mode='a')


def create_data_df(data):
    data_df = pd.DataFrame(data)
    data_df['time_period_start'] = pd.to_datetime(
        data_df['time_period_start'])
    data_df.drop(['time_period_end', 'time_open', 'time_close',
                  'trades_count'], inplace=True)
    data_df.rename(
        columns={
            'time_period_start': 'time', 'price_open': 'open',
            'price_high': 'high', 'price_low': 'low',
            'price_close': 'close', 'volume_traded': 'volume'},
        inplace=True)
    return data_df[['time', 'open', 'high', 'low', 'close', 'volume']]
