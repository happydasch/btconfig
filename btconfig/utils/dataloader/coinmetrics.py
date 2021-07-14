from __future__ import division, absolute_import, print_function

from btconfig.utils.api.coinmetrics import (
    CoinMetricsClient,
    CoinMetricsDataClient,
    create_data_df,
    create_metrics_df,
    create_traditionaldata_df,
    get_market_parts)


class CoinMetricsDataloaderApp:

    def __init__(self, **kwargs):
        self.client = CoinMetricsClient(**kwargs)

    def request(self, symbol, timeframe, compression, fromdate,
                todate, add_mvrv=False, use_base_asset=True):
        '''
        :param symbol:
        :param timeframe:
        :param compression:
        :param fromdate:
        :param todate:
        :param add_mvrv:
        :param use_base_asset:
        :return pd.DataFrame | None:
        '''
        if (timeframe, compression) not in CoinMetricsClient.FREQUENCY:
            raise Exception(
                f'Unsupported ({timeframe}-{compression})'
                + ' granularity provided')
        frequency = CoinMetricsClient.FREQUENCY[(timeframe, compression)]
        fromdate_str = None
        if fromdate:
            fromdate_str = fromdate.strftime(CoinMetricsClient.FMT)
        todate_str = None
        if todate:
            todate_str = todate.strftime(CoinMetricsClient.FMT)
        data = self.client.getMarketCandles(
            symbol, fromdate_str, todate_str, frequency)
        data_df = create_data_df(data)
        if add_mvrv:
            metrics_cols = {'CapMrktCurUSD': 'mv',
                            'CapRealUSD': 'rv',
                            'CapMVRVCur': 'mvrv'}
            exchange, base_asset, quote_asset, type = get_market_parts(symbol)
            metrics = self.client.getAssetMetrics(
                base_asset if use_base_asset else quote_asset,
                ','.join(metrics_cols.keys()))
            metrics_df = create_metrics_df(metrics, metrics_cols)
            metrics_df.set_index('datetime', inplace=True)
            # update data with metrics values
            start = min(
                data_df.datetime.iloc[-1],
                max(data_df.datetime.iloc[0], metrics_df.index[0]))
            end = min(data_df.datetime.iloc[-1], metrics_df.index[-1])
            if start <= end:
                for c in metrics_cols.values():
                    values = metrics_df.loc[start:end, c].values
                    data_df.loc[data_df[data_df.datetime == start].index[0]:
                                data_df[data_df.datetime == end].index[0], c] = values
        return data_df


class CoinMetricsDataDataloaderApp:

    def __init__(self, **kwargs):
        self.client = CoinMetricsDataClient(**kwargs)

    def request(self, symbol, timeframe, compression, fromdate, todate):
        '''
        :param symbol:
        :param timeframe:
        :param compression:
        :param fromdate:
        :param todate:
        :return pd.DataFrame | None:
        '''
        if (timeframe, compression) not in CoinMetricsClient.FREQUENCY:
            raise Exception(
                f'Unsupported ({timeframe}-{compression})'
                + ' granularity provided')
        data = getattr(self.client, f'get{symbol}')()
        data_df = create_traditionaldata_df(data)
        data_df.set_index('datetime', inplace=True)
        data_df = data_df.loc[fromdate:]
        if todate:
            data_df = data_df.loc[:todate]
        return data_df.reset_index()
