from __future__ import division, absolute_import, print_function

import backtrader as bt
from tabulate import tabulate

import logging
import btconfig

from btconfig.helper import sqn2rating
from btconfig.observers import BuySell
from btconfig.analyzers import TradeList


class PartBacktrader(btconfig.BTConfigPart):

    PRIORITY = 30

    def setup(self) -> None:
        commoncfg = self._instance.config.get('common', {})
        if (commoncfg.get('create_plot', False)
                or commoncfg.get('create_report', False)):
            self._addObserver()
            self._addAnalyzer()
        self.log('Backtrader configured\n', logging.INFO)

    def finish(self, result) -> None:
        commoncfg = self._instance.config.get('common', {})
        if commoncfg.get('create_report', False):
            for r in result:
                if isinstance(r, list):
                    r = r.pop()
                params = r.p._getkwargs()
                report = create_report(r, r.cerebro.broker.startingcash)
                if self._instance.mode == btconfig.MODE_OPTIMIZE:
                    self.log('Optimize Instance Args:\n{}'.format(tabulate(
                        params.items(), tablefmt='plain')),
                        logging.DEBUG)
                if report:
                    self.log(report, logging.INFO)

    def _addObserver(self) -> None:
        plotcfg = self._instance.config.get('plot', {})
        ccerebro = self._instance.cerebro
        ccerebro.addobserver(bt.observers.Broker)
        ccerebro.addobserver(bt.observers.Trades)
        ccerebro.addobserver(bt.observers.DrawDown)
        ccerebro.addobservermulti(
            BuySell,  # buy / sell arrows
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


def create_report(result, startcash) -> str:
    '''
    Creates a report from backtest
    '''
    trade_list = result.analyzers.TradeList.get_analysis()
    trade_analysis = result.analyzers.TradeAnalyzer.get_analysis()
    drawdown = result.analyzers.DrawDown.get_analysis()
    sqn = result.analyzers.SQN.get_analysis()['sqn']
    # load the following analyzer only if available
    time_return = None
    if 'TimeReturn' in result.analyzers._names:
        time_return = result.analyzers.TimeReturn.get_analysis()
    sharpe = None
    if 'Sharpe' in result.analyzers._names:
        sharpe = result.analyzers.Sharpe.get_analysis()['sharperatio']

    if 'pnl' not in trade_analysis:
        return 'No PnL, empty report\n'

    txt = []

    txt.append('')
    txt.append('Trade List')
    txt.append(tabulate(trade_list, headers='keys', tablefmt='simple'))
    txt.append('')

    if time_return:
        txt.append('Time Return')
        txt.append(tabulate(
            time_return.items(),
            headers=['time', 'return'],
            tablefmt='fancy_grid'))
        txt.append('')

    rpl = trade_analysis.pnl.net.total
    total_return = rpl / startcash
    total_number_trades = trade_analysis.total.total
    trades_closed = trade_analysis.total.closed

    kpi_pnl = [
        ['rpl (RPL)', rpl],
        ['result_won_trades', trade_analysis.won.pnl.total],
        ['result_lost_trades', trade_analysis.lost.pnl.total],
        ['profit_factor (PF)', (trade_analysis.won.pnl.total / max(
            1, abs(trade_analysis.lost.pnl.total)))],
        ['gain_to_pain (GtPR)', rpl / max(
            1, abs(trade_analysis.lost.pnl.total))],
        ['rpl_per_trade', rpl / max(1, trades_closed)],
        ['total_return', total_return],
        ['money_drawdown', drawdown.moneydown],
        ['pct_drawdown (DD)', drawdown.drawdown],
        ['max_money_drawdown', drawdown.max.moneydown],
        ['max_pct_drawdown (DD)', drawdown.max.drawdown]
    ]
    txt.append('PnL')
    txt.append(tabulate(kpi_pnl, tablefmt='fancy_grid'))
    txt.append('')

    kpi_trades = [
        ['total_number_trades', total_number_trades],
        ['trades_closed', trades_closed],
        ['pct_winning', (100 * trade_analysis.won.total) / max(
            1, trades_closed)],
        ['pct_losing', (100 * trade_analysis.lost.total) / max(
            1, trades_closed)],
        ['avg_money_winning', trade_analysis.won.pnl.average],
        ['avg_money_losing',  trade_analysis.lost.pnl.average],
        ['best_winning_trade', trade_analysis.won.pnl.max],
        ['worst_losing_trade', trade_analysis.lost.pnl.max],
        ['longest_win_streak', trade_analysis.streak.won.longest],
        ['longest_lose_streak', trade_analysis.streak.lost.longest]
    ]
    txt.append('Trades')
    txt.append(tabulate(kpi_trades, tablefmt='fancy_grid'))
    txt.append('')

    kpi_perf = [
        ['sqn_score', sqn],
        ['sqn_human', sqn2rating(sqn)]
    ]
    if sharpe:
        kpi_perf.append(['sharpe_ratio (SR)', sharpe])
    txt.append('Performance')
    txt.append(tabulate(kpi_perf, tablefmt='fancy_grid'))
    txt = '\n'.join(txt)

    return txt
