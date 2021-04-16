from __future__ import division, absolute_import, print_function

from tabulate import tabulate

import logging
import btconfig

from btconfig.helper import get_classes


class PartSizer(btconfig.BTConfigPart):
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

    PRIORITY = 60

    def setup(self):
        sizercfg = self._instance.config.get('sizer', {})
        classname = sizercfg.get('classname')
        params = sizercfg.get('params', {})
        if not classname:
            return

        all_classes = get_classes(self._instance.PATH_SIZER)
        if classname not in all_classes:
            raise Exception(f'Sizer {classname} not found')

        self.log('Creating Sizer {}\n{}'.format(
            classname,
            tabulate(params.items(), tablefmt='plain')),
            logging.DEBUG)
        self._instance.cerebro.addsizer(all_classes[classname], **params)
        self.log('Sizer created\n', logging.INFO)
