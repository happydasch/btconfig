from __future__ import division, absolute_import, print_function

import btconfig

#from ccxtbt.ccxtfeed import CCXTFeed


class FeedCCXT(btconfig.BTConfigFeed):
    '''
    Creates a data source from ccxt

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
        - historical (bool): Default=false
        - config = {'urls': {'api': 'https://testnet.bitmex.com'},
                    'apiKey': apikey,
                    'secret': secret,
                    'enableRateLimit': enableRateLimit,
                    }
        - ohlcv_limit
        - fetch_ohlcv_params {}

        Returns:
        --------
        bt.AbstractDataBase
    '''

    def create(self, cfg: dict, tz: str):
        pass

"""
def create_ccxt(cfg: dict, tz: str) -> CCXTFeed:
    pass
    timeframe = bt.TimeFrame.TFrame(cfg['granularity'][0])
    compression = cfg['granularity'][1]
    datakwargs = dict(
        dataname=cfg['name'],
        timeframe=timeframe,
        compression=compression,
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
    datakwargs['config'] = cfg['options'].get('config', {})
    datakwargs['ohlcv_limit'] = cfg['options'].get('ohlcv_limit')
    datakwargs['fetch_ohlcv_params'] = cfg['options'].get('fetch_ohlcv_params', {})
    '''log('Loading CCXT data {} - {} {}\n{}'.format(
        cfg['name'],
        compression,
        bt.TimeFrame.TName(timeframe),
        tabulate(datakwargs.items(), tablefmt='plain')
    ), logging.DEBUG)'''
    data = cstores['ccxt'].getdata(**datakwargs)
    return data
"""
