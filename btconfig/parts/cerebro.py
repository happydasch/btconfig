from __future__ import division, absolute_import, print_function

import logging

from tabulate import tabulate

import backtrader as bt

import btconfig
from btconfig import log, cconfig


def setup_cerebro() -> None:
    '''
    Sets up a backtrader cerebro instance

    Config Example:
    ---------------
    The following example would set preload=True and
    runonce=True for backtest and optimization:

    "cerebro": {},
    "_live": {
        "cerebro": {}
    },
    "_backtest": {
        "cerebro": {
            "preload": true,
            "runonce": true
        }
    }

    The following example would set preload=True for all modes:

    "cerebro": {
        "preload": true
    }
    '''
    commoncfg = cconfig.get('common', {})
    # collect all args for cerebro
    args = cconfig.get('cerebro', {})
    args['tz'] = commoncfg.get('timezone')
    log('Creating Cerebro\n{}'.format(tabulate(
            args.items(), tablefmt='plain')),
        logging.DEBUG)
    # create and assign cerebro instance to module
    btconfig.cerebro = bt.Cerebro(**args)
    # log execution
    log('Cerebro created\n', logging.INFO)
