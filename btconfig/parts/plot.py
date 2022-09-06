from __future__ import division, absolute_import, print_function

import os
import logging
import btconfig
import backtrader as bt
import backtrader.plot.scheme as btplotscheme

from btplotting.schemes import Tradimo
from btplotting import (
    BacktraderPlotting, BacktraderPlottingLive,
    BacktraderPlottingOptBrowser)
from btplotting.tabs import AnalyzerTab, MetadataTab, ConfigTab, LogTab
from btconfig import (
    MODE_LIVE,  MODE_BACKTEST, MODE_OPTIMIZE, MODE_OPTIMIZEGENETIC,
    NUMBERFORMAT, TIMEFORMAT)


class PartPlot(btconfig.BTConfigPart):

    PRIORITY = 90

    def _prepare(self):
        self.btplotting = None
        self.plotfigs = None

    def setup(self):
        commoncfg = self._instance.config.get('common', {})
        if not commoncfg.get('create_plot', False):
            return

        if self._instance.mode == MODE_LIVE:
            self._createLivePlotting()
        self.log('Plotting configured\n', logging.INFO)

    def finish(self, result):
        commoncfg = self._instance.config.get('common', {})
        if not commoncfg.get('create_plot', False):
            return
        if not len(result):
            return
        if self._instance.mode == MODE_BACKTEST:
            self._createBacktestPlotting()
        elif self._instance.mode in [MODE_OPTIMIZE, MODE_OPTIMIZEGENETIC]:
            self._createOptimizePlotting(result)

    def _createLivePlotting(self):
        '''
        Live plotting configuration
        '''
        cfg = self._instance.config.get('plot', {})
        self._instance.cerebro.addanalyzer(
            BacktraderPlottingLive,
            lookback=cfg.get('live_lookback', 50),
            style=cfg.get('style', 'candle'),
            port=cfg.get('port', 80),
            use_default_tabs=False,
            tabs=[AnalyzerTab, ConfigTab],
            scheme=self._getBTPlottingScheme(self._getPlotscheme()))

    def _createBacktestPlotting(self):
        '''
        Backtest plotting configuration
        '''
        commoncfg = self._instance.config.get('common', {})
        path = commoncfg.get('report_path', './backtest')
        if not os.path.isdir(path):
            os.makedirs(path)
        plotcfg = self._instance.config.get('plot', {})
        # if plots should be combined, set up datafeeds
        if plotcfg.get('combine', False):
            for d in self._instance.cerebro.datas[1:]:
                d.plotinfo.plotmaster = self._instance.cerebro.datas[0]
        # create custom plot scheme if needed
        plotscheme = self._getPlotscheme()
        # plot
        if plotcfg.get('use', 'web') != 'web':
            res = self._instance.cerebro.plot(
                use=plotcfg.get('use', 'web'),
                style=plotcfg.get('style', 'candle'),
                scheme=plotscheme)
        else:
            kwargs = {}
            kwargs['style'] = plotcfg.get('style', 'candle')
            kwargs['use_default_tabs'] = False
            kwargs['tabs'] = [AnalyzerTab, MetadataTab, LogTab]
            kwargs['scheme'] = self._getBTPlottingScheme(plotscheme)
            output_file = os.path.abspath(path)
            output_file = os.path.join(output_file, 'bt_{}_{}.html'.format(
                commoncfg.get('strategy'),
                commoncfg.get('time').strftime(btconfig.FILE_TIMEFORMAT)))
            kwargs['filename'] = output_file
            kwargs['headline'] = f'Backtest {commoncfg.get("strategy")}'
            self.btplotting = BacktraderPlotting(**kwargs)
            res = self._instance.cerebro.plot(self.btplotting)
        self.plotfigs = res

    def _createOptimizePlotting(self, result):
        '''
        Optimization plotting configuration
        '''
        for i in result:
            if not len(i):
                return

        plotcfg = self._instance.config.get('plot', {})
        plotscheme = self._getPlotscheme()
        kwargs = {}
        kwargs['style'] = plotcfg.get('style', 'candle')
        kwargs['use_default_tabs'] = False
        kwargs['tabs'] = [AnalyzerTab, MetadataTab]
        kwargs['scheme'] = self._getBTPlottingScheme(plotscheme)
        self.btplotting = BacktraderPlotting(**kwargs)
        browser = BacktraderPlottingOptBrowser(
            self.btplotting,
            result,
            port=plotcfg.get('port', 80),
            autostart=plotcfg.get('autostart', True),
            usercolumns={'Profit & Loss': _analyzer_df},
            sortcolumn='Profit & Loss',
            sortasc=False)
        browser.start()

    def _getPlotscheme(self):
        '''
        Returns a plotscheme for backtrader
        '''
        plotcfg = self._instance.config.get('plot', {})
        scheme = btplotscheme.PlotScheme()
        scheme.number_format = NUMBERFORMAT
        if not plotcfg.get('volume', False):
            scheme.volume = False
        datas = self._instance.cerebro.datas
        if (len(datas) and datas[0]._timeframe == bt.TimeFrame.Ticks):
            scheme.volume = False
        return scheme

    def _getBTPlottingScheme(self, plotscheme):
        '''
        Returns a scheme for btplotting
        '''
        plotcfg = self._instance.config.get('plot', {})
        override = plotcfg.get('override', {})
        kwargs = dict(
            hovertool_timeformat=TIMEFORMAT,
            number_format=plotscheme.number_format,
            volume=plotscheme.volume,
            data_aspectratio=2.5,
            vol_aspectratio=5.5,
            obs_aspectratio=8.5,
            ind_aspectratio=11.5,
            xaxis_pos='bottom',
            plot_title=False
        )
        kwargs.update(override)
        scheme = Tradimo(**kwargs)
        return scheme


def _analyzer_df(optresults):
    '''
    Generates a custom df for optimiziation results
    '''
    a = [x.analyzers.TradeAnalyzer.get_analysis() for x in optresults]
    return sum([x.pnl.net.total if 'pnl' in x else 0 for x in a])
