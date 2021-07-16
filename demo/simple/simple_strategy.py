from btconfig.proto import ForexProtoStrategy
import backtrader as bt


class SimpleStrategy(ForexProtoStrategy):

    params = dict(
        period1=9,
        period2=26,
        revert_pos=True
    )

    def __init__(self):
        super(SimpleStrategy, self).__init__()
        self.data_primary = self.getdatabyname('primary')
        self.sma_p1 = bt.ind.SMA(
            self.data_primary, period=self.p.period1)
        self.sma_p2 = bt.ind.SMA(
            self.data_primary, period=self.p.period2)
        self.cross = bt.ind.CrossOver(
            self.sma_p1, self.sma_p2)
        self.lastlen = -1
        self.order = None

    def notify_order(self, order):
        if order.alive():
            return
        if self.order and order.ref == self.order.ref:
            self.log_order(order)
            self.order = None

    def notify_trade(self, trade):
        self.log_trade(trade)

    def next(self):
        self.log_candle(data=self.data_primary)
        if self.lastlen == len(self.data_primary):
            return
        self.lastlen = len(self.data_primary)
        if not self.datastatus:
            return
        if self.order:
            return

        pos = self.getposition()
        close = False
        sell = False
        buy = False

        if pos.size != 0:
            if pos.size > 0 and self.cross[0] < 0:
                close = True
            elif pos.size < 0 and self.cross[0] > 0:
                close = True
        if pos.size == 0 or (self.p.revert_pos and close):
            if self.cross[0] > 0:
                buy = True
            elif self.cross[0] < 0:
                sell = True

        if close:
            self.order = self.close()
        if sell:
            self.order = self.sell()
        if buy:
            self.order = self.buy()
