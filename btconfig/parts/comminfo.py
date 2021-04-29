from __future__ import division, absolute_import, print_function

from tabulate import tabulate

import logging
import btconfig

from btconfig.helper import get_classes


class PartCommInfo(btconfig.BTConfigPart):
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

    PRIORITY = 70

    def setup(self) -> None:
        comminfocfg = self._instance.config.get('comminfo', {})
        classname = comminfocfg.get('classname')
        params = comminfocfg.get('params', {})
        if not classname:
            return

        all_classes = get_classes(self._instance.PATH_COMMINFO)
        if classname not in all_classes:
            raise Exception(f'CommInfo {classname} not found')

        self.log('Creating Comminfo {}\n{}'.format(
                classname, tabulate(params.items(), tablefmt='plain')),
            logging.DEBUG)
        comminfo = all_classes[classname](**params)
        self._instance.cerebro.broker.addcommissioninfo(comminfo)
        self.log(f'Comminfo {classname} created\n', logging.INFO)
