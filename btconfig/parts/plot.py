from __future__ import division, absolute_import, print_function

import os

import backtrader as bt
import backtrader.plot.scheme as btplotscheme

from btplotting.schemes import Tradimo
from btplotting import (
    BacktraderPlotting, BacktraderPlottingLive,
    BacktraderPlottingOptBrowser)

from btplotting.tabs import AnalyzerTab, MetadataTab, ConfigTab, LogTab

import logging

import btconfig
from btconfig import (
    log, cconfig, cmode,
    MODE_LIVE,  MODE_BACKTEST, MODE_OPTIMIZE,
    NUMBERFORMAT, TIMEFORMAT)


def setup_plot():
    '''
    Sets up plotting functionality
    '''
    commoncfg = cconfig.get('common', {})
    if not commoncfg.get('create_plot', False):
        return

    if cmode == MODE_LIVE:
        _create_live_plotting()
    log('Plotting configured\n', logging.INFO)


def finish_plot(result):
    '''
    Finishes plotting functionality with result
    '''
    commoncfg = cconfig.get('common', {})
    if not commoncfg.get('create_plot', False):
        return

    if cmode == MODE_BACKTEST:
        _create_backtest_plotting()
    elif cmode == MODE_OPTIMIZE:
        _create_optimize_plotting(result)


def _create_live_plotting():
    '''
    Live plotting configuration
    '''
    cfg = cconfig.get('plot', {})
    btconfig.cerebro.addanalyzer(
        BacktraderPlottingLive,
        lookback=cfg.get('live_lookback', 50),
        style=cfg.get('style', 'candle'),
        http_port=cfg.get('web_port',  80),
        use_default_tabs=False,
        tabs=[AnalyzerTab, MetadataTab, ConfigTab, LogTab],
        scheme=_get_btplotting_scheme(_get_plotscheme()))


def _create_backtest_plotting():
    '''
    Backtest plotting configuration
    '''
    commoncfg = cconfig.get('common', {})
    plotcfg = cconfig.get('plot', {})
    # if plots should be combined, set up datafeeds
    if plotcfg.get('combine', False):
        for d in btconfig.cerebro.datas[1:]:
            d.plotinfo.plotmaster = btconfig.cerebro.datas[0]
    # create custom plot scheme if needed
    plotscheme = _get_plotscheme()
    # plot
    if plotcfg.get('use', 'web') != 'web':
        btconfig.cerebro.plot(
            use=plotcfg.get('use'),
            style=plotcfg.get('style'),
            scheme=plotscheme)
    else:
        kwargs = {}
        kwargs['style'] = plotcfg.get('style')
        kwargs['http_port'] = plotcfg.get('web_port')
        kwargs['use_default_tabs'] = False
        kwargs['tabs'] = [AnalyzerTab, MetadataTab, LogTab]
        kwargs['scheme'] = _get_btplotting_scheme(plotscheme)
        output_file = plotcfg.get('path', './backtest')
        output_file = os.path.abspath(output_file)
        output_file = os.path.join(output_file, 'bt_{}_{}.html'.format(
            commoncfg.get('strategy'),
            commoncfg.get('time').strftime('%Y%m%d_%H%M%S')))
        kwargs['filename'] = output_file
        btconfig.cerebro.plot(BacktraderPlotting(**kwargs))


def _create_optimize_plotting(result):
    '''
    Optimization plotting configuration
    '''
    for i in result:
        if not len(i):
            return

    plotcfg = cconfig.get('plot', {})
    plotscheme = _get_plotscheme()
    kwargs = {}
    kwargs['style'] = plotcfg.get('style')
    kwargs['http_port'] = plotcfg.get('web_port')
    kwargs['use_default_tabs'] = False
    kwargs['tabs'] = [AnalyzerTab, MetadataTab]
    kwargs['scheme'] = _get_btplotting_scheme(plotscheme)
    btp = BacktraderPlotting(**kwargs)
    browser = BacktraderPlottingOptBrowser(
        btp,
        result,
        usercolumns={'Profit & Loss': _analyzer_df},
        sortcolumn='Profit & Loss',
        sortasc=False)
    browser.start()


def _analyzer_df(optresults):
    '''
    Generates a custom df for optimiziation  results
    '''
    a = [x.analyzers.TradeAnalyzer.get_analysis() for x in optresults]
    return sum([x.pnl.gross.total if 'pnl' in x else 0 for x in a])


def _get_plotscheme():
    '''
    Returns a plotscheme for backtrader
    '''
    plotcfg = cconfig.get('plot', {})
    scheme = btplotscheme.PlotScheme()
    scheme.number_format = NUMBERFORMAT
    if not plotcfg.get('plot_volume', False):
        scheme.volume = False
    datas = btconfig.cerebro.datas
    if (len(datas) and datas[0]._timeframe == bt.TimeFrame.Ticks):
        scheme.volume = False
    return scheme


def _get_btplotting_scheme(plotscheme):
    '''
    Returns a scheme for btplotting
    '''
    scheme = Tradimo(
        hovertool_timeformat=TIMEFORMAT,
        number_format=plotscheme.number_format,
        volume=plotscheme.volume,
        data_aspectratio=2.5,
        vol_aspectratio=5.5,
        obs_aspectratio=8.5,
        ind_aspectratio=11.5,
        xaxis_pos='bottom',
        plot_title=False)
    return scheme
