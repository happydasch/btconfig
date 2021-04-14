from __future__ import division, absolute_import, print_function

from tabulate import tabulate

import logging

import btconfig
from btconfig import log, cconfig, PATH_COMMINFO
from btconfig.helper import get_classes


def setup_comminfo():
    '''
    Sets up the comminfo to use

    Config Example:
    ---------------
    To set up oanda comminfo:

    "comminfo": {
        "classname": "OandaV20BacktestCommInfo",
        "params": {
            "acc_counter_currency": true,
            "spread": 0.7,
            "leverage": 20.0,
            "margin": 0.5,
            "pip_location": -4
        }
    }
    '''
    comminfocfg = cconfig.get('comminfo', {})
    classname = comminfocfg.get('classname')
    params = comminfocfg.get('params', {})
    if not classname:
        return
    all_classes = get_classes(PATH_COMMINFO)
    if classname not in all_classes:
        raise Exception(f'CommInfo: {classname} not found')
    log('Creating Comminfo: {} with Params: \n{}'.format(
            classname,
            tabulate(params.items(), tablefmt='plain')),
        logging.DEBUG)
    comminfo = all_classes[classname](**params)
    btconfig.cerebro.broker.addcommissioninfo(comminfo)
    log('Comminfo created\n', logging.INFO)
