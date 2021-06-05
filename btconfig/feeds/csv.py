from __future__ import division, absolute_import, print_function

import backtrader as bt

from datetime import timedelta, timezone
from backtrader.utils import date2num
from btconfig.helper import get_starttime


class CSVAdjustTime(bt.feeds.GenericCSVData):

    params = dict(
        adjstarttime=False,
        datetime=0, time=-1, open=1, high=2, low=3,
        close=4, volume=5, openinterest=-1
    )

    def _loadline(self, linetokens):
        res = super(CSVAdjustTime, self)._loadline(linetokens)
        # ensure that utc time is being used
        dt = self.datetime.datetime(0, tz=timezone.utc)
        if self.p.adjstarttime:
            # move time to start time of next candle
            # and subtract 0.1 miliseconds (ensures no
            # rounding issues, 10 microseconds is minimum)
            new_date = get_starttime(
                self._timeframe, self._compression, dt,
                self.p.sessionstart, -1)
            new_date -= timedelta(microseconds=100)
            self.datetime[0] = date2num(new_date)
        else:
            self.datetime[0] = date2num(dt)
        return res


class CSVBidAskAdjustTime(CSVAdjustTime):

    lines = ('mid_close', 'bid_close', 'ask_close',)

    params = dict(
        mid_close=5, bid_close=6, ask_close=7,
        volume=8
    )


class CSVMVRVData(CSVAdjustTime):

    lines = ('mv', 'rv', 'mvrv')
    params = dict(
        dtformat='%Y-%m-%d %H:%M:%S%z',
        datetime=0, time=-1, open=1, high=2, low=3,
        close=4, volume=5, openinterest=-1,
        mv=6, rv=7, mvrv=8
    )
