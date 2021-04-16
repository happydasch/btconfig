from __future__ import division, absolute_import, print_function

import btconfig

from .csv import CSVAdjustTime, CSVBidAskAdjustTime

from btoandav20.feeds import OandaV20Data


class OandaV20Download(btconfig.BTConfigDataloader):
    pass

"""

class FeedOandaV20(btconfig.BTConfigFeed):
    '''
    Creates a data source from Oanda V20

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
        - backfill_days (int): Default=0
        - fromdate (str): Default=null
        - todate (str): Default=null
        - bidask (bool): Default=true
        - useask (bool): Default=false
        - historical (bool): Default=false
        - adjstarttime (bool): Default=false

        Returns:
        --------
        bt.AbstractDataBase
    '''

    def create(self, cfg: dict, tz: str):
        pass


class FeedOandaV20Downloader(btconfig.BTConfigFeed):
    '''
    Creates a data source from Oanda V20 to csv

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
        - backfill_days (int): Default=0
        - fromdate (str): Default=null
        - todate (str): Default=null
        - bidask (bool): Default=true
        - useask (bool): Default=false
        - adjstarttime (bool): Default=false

        Returns:
        --------
        bt.AbstractDataBase
    '''

    def create(self, cfg: dict, tz: str):
        pass


def create_oandav20(cfg: dict, tz: str) -> bt.AbstractDataBase:
    '''
    Creates a data source from Oanda V20

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
        - backfill_days (int): Default=0
        - fromdate (str): Default=null
        - todate (str): Default=null
        - bidask (bool): Default=true
        - useask (bool): Default=false
        - historical (bool): Default=false
        - adjstarttime (bool): Default=false

        Returns:
        --------
        bt.AbstractDataBase
    '''
    timeframe = bt.TimeFrame.TFrame(cfg['granularity'][0])
    compression = cfg['granularity'][1]
    datakwargs = dict(
        dataname=cfg['name'],
        timeframe=timeframe,
        compression=compression,
        qcheck=0.25,
        tz=tz,
        sessionstart=time(
            cfg['sessionstart'][0],
            cfg['sessionstart'][1],
            cfg['sessionstart'][2],
            cfg['sessionstart'][3]),
        sessionend=time(
            cfg['sessionend'][0],
            cfg['sessionend'][1],
            cfg['sessionend'][2],
            cfg['sessionend'][3]))
    if (cfg['options'].get('backfill_days')
            and cfg['options'].get('backfill_days') > 0):
        # date for backfill start
        dt = datetime.now() - timedelta(
            days=cfg['options']['backfill_days'])
        datakwargs['fromdate'] = dt
        datakwargs['backfill_start'] = True
    elif cfg['options'].get('fromdate'):
        fromdate = iso8601.parse_date(
            cfg['options']['fromdate'],
            default_timezone=None)
        datakwargs['fromdate'] = fromdate
        if cfg['options'].get('todate'):
            todate = iso8601.parse_date(
                cfg['options']['todate'],
                default_timezone=None)
            datakwargs['todate'] = todate
            # with a todate, this is always historical
            datakwargs['historical'] = True
        datakwargs['backfill_start'] = True
    else:
        datakwargs['backfill_start'] = False
    datakwargs['bidask'] = cfg['options'].get('bidask', True)
    datakwargs['useask'] = cfg['options'].get('useask', False)
    datakwargs['adjstarttime'] = cfg['options'].get('adjstarttime', False)
    if cfg['options'].get('historical', False):
        datakwargs['historical'] = True

    log('Loading OANDA data {} - {} {}\n{}'.format(
        cfg['name'],
        compression,
        bt.TimeFrame.TName(timeframe),
        tabulate(datakwargs.items(), tablefmt='plain')
    ), logging.DEBUG)
    data = cstores['oandav20'].getdata(**datakwargs)
    return data


def create_oandav20_downloader(cfg: dict, tz: str) -> bt.AbstractDataBase:
    '''
    Creates a data source from Oanda V20 to csv

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
        - backfill_days (int): Default=0
        - fromdate (str): Default=null
        - todate (str): Default=null
        - bidask (bool): Default=true
        - useask (bool): Default=false
        - adjstarttime (bool): Default=false

        Returns:
        --------
        bt.AbstractDataBase
    '''
    bidask = cfg['options'].get('bidask', True)
    useask = cfg['options'].get('useask', False)
    if bidask and useask:
        ctype = 'ASK'
    elif bidask:
        ctype = 'BID'
    else:
        ctype = 'MID'
    fromdate = cfg['options'].get('fromdate', None)
    todate = cfg['options'].get('todate', None)
    backfill_days = cfg['options'].get('backfill_days', None)
    if backfill_days:
        fromdate = None
        todate = None
    filename = 'OANDA_CSV_DATA_{}_{}_{}_{}_{}_{}_{}.csv'.format(
        ctype,
        cfg['name'],
        cfg['granularity'][0],
        cfg['granularity'][1],
        fromdate,
        todate,
        backfill_days
    )
    timeframe = bt.TimeFrame.TFrame(cfg['granularity'][0])
    compression = cfg['granularity'][1]
    filename = os.path.join('data', filename)
    if backfill_days:
        dt = datetime.now() - timedelta(days=backfill_days)
        fromdate = dt.strftime(TIMEFORMAT)
    if not todate:
        todate = datetime.utcnow().strftime(TIMEFORMAT)
    sessionstart = time(
        cfg['sessionstart'][0],
        cfg['sessionstart'][1],
        cfg['sessionstart'][2],
        cfg['sessionstart'][3])
    sessionend = time(
        cfg['sessionend'][0],
        cfg['sessionend'][1],
        cfg['sessionend'][2],
        cfg['sessionend'][3])
    adjstarttime = cfg['options'].get('adjstarttime', False)

    log('Loading OANDA download data {} - {} {}'.format(
        cfg['name'],
        cfg['granularity'][1],
        cfg['granularity'][0]
    ), logging.DEBUG)
    # download data into csv file
    if not fromdate or not todate or not os.path.isfile(filename):
        app = OandaV20DownloadApp(
            cconfig['stores']['oandav20']['token'],
            cconfig['stores']['oandav20']['practice'])
        app.download(
            filename, cfg['name'], timeframe, compression,
            fromdate, todate, bidask, useask)
    # set csv file from download
    data = CSVBidAskAdjustTime(
        adjstarttime=adjstarttime,
        dataname=filename,
        nullvalue=0.0,
        headers=True,
        timeframe=timeframe,
        compression=compression,
        tz=tz,
        tzinput=tz,
        sessionstart=sessionstart,
        sessionend=sessionend,
        dtformat=parse_time)
    return data
"""
