from __future__ import division, absolute_import, print_function

from btconfig.utils.api.ftx import (
    FTXClient, create_data_df, create_funding_rates_df)

import backtrader as bt


class FTXDataloaderApp:

    def __init__(self, **kwargs):
        self.client = FTXClient(**kwargs)

    def getMarketCandles(self, symbol, timeframe, compression,
                         fromdate=None, todate=None):
        '''
        :param symbol:
        :param timeframe:
        :param compression:
        :param fromdate:
        :param todate:

        :return pd.DataFrame | None:
        '''
        if (timeframe, compression) not in FTXClient.RESOLUTIONS:
            if (timeframe != bt.TimeFrame.Days or (
                    timeframe == bt.TimeFrame.Days and compression > 30)):
                raise Exception(
                    f'Unsupported ({timeframe}-{compression})'
                    + ' granularity provided')
        if timeframe != bt.TimeFrame.Days:
            resolution = FTXClient.RESOLUTIONS[(timeframe, compression)]
        else:
            # for days, the resolution needs to be calculated manually:
            # 86400 * compression
            resolution = (FTXClient.RESOLUTIONS[(bt.TimeFrame.Days, 1)]
                          * compression)
        fromdate_ts = None
        if fromdate:
            fromdate_ts = fromdate.timestamp()
        todate_ts = None
        if todate:
            todate_ts = todate.timestamp()
        data = self.client.getMarketCandles(
            symbol, start_time=fromdate_ts, end_time=todate_ts,
            resolution=resolution)
        data_df = create_data_df(data)
        return data_df

    def getAllFundingRates(self):
        '''
        :return pd.DataFrame | None:
        '''
        data = self.client.getAllFundingRates()
        data_df = create_funding_rates_df(data)
        return data_df

    def getFundingRates(self, future, fromdate=None, todate=None):
        '''
        :param future:
        :param fromdate:
        :param todate:

        :return pd.DataFrame | None:
        '''
        fromdate_ts = fromdate.timestamp()
        todate_ts = None
        if todate:
            todate_ts = todate.timestamp()
        data = self.client.getFundingRates(future, fromdate_ts, todate_ts)
        data_df = create_funding_rates_df(data)
        return data_df
