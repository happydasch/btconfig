from __future__ import division, absolute_import, print_function

import backtrader as bt

from datetime import timedelta, timezone
from btconfig.helper import get_starttime, parse_dt


class PandasAdjustTime(bt.feeds.PandasData):

    params = dict(
        adjstarttime=False,
        roundvalues=False,
        roundprecision=8,
        dtformat=parse_dt,
        datetime=0, open=1, high=2, low=3,
        close=4, volume=5, openinterest=-1,
    )

    def _load(self):
        res = super()._load()
        if self.p.roundvalues:
            for datafield in self.getlinealiases():
                if datafield == 'datetime':
                    continue
                colindex = self._colmapping[datafield]
                if colindex is None:
                    continue
                line = getattr(self.lines, datafield)
                if line[0] == line[0]:
                    line[0] = round(line[0], self.p.roundprecision)
        if self.datetime[0] == self.datetime[0]:
            dt = self.datetime.datetime(0, tz=timezone.utc)
            if self.p.adjstarttime:
                # move time to start time of next candle
                # and subtract 0.1 miliseconds (ensures no
                # rounding issues, 10 microseconds is minimum)
                new_date = get_starttime(
                    self._timeframe, self._compression, dt,
                    self.p.sessionstart, 1)
                new_date -= timedelta(microseconds=100)
                self.datetime[0] = bt.date2num(new_date)
            else:
                self.datetime[0] = bt.date2num(dt)
        return res


class CSVAdjustTime(bt.feeds.GenericCSVData):

    params = dict(
        adjstarttime=False,
        roundvalues=False,
        roundprecision=8,
        dtformat=parse_dt,
        datetime=0, open=1, high=2, low=3, close=4, volume=5,
        openinterest=-1
    )

    def _loadline(self, linetokens):
        res = super(CSVAdjustTime, self)._loadline(linetokens)
        # if values should be rounded, all lines will get rounded
        if self.p.roundvalues:
            for linefield in (x for x in self.getlinealiases() if x != 'datetime'):
                csvidx = getattr(self.params, linefield)
                if csvidx is None or csvidx < 0:
                    continue
                line = getattr(self.lines, linefield)
                if line[0] == line[0]:
                    line[0] = round(line[0], self.p.roundprecision)
        # ensure that utc time is being used
        dt = self.datetime.datetime(0, tz=timezone.utc)
        if self.p.adjstarttime:
            # move time to start time of next candle
            # and subtract 0.1 miliseconds (ensures no
            # rounding issues, 10 microseconds is minimum)
            new_date = get_starttime(
                self._timeframe, self._compression, dt,
                self.p.sessionstart, 1)
            new_date -= timedelta(microseconds=100)
            self.datetime[0] = bt.date2num(new_date)
        else:
            self.datetime[0] = bt.date2num(dt)
        return res


class CSVAdjustTimeCloseOnly(CSVAdjustTime):

    params = dict(
        datetime=0, open=1, high=1, low=1, close=1,
        volume=-1, openinterest=-1
    )


class CSVAdjustTimeBidAsk(CSVAdjustTime):

    lines = ('mid_close', 'bid_close', 'ask_close',)

    params = dict(
        mid_close=5, bid_close=6, ask_close=7, volume=8
    )


class CSVAdjustTimeMVRVData(CSVAdjustTime):

    lines = ('mv', 'rv', 'mvrv')
    params = dict(
        datetime=0, open=1, high=2, low=3, close=4, volume=5,
        mv=6, rv=7, mvrv=8, openinterest=-1
    )
