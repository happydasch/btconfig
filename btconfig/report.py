from __future__ import division, absolute_import, print_function

from tabulate import tabulate

from btconfig.helper import sqn2rating


def create_report(result, startcash) -> str:
    '''
    Creates a report from backtest
    '''
    trade_list = result.analyzers.TradeList.get_analysis()
    annual_return = result.analyzers.AnnualReturn.get_analysis()
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

    txt.append('Annual Return')
    txt.append(tabulate(
        annual_return.items(),
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
