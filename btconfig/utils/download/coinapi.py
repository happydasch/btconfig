from __future__ import division, absolute_import, print_function

import pandas as pd

from dateutil import parser
from btconfig.utils.api.coinapi import CoinApiClient, create_data_df


class CoinAPIDownloadApp:

    def __init__(self, api_key):
        self.client = CoinApiClient(api_key)

    def download(self, filename, symbol, timeframe, compression, fromdate, todate):
        """
        :param filename:
        :param symbol:
        :param timeframe:
        :param compression:
        :param fromdate:
        :param todate:
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

        fromdate_str = from_date.strftime(CoinApiClient.FMT)
        todate_str = None
        if todate:
            todate_str = todate.strftime(CoinApiClient.FMT)
        data = self.client.getOHLCVHistory(
            symbol, period, fromdate_str,  todate_str)
        data_df = create_data_df(data)
        # if first line then output also headers
        if data_len == 0:
            data_df.to_csv(filename, index=False)
        else:
            data_df[1:].to_csv(filename, header=None,
                               index=False, mode='a')
