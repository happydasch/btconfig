from __future__ import division, absolute_import, print_function

import btconfig

from backtrader.feeds import IBData


class IBDownload(btconfig.BTConfigDataloader):

    def load(self):
        pass

"""

    '''
    Creates a data source from Interactive Brokers

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
        - rtbar (bool): Default=false
        - what (str): Default=MIDPOINT
        - useRTH (bool): Default=false
        - reconnect (int): Default=-1

        Returns:
        --------
        bt.AbstractDataBase
    '''

    def create(self, cfg: dict, tz: str):
        pass


class FeedIBDownloader(btconfig.BTConfigPart):
    '''
    Creates a data source from Interactive Brokers to csv

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
        - what (str): Default=MIDPOINT
        - useRTH (bool): Default=false
        - adjstarttime (bool): Default=false

        Returns:
        --------
        bt.AbstractDataBase
    '''

    def create(self, cfg: dict, tz: str):
        pass


def create_ib(cfg: dict, tz: str) -> bt.AbstractDataBase:
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
    if cfg['options'].get('historical', False):
        datakwargs['historical'] = True
    datakwargs['rtbar'] = cfg['options'].get('rtbar', False)
    datakwargs['what'] = cfg['options'].get('what', 'MIDPOINT')
    datakwargs['useRTH'] = cfg['options'].get('useRTH', False)
    datakwargs['reconnect'] = cfg['options'].get('reconnect', -1)
    log('Loading Interactive Brokers data {} - {} {}\n{}'.format(
        cfg['name'],
        compression,
        bt.TimeFrame.TName(timeframe),
        tabulate(datakwargs.items(), tablefmt='plain')
    ), logging.DEBUG)
    data = cstores['ib'].getdata(**datakwargs)
    return data


def create_ib_downloader(cfg: dict, tz: str) -> bt.AbstractDataBase:
    '''
    Creates a data source from Interactive Brokers to csv

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
        - what (str): Default=MIDPOINT
        - useRTH (bool): Default=false
        - adjstarttime (bool): Default=false

        Returns:
        --------
        bt.AbstractDataBase
    '''
    what = cfg['options'].get('what', 'MIDPOINT')
    fromdate = cfg['options'].get('fromdate', None)
    todate = cfg['options'].get('todate', None)
    backfill_days = cfg['options'].get('backfill_days', None)
    if backfill_days:
        fromdate = None
        todate = None
    filename = 'IB_CSV_DATA_{}_{}_{}_{}_{}_{}_{}.csv'.format(
        what,
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
    useRTH = cfg['options'].get('useRTH', False)

    log('Loading Interactive Brokers download data {} - {} {}'.format(
        cfg['name'],
        cfg['granularity'][1],
        cfg['granularity'][0]
    ), logging.DEBUG)
    # download data into csv file
    if not fromdate or not todate or not os.path.isfile(filename):
        app = IBDownloadApp(
            cconfig['stores']['ib']['host'],
            cconfig['stores']['ib']['port'],
            cconfig['stores']['ib']['clientId'])
        app.download(
            filename, cfg['name'], timeframe, compression,
            fromdate, todate, what, useRTH)

    # set csv file from download
    data = CSVAdjustTime(
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
    # return data
    return data
"""
