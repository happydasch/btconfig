from __future__ import division, absolute_import, print_function

import logging

from tabulate import tabulate

from backtrader.stores import IBStore
from btconfig import log


def create_ib(cfg: dict) -> IBStore:
    '''
    Creates an Interactive Brokers store

    Args:
    -----
    - cfg (dict)

    Params:
    -------
    - host
    - port
    - clientId
    - reconnect
    - timeout
    - timeoffset
    - timerefresh
    - notifyall
    - indcash
    - _debug
    '''
    storekwargs = dict(
        host=cfg.get('host', ''),
        port=cfg.get('port', ''),
        clientId=cfg.get('clientId', ''),
        reconnect=cfg.get('reconnect', 3),
        timeout=cfg.get('timeout', 3),
        timeoffset=cfg.get('timeoffset', True),
        timerefresh=cfg.get('timerefresh', 60),
        notifyall=cfg.get('notifyall', False),
        indcash=cfg.get('indcash', True),
        _debug=cfg.get('_debug', False)
    )

    log('Creating Interactive Brokers store\n{}'.format(tabulate(
            storekwargs.items(), tablefmt='plain')),
        logging.DEBUG)
    # set created ib store
    store = IBStore(**storekwargs)
    # return store
    return store
