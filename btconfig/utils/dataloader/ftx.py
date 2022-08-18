from __future__ import division, absolute_import, print_function

from btconfig.utils.api.ftx import (
    FTXClient,
    create_data_df,
    create_funding_rates_df,
    list_futures_df,
)

import backtrader as bt
import pandas as pd


class FTXDataloaderApp:
    def __init__(self, api_key='', api_secret='', **kwargs):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = FTXClient(**kwargs)

    def getMarkets(self):
        '''
        :return pd.DataFrame | None:
        '''
        data = self.client.getMarkets()
        data_df = pd.DataFrame(data)
        return data_df

    def getMarketCandles(
        self, symbol, timeframe, compression, fromdate=None, todate=None
    ):
        '''
        :param symbol:
        :param timeframe:
        :param compression:
        :param fromdate:
        :param todate:

        :return pd.DataFrame | None:
        '''
        if (timeframe, compression) not in FTXClient.RESOLUTIONS:
            if timeframe != bt.TimeFrame.Days or (
                timeframe == bt.TimeFrame.Days and compression > 30
            ):
                raise Exception(
                    f'Unsupported ({timeframe}-{compression})'
                    ' granularity provided')
        if timeframe != bt.TimeFrame.Days:
            resolution = FTXClient.RESOLUTIONS[(timeframe, compression)]
        else:
            # for days, the resolution needs to be calculated manually:
            # 86400 * compression
            resolution = (
                FTXClient.RESOLUTIONS[(bt.TimeFrame.Days, 1)] * compression)
        fromdate_ts = None
        if fromdate:
            fromdate_ts = fromdate.timestamp()
        todate_ts = None
        if todate:
            todate_ts = todate.timestamp()
        data = self.client.getMarketCandles(
            symbol,
            start_time=fromdate_ts,
            end_time=todate_ts,
            resolution=resolution)
        if len(data):
            return create_data_df(data)
        return None

    def getAllFundingRates(self, fromdate=None, todate=None):
        '''
        :return pd.DataFrame | None:
        '''
        fromdate_ts = None
        if fromdate:
            fromdate_ts = fromdate.timestamp()
        todate_ts = None
        if todate:
            todate_ts = todate.timestamp()
        data = self.client.getAllFundingRates(
            start_time=fromdate_ts, end_time=todate_ts)
        data_df = create_funding_rates_df(data)
        return data_df

    def getFundingRates(self, future=None, fromdate=None, todate=None):
        '''
        :param future:
        :param fromdate:
        :param todate:

        :return pd.DataFrame | None:
        '''
        fromdate_ts = None
        if fromdate:
            fromdate_ts = fromdate.timestamp()
        todate_ts = None
        if todate:
            todate_ts = todate.timestamp()
        data = self.client.getFundingRates(future, fromdate_ts, todate_ts)
        data_df = create_funding_rates_df(data)
        return data_df

    def listFuturesInfo(self, type=None) -> pd.DataFrame:
        '''
        Returns a df of all the available futures info
        types: perpetual, future, prediction, move
        '''

        data = self.client.listFuturesInfo()
        df = list_futures_df(data, type)

        return df
