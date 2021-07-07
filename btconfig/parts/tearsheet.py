from __future__ import division, absolute_import, print_function

import btconfig
import os
import pandas as pd
import quantstats as qs
import yfinance as yf
from bokeh.util.browser import view


class PartTearsheet(btconfig.BTConfigPart):

    PRIORITY = 110

    def setup(self) -> None:
        commoncfg = self._instance.config.get('common', {})
        if commoncfg.get('create_tearsheet', False):
            ccerebro = self._instance.cerebro
            ccerebro.addanalyzer(btconfig.analyzers.CashMarket)

    def finish(self, result) -> None:
        commoncfg = self._instance.config.get('common', {})
        path = commoncfg.get('report_path', './backtest')

        if not commoncfg.get('create_tearsheet', False):
            return
        for r in result:
            if isinstance(r, list):
                r = r.pop()
            params = r.p._getkwargs()
            filename = os.path.abspath(path)
            filename = os.path.join(filename, 'tearsheet_{}_{}_{}.html'.format(
                commoncfg.get('strategy'),
                '_'.join([str(x) for x in params.values()]),
                commoncfg.get('time').strftime('%Y%m%d_%H%M%S')))
            title = commoncfg.get('strategy')
            create_tearsheet(r, filename, title)
            view(filename)


def create_tearsheet(result, filename, title, bm=None):
   
    '''
    Creates a tearsheet from result

    Source:
    https://community.backtrader.com/topic/3987/skewness-kurtosis-of-returns/4
   '''

    # Get the stats auto ordered nested dictionary
    value = result.analyzers.getbyname('cashmarket').get_analysis()

    columns = ['Date', 'Cash', 'Value']

    # Save tearsheet
    df = pd.DataFrame(value)
    df = df.T
    df = df.reset_index()
    df.columns = columns

    df_value = df.set_index('Date')['Value']
    df_value.index = pd.to_datetime(df_value.index)
    df_value = df_value.sort_index()
    value_returns = qs.utils.to_returns(df_value)
    value_returns = pd.DataFrame(value_returns)

    value_returns['diff'] = value_returns['Value'].diff().dropna()
    value_returns['diff'] = value_returns['diff'].abs().cumsum()
    value_returns = value_returns.loc[value_returns['diff'] > 0, 'Value']
    value_returns.index = pd.to_datetime(value_returns.index.date)

    benchmark = None
    if bm:
        df_benchmark = yf.download(
            bm,
            start=value_returns.index[0],
            end=value_returns.index[-1],
            auto_adjust=True,
        )['Close']

        df_benchmark = qs.utils.rebase(df_benchmark)
        benchmark = qs.utils.to_returns(df_benchmark)
        benchmark.name = bm
        benchmark.index = pd.to_datetime(benchmark.index.date)

    try:
        qs.reports.html(
            value_returns,
            benchmark=benchmark,
            title=title,
            output=filename,
        )
    except:
        pass
