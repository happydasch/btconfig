from __future__ import division, absolute_import, print_function

import logging

import backtrader as bt

import btconfig
from btconfig import log, cconfig, cstores
from btconfig.stores import create_oandav20, create_ib


def setup_stores() -> None:
    '''
    Sets up configured stores

    This creates all stores and sets a broker
    from store if this is configured.

    Available Stores:
    -----------------
    - oandav20
    - ib

    Config Example:
    ---------------
    The following example would create a store
    named store and set the broker from the given
    store:

    "common": {
        "broker": "store"
    }
    "stores": {
        "store": {}
    }
    '''
    commoncfg = cconfig.get('common', {})
    storescfg = cconfig.get('stores', {})
    # create all configured stores
    for s in storescfg:
        cstores[s] = _create_store(s, storescfg.get(s, {}))
    # set broker if configured
    broker = commoncfg.get('broker', None)
    if broker is not None:
        store = cstores[broker].getbroker()
        btconfig.cerebro.setbroker(store.getbroker())
    # log execution
    if broker is not None:
        log('Broker %s was set' % broker, logging.DEBUG)
    else:
        log('Broker was not set', logging.DEBUG)
    log('Stores created\n', logging.INFO)


def _create_store(store: str, cfg: dict) -> bt.Store:
    '''
    Creates and configures the store

    Args:
    -----
    store (str)
    cfg (dict)

    Returns:
    --------
    bt.Store instance
    '''
    if store == 'oandav20':
        s = create_oandav20(cfg)
    elif store == 'ib':
        s = create_ib(cfg)
    else:
        raise Exception('Unknown store: %s\n' % store)
    log('Store created: %s\n' % store, logging.DEBUG)
    return s
