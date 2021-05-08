from __future__ import division, absolute_import, print_function
import pandas as pd

from dateutil import parser

from btconfig.utils.api import CoinMetricsClient


class CoinMetricsDownloadApp:

    def __init__(self, api_key):
        self.client = CoinMetricsClient(api_key)

    def download(self, filename, symbol, timeframe, compression, from_date,
                 to_date, add_mvrv=False, use_base_asset=True):
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

        from_date_str = None
        if from_date:
            from_date_str = from_date.strftime(CoinMetricsClient.FMT)
        to_date_str = None
        if to_date:
            to_date_str = to_date.strftime(CoinMetricsClient.FMT)
        data = self.client.getMarketCandles(
            symbol, from_date_str, to_date_str, frequency)
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
                data_df.loc[data_df[data_df.time == start].index[0]
                            :data_df[data_df.time == end].index[0], c] = metrics_df.loc[start:end, c].values
        # if first line then output also headers
        if data_len == 0:
            data_df.to_csv(filename, index=False)
        else:
            data_df[1:].to_csv(filename, header=None,
                               index=False, mode='a')


def get_mvrv_data(
        market,
        metrics_cols,
        use_base_asset=True):
    # mvrv can also be set this way: data['mvrv'] = data.mv / data.rv
    exchange, base_asset, quote_asset, type = get_market_parts(market)
    # get data
    data = get_data(market)
    metrics = get_metrics(
        base_asset if use_base_asset else quote_asset,
        metrics_cols)
    res = client.getAssetMetrics(assets=asset, metrics=','.join(
        metrics.keys()), start_time=start_time, end_time=end_time)
    metrics.set_index('time', inplace=True)
    # update data with metrics values
    start = max(data.time.iloc[0], metrics.index[0])
    end = min(data.time.iloc[-1], metrics.index[-1])
    for c in metrics_cols.values():
        data.loc[data[data.time == start].index[0]:data[data.time ==
                                                        end].index[0], c] = metrics.loc[start:end, c].values
    return data


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


def create_metrics_df(data, metrics_cols):
    res = pd.DataFrame(data)
    res.time = pd.to_datetime(res.time)
    for m in metrics_cols.keys():
        res[m] = pd.to_numeric(res[m])
    res.rename(columns=metrics_cols, inplace=True)
    res.drop(columns=['asset'], inplace=True)
    return res


def get_market_name(exchange='bitstamp', base='btc', quote='usd', type='spot'):
    market = f'{exchange}-{base}-{quote}-{type}'
    return market


def get_market_parts(market):
    exchange, base, quote, type = market.split('-')
    return exchange, base, quote, type
