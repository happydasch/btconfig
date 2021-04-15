
from __future__ import division, absolute_import, print_function


import btconfig


class StoreOandaV20(btconfig.BTConfigStore):

    def create(self, cfg: dict):
        pass

"""
import logging
from tabulate import tabulate

from btoandav20.stores import OandaV20Store

from btconfig import log


def create_oandav20(cfg: dict) -> OandaV20Store:
    '''
    Creates an Oanda V20 store

        Args:
        -----
        - cfg (dict)

        Params:
        -------
        - token
        - account
        - practice
        - stream_timeout
        - notif_transactions
    '''

    storekwargs = dict(
        token=cfg.get('token', ''),
        account=cfg.get('account', ''),
        practice=cfg.get('practice', True),
        stream_timeout=cfg.get('stream_timeout', None),
        poll_timeout=cfg.get('poll_timeout', None),
        notif_transactions=cfg.get('notif_transactions', False),
    )

    # copy args and remove secrets for log
    kwargs_cp = dict(storekwargs)
    del kwargs_cp['token'], kwargs_cp['account']
    log('Creating Oanda V20 API store\n{}'.format(tabulate(
            kwargs_cp.items(), tablefmt='plain')),
        logging.DEBUG)
    # set created oanda store
    store = OandaV20Store(**storekwargs)
    # return store
    return store
"""