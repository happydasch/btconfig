from __future__ import division, absolute_import, print_function

import logging

from tabulate import tabulate

import backtrader as bt

import btconfig
from btconfig import log, cconfig, cmode, MODE_OPTIMIZE
from btconfig.observers import BuySell
from btconfig.analyzers import TradeList
from btconfig.report import create_report


def setup_backtrader():
    '''
    Sets up backtrader functionality
    '''
    commoncfg = cconfig.get('common', {})
    if (commoncfg.get('create_plot', False)
            or commoncfg.get('create_report', False)):
        _add_observer()
        _add_analyzer()
    log('Backtrader created\n', logging.INFO)


def finish_backtrader(result):
    '''
    Finishes backtrader functionality with result
    '''
    commoncfg = cconfig.get('common', {})
    if commoncfg.get('create_report', False):
        for r in result:
            if isinstance(r, list):
                r = r.pop()
            params = r.p._getkwargs()
            report = create_report(
                r, r.cerebro.broker.startingcash)
            if cmode == MODE_OPTIMIZE:
                log('Optimize Instance Args: \n{}'.format(tabulate(
                    params.items(), tablefmt='plain')),
                    logging.DEBUG)
            log(report, logging.INFO)


def _add_observer():
    '''
    Adds observer to cerebro
    '''
    plotcfg = cconfig.get('plot', {})
    ccerebro = btconfig.cerebro
    ccerebro.addobserver(bt.observers.Broker)
    ccerebro.addobserver(bt.observers.Trades)
    ccerebro.addobserver(bt.observers.DrawDown)
    ccerebro.addobservermulti(
        BuySell,  # buy / sell arrows
        barplot=True,
        bardist=plotcfg.get('bar_dist', 0.001))


def _add_analyzer():
    '''
    Adds analyzer to cerebro
    '''
    analyzercfg = cconfig.get('analyzers', {})
    ccerebro = btconfig.cerebro
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
    ccerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='AnnualReturn')
    ccerebro.addanalyzer(bt.analyzers.DrawDown, _name='DrawDown')
    ccerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='TradeAnalyzer')
    ccerebro.addanalyzer(bt.analyzers.SQN, _name='SQN')
    ccerebro.addanalyzer(TradeList, _name='TradeList')
