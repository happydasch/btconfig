from __future__ import division, absolute_import, print_function

from datetime import timedelta
import backtrader as bt
from backtrader.utils import date2num
from btconfig.utils.date import getstarttime


class CSVAdjustTime(bt.feeds.GenericCSVData):

    params = dict(
        adjstarttime=False,
        datetime=0, time=-1, open=1, high=2, low=3,
        close=4, volume=5, openinterest=-1
    )

    def _loadline(self, linetokens):
        res = super(CSVAdjustTime, self)._loadline(linetokens)
        if self.p.adjstarttime:
            # move time to start time of next candle
            # and subtract 0.1 miliseconds (ensures no
            # rounding issues, 10 microseconds is minimum)
            new_date = getstarttime(
                self._timeframe,
                self._compression,
                self.datetime.datetime(0),
                self.p.sessionstart,
                -1) - timedelta(microseconds=100)
            self.datetime[0] = date2num(new_date)
        else:
            self.datetime[0] = date2num(self.datetime.datetime(0))
        return res


class CSVBidAskAdjustTime(CSVAdjustTime):

    lines = ('mid_close', 'bid_close', 'ask_close',)

    params = dict(
        mid_close=5, bid_close=6, ask_close=7,
        volume=8
    )
