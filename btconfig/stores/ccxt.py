from __future__ import division, absolute_import, print_function

import logging

from tabulate import tabulate

from ccxtbt.ccxtstore import CCXTStore
from btconfig import log


def create_ccxt(cfg: dict) -> CCXTStore:
    '''
    Creates an CCXT store

    Args:
    -----
    - cfg (dict)

    Params:
    -------
    - exchange='bitmex'
    - currency=currency
    - config = {'urls': {'api': 'https://testnet.bitmex.com'},
                   'apiKey': apikey,
                   'secret': secret,
                   'enableRateLimit': enableRateLimit,
                }
    - retries=5
    - debug=False
    '''
    storekwargs = dict(
        exchange=cfg.get('exchange', ''),
        currency=cfg.get('currency', ''),
        config=cfg.get('config', {}),
        retries=cfg.get('retries', 5),
        debug=cfg.get('debug', False)
    )
    log('Creating CCXT store\n{}'.format(tabulate(
        storekwargs.items(), tablefmt='plain')),
        logging.DEBUG)
    # set created ccxt store
    store = CCXTStore(**storekwargs)
    # return store
    return store
