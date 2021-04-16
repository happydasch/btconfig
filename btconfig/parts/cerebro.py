from __future__ import division, absolute_import, print_function

import backtrader as bt
from tabulate import tabulate

import logging
import btconfig


class PartCerebro(btconfig.BTConfigPart):
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

    PRIORITY = 20

    def setup(self) -> None:
        commoncfg = self._instance.config.get('common', {})
        # collect all args for cerebro
        args = self._instance.config.get('cerebro', {})
        args['tz'] = commoncfg.get('timezone')
        self.log('Creating Cerebro\n{}'.format(tabulate(
                args.items(), tablefmt='plain')),
            logging.DEBUG)
        # create and assign cerebro instance
        self._instance.cerebro = bt.Cerebro(**args)
        self._instance.cerebro.btconfig = self._instance
        # log execution
        self.log('Cerebro created\n', logging.INFO)
