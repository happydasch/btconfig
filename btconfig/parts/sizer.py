from __future__ import division, absolute_import, print_function

from tabulate import tabulate

import logging

import btconfig
from btconfig import log, cconfig, PATH_SIZER
from btconfig.helper import get_classes


def setup_sizer():
    '''
    Sets up the sizer to use

    Config Example:
    ---------------
    To set up oanda sizer:

    "sizer": {
        "classname": "OandaV20RiskPercentSizer",
        "params": {
            "percents": 2,
            "avail_reduce_perc": 0.1
        }
    }
    '''
    sizercfg = cconfig.get('sizer', {})
    classname = sizercfg.get('classname')
    params = sizercfg.get('params', {})
    if not classname:
        return
    all_classes = get_classes(PATH_SIZER)
    if classname not in all_classes:
        raise Exception(f'Sizer: {classname} not found')
    log('Creating Sizer: {} with Params: \n{}'.format(
        classname,
        tabulate(params.items(), tablefmt='plain')),
        logging.DEBUG)
    btconfig.cerebro.addsizer(all_classes[classname], **params)
    log('Sizer created\n', logging.INFO)
