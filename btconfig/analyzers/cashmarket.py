import btconfig
import backtrader as bt


class CashMarket(bt.analyzers.Analyzer):

    '''
    CashMarket Analyzer

    Source:
    https://community.backtrader.com/topic/2506/how-to-create-pyfolio-round-trip-tearsheet/16?_=1625412035950
    '''

    def start(self):
        super(CashMarket, self).start()

    def create_analysis(self):
        self.rets = {}
        self.vals = 0.0

    def notify_cashvalue(self, cash, value):
        self.vals = (cash, value)
        self.rets[self.strategy.datetime.datetime().strftime(
            "%Y-%m-%d")] = self.vals

    def get_analysis(self):
        return self.rets
