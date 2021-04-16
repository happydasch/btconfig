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
                self.sessionstart,
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



'''
class FeedCSV(btconfig.BTConfigFeed):
    '''
    Creates a data source from csv

        Args:
        -----
        - cfg (dict)
        - tz (str)

        Params:
        -------
        All default params are supported. Additionally custom
        options are available.

        Custom Options:
        ---------------
        - fromdate (str): null
        - todate (str): null
        - datetime (int): CSV Column datetime, Default=0
        - time (int): CSV Column time, Default=-1
        - open (int): CSV Column open, Default=1
        - high (int): CSV Column high, Default=2
        - low (int): CSV Column low, Default=3
        - close (int): CSV Column close, Default=4
        - volume (int): CSV Column volume, Default=5
        - openinterest (int): : CSV Column openinterest, Default=-1

        Returns:
        --------
        bt.AbstractDataBase
    '''

    def create(self, cfg: dict, tz: str):
        pass

"""
def create_csv(cfg: dict, tz: str) -> bt.AbstractDataBase:
    if cfg['granularity'][0] != 'Ticks':
        log('Loading CSV file {} - {} {}'.format(
            cfg['name'],
            cfg['granularity'][1],
            cfg['granularity'][0]
        ), logging.DEBUG)
        datakwargs = dict(
            adjstarttime=cfg['options'].get('adjstarttime', False),
            dataname='data/{}'.format(cfg['name']),
            nullvalue=0.0,
            headers=True,
            timeframe=bt.TimeFrame.TFrame(cfg['granularity'][0]),
            compression=cfg['granularity'][1],
            tz=tz,
            tzinput=tz,
            sessionstart=time(
                cfg['sessionstart'][0],
                cfg['sessionstart'][1],
                cfg['sessionstart'][2],
                cfg['sessionstart'][3]),
            sessionend=time(
                cfg['sessionend'][0],
                cfg['sessionend'][1],
                cfg['sessionend'][2],
                cfg['sessionend'][3]),
            dtformat=parse_time,
            datetime=cfg['options'].get('datetime', 0),
            time=cfg['options'].get('time', -1),
            open=cfg['options'].get('open', 1),
            high=cfg['options'].get('high', 2),
            low=cfg['options'].get('low', 3),
            close=cfg['options'].get('close', 4),
            volume=cfg['options'].get('volume', 5),
            openinterest=cfg['options'].get('openinterest', -1)
        )
        if cfg['options'].get('fromdate'):
            fromdate = iso8601.parse_date(
                cfg['options']['fromdate'],
                default_timezone=None)
            datakwargs['fromdate'] = fromdate
        if cfg['options'].get('todate'):
            todate = iso8601.parse_date(
                cfg['options']['todate'],
                default_timezone=None)
            datakwargs['todate'] = todate
        data = CSVAdjustTime(**datakwargs)
    else:
        log('Loading CSV file {} with Ticks'.format(cfg['name']),
            logging.DEBUG)
        datakwargs = dict(
            adjstarttime=cfg['options'].get('adjstarttime', False),
            dataname='data/{}'.format(cfg['name']),
            nullvalue=0.0, headers=True,
            timeframe=bt.TimeFrame.Ticks,
            tz=tz,
            tzinput=tz,
            sessionstart=time(
                cfg['sessionstart'][0],
                cfg['sessionstart'][1],
                cfg['sessionstart'][2],
                cfg['sessionstart'][3]),
            sessionend=time(
                cfg['sessionend'][0],
                cfg['sessionend'][1],
                cfg['sessionend'][2],
                cfg['sessionend'][3]),
            dtformat=parse_time,
            datetime=0, time=-1, open=3, high=3, low=3,
            close=3, mid_close=3, bid_close=2, ask_close=1,
            volume=-1, openinterest=-1
        )
        if cfg['options'].get('fromdate'):
            fromdate = iso8601.parse_date(
                cfg['options']['fromdate'],
                default_timezone=None)
            datakwargs['fromdate'] = fromdate
        if cfg['options'].get('todate'):
            todate = iso8601.parse_date(
                cfg['options']['todate'],
                default_timezone=None)
            datakwargs['todate'] = todate
        data = CSVBidAskAdjustTime(**datakwargs)
    return data
"""
