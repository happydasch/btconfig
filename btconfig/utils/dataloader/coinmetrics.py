from __future__ import division, absolute_import, print_function

from btconfig.utils.api.coinmetrics import (
    CoinMetricsClient,
    create_data_df,
    create_metrics_df,
    get_market_parts)


class CoinMetricsDataloaderApp:

    def __init__(self, api_key):
        self.client = CoinMetricsClient(api_key)

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
            metrics_df.set_index('time', inplace=True)
            # update data with metrics values
            start = max(data_df.time.iloc[0], metrics_df.index[0])
            end = min(data_df.time.iloc[-1], metrics_df.index[-1])
            for c in metrics_cols.values():
                values = metrics_df.loc[start:end, c].values
                data_df.loc[data_df[data_df.time == start].index[0]:
                            data_df[data_df.time == end].index[0], c] = values
        return data_df
