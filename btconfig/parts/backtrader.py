from __future__ import division, absolute_import, print_function

import logging
import btconfig
import backtrader as bt

from btconfig.helper import get_classes
from btconfig.observers import BuySellMarker
from btconfig.analyzers import TradeList


class PartBacktrader(btconfig.BTConfigPart):

    PRIORITY = 30

    def setup(self) -> None:
        commoncfg = self._instance.config.get('common', {})
        if commoncfg.get('add_observer', False):
            self._addObserver()
        if commoncfg.get('add_analyzer', False):
            self._addAnalyzer()
        self.log('Backtrader configured\n', logging.INFO)

    def _addObserver(self) -> None:
        plotcfg = self._instance.config.get('plot', {})
        ccerebro = self._instance.cerebro
        ccerebro.addobserver(bt.observers.Broker)
        ccerebro.addobserver(bt.observers.Trades)
        ccerebro.addobserver(bt.observers.DrawDown)
        ccerebro.addobservermulti(
            BuySellMarker,  # buy / sell arrows
            barplot=True,
            bardist=plotcfg.get('bar_dist', 0.001))

    def _addAnalyzer(self) -> None:
        analyzercfg = self._instance.config.get('analyzers', {})
        ccerebro = self._instance.cerebro
        cfg = analyzercfg.get('time_return')
        if cfg:
            ccerebro.addanalyzer(
                bt.analyzers.TimeReturn,
                timeframe=bt.TimeFrame.TFrame(cfg[0]),
                compression=cfg[1],
                _name='TimeReturn')
        cfg = analyzercfg.get('sharpe_ratio')
        if cfg:
            ccerebro.addanalyzer(
                bt.analyzers.SharpeRatio,
                riskfreerate=0,
                timeframe=bt.TimeFrame.TFrame(cfg[0]),
                compression=cfg[1],
                factor=cfg[2],
                annualize=cfg[3],
                _name='Sharpe')
        ccerebro.addanalyzer(bt.analyzers.DrawDown, _name='DrawDown')
        ccerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='TradeAnalyzer')
        ccerebro.addanalyzer(bt.analyzers.SQN, _name='SQN')
        ccerebro.addanalyzer(TradeList, _name='TradeList')

        # Add Custom Analyzers
        all_classes = get_classes(self._instance.PATH_ANALYZER)
        for analyzer_name, params in analyzercfg.items():
            if analyzer_name not in ['sharpe_ratio', 'time_return', 'DrawDown', 'TradeAnalyzer', 'TradeList']:
                if analyzer_name not in all_classes:
                    raise Exception(f'Analyzer {analyzer_name} not found configured PATH_ANALYZER directory paths')
                params = dict({'_name': analyzer_name}, **params)
                ccerebro.addanalyzer(all_classes[analyzer_name], **params)
