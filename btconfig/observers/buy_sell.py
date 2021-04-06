import backtrader as bt


class BuySell(bt.observers.BuySell):
    plotlines = dict(
        buy=dict(marker=6, markersize=12.0),
        sell=dict(marker=7, markersize=12.0)
    )
