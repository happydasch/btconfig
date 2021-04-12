from __future__ import division, absolute_import, print_function

import logging

import backtrader as bt

import btconfig
from btconfig import log, cconfig, cdatas
from btconfig.feeds import (
    create_ib, create_ib_downloader, create_oandav20,
    create_oandav20_downloader, create_csv,
    create_ccxt)


def setup_datas() -> None:
    '''
    Sets up data sources and feeds

    All data sources will be created and after that
    all configured feeds will be created.

    Params:
    -------
    For datas:
        - type (str): Name of data source type
        - name (str): Name of data source
        - sessionstart: [hour, minute, second, microsecond]
        - sessionend: [hour, minute, second, microsecond]
        - granularity: [timeframe, compression]
        - for (list): List of feed names this data source is used with
        - options (dict): Custom data source params

    All data sources support some common backtrader options.
    Custom data source configuration is being done using options.

    For feeds:
        - timeframe (str): Timeframe as string
        - compression (int): Compression
        - method (str): Possible values: replay, resample, add
        - options (dict): Custom data options

    A data feed is a data source that is being used in backtrader.

    Config Example:
    ---------------
    The following examples creates a data source type data
    and sets the primary data feed from created data source:
    "datas": {
        "ident": {
            "type": "data",
            "name": "name",
            "sessionstart": [22, 0, 0, 0],
            "sessionend": [21, 59, 59, 999999],
            "granularity": ["Minutes", 5],
            "options": {},
            "for": ["primary"]
        },
    },
    "feeds": {
        "primary": {"Minutes", 1, "resample", {}}
    }
    The feed named primary will be available in the strategy as datas0
    '''
    feedcfg = cconfig.get('feeds', {})
    datascfg = cconfig.get('datas', {})
    commoncfg = cconfig.get('common', {})
    tz = commoncfg.get('timezone', None)

    for c in datascfg:
        added = False
        d = _create_data(datascfg[c], tz)

        # store data
        cdatas[datascfg[c]['name']] = d

        # check for feeds
        if not len(datascfg[c]['for']):
            continue

        # create all feeds from data source
        for f in datascfg[c]['for']:
            if f in feedcfg:
                if feedcfg[f][2] == 'add':
                    added = True
                elif not added:
                    # if a feed is added, ensure, source data is added, too
                    # this is needed since the source data is providing the
                    # clock
                    btconfig.cerebro.adddata(d)
                    added = True
                cdatas[f] = _create_feed(d, f, feedcfg[f])
                # remove created feed so already created feeds don't
                # get recreated by other data sources
                del(feedcfg[f])
            else:
                log('Feed {} is already set or does not exist'.format(f),
                    logging.DEBUG)
        log('Datas created\n', logging.INFO)


def _create_data(cfg: dict, tz: str) -> bt.AbstractDataBase:
    '''
    Creates and returns the data source from config

    Args:
    -----
    - cfg (dict)
    - tz (str)

    Returns:
    --------
    bt.AbstractDataBase
    '''
    if cfg['type'] == 'ib':
        d = create_ib(cfg, tz)
    elif cfg['type'] == 'ib_downloader':
        d = create_ib_downloader(cfg, tz)
    elif cfg['type'] == 'oandav20':
        d = create_oandav20(cfg, tz)
    elif cfg['type'] == 'oandav20_downloader':
        d = create_oandav20_downloader(cfg, tz)
    elif cfg['type'] == 'ccxt':
        d = create_ccxt(cfg, tz)
    elif cfg['type'] == 'csv':
        d = create_csv(cfg, tz)
    else:
        raise Exception('Unknown data type: %s' % cfg['type'])
    return d


def _create_feed(
        data: bt.AbstractDataBase,
        name: str,
        cfg: dict) -> bt.AbstractDataBase:
    '''
    Creates and returns the data feed from config

    Args:
    -----
    - data (bt.AbstractDataBase)
    - name (str)
    - cfg (dict)

    Returns:
    --------
    bt.AbstractDataBase
    '''
    dargs = dict(
        timeframe=bt.TimeFrame.TFrame(cfg[0]),
        compression=cfg[1] or None,
        name=name)
    mode = cfg[2]
    if len(cfg) > 3:
        dargs = {**dargs, **cfg[3]}
    d = None
    if mode == 'replay':
        d = btconfig.cerebro.replaydata(data, **dargs)
    elif mode == 'resample':
        d = btconfig.cerebro.resampledata(data, **dargs)
    elif mode == 'add':
        d = btconfig.cerebro.adddata(data, name=name)
    else:
        raise Exception(f'Unsupported mode: {mode}')
    return d
