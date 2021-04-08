from __future__ import division, absolute_import, print_function

import logging

import btconfig
from btconfig import log, cconfig, cmode, MODE_LIVE

from btoandav20.sizers import (
    OandaV20RiskPercentSizer, OandaV20BacktestRiskPercentSizer)


def setup_sizer():
    '''
    Set ups the sizer to use
    '''
    commoncfg = cconfig.get('common', {})
    sizercfg = cconfig.get('sizer', {})
    if cmode != MODE_LIVE or commoncfg.get('broker') != 'oandav20':
        btconfig.cerebro.addsizer(
            OandaV20BacktestRiskPercentSizer,
            percents=sizercfg.get('risk', 2),
            avail_reduce_perc=0.1)
    else:
        btconfig.cerebro.addsizer(
            OandaV20RiskPercentSizer,
            percents=sizercfg.get('risk', 2),
            avail_reduce_perc=0.1)
    log('Sizer created\n', logging.INFO)
