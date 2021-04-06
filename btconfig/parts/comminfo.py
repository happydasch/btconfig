from __future__ import division, absolute_import, print_function

import logging

import btconfig
from btconfig import log, cconfig, cmode, MODE_LIVE

from btoandav20.commissions import OandaV20BacktestCommInfo


def setup_comminfo():
    '''
    Set ups the comminfo to use
    '''
    if cmode != MODE_LIVE:
        comminfocfg = cconfig.get('comminfo', {})
        stratcfg = cconfig.get('ForexProtoStrategy', {})
        leverage = comminfocfg.get('leverage', 1)
        margin = comminfocfg.get('margin', 0.5)
        spread = comminfocfg.get('spread', 1.0)
        counter_curr = comminfocfg.get('acc_counter_currency', True)
        pip_location = stratcfg.get('pip_location', 1)
        comminfo = OandaV20BacktestCommInfo(
            data=btconfig.cerebro.datas[0],
            acc_counter_currency=counter_curr,
            pip_location=pip_location,
            spread=spread,
            margin=margin,
            leverage=leverage)
        btconfig.cerebro.broker.addcommissioninfo(comminfo)
    log('Comminfo created\n', logging.INFO)
