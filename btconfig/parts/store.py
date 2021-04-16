from __future__ import division, absolute_import, print_function

import backtrader as bt
from tabulate import tabulate

import logging
import btconfig

from btconfig.helper import get_classes


class PartStores(btconfig.BTConfigPart):
    '''
    Sets up configured stores

    This creates all stores and sets a broker
    from store if this is configured.

    Multiple stores can be configured

        Config Example:
        ---------------
        The following example would create a store
        named store and set the broker and cash from
        the given store:

        "common": {
            "broker": "store_id",
            "cash": 10000
        }
        "stores": {
            "store_id": {
                "classname": "StoreClass",
                "params": {
                    # store params as key/value pairs
                }
            }
        }
    '''

    PRIORITY = 40

    def setup(self) -> None:
        commoncfg = self._instance.config.get('common', {})
        storescfg = self._instance.config.get('stores', {})
        all_classes = get_classes(self._instance.PATH_STORE)
        for i, v in storescfg.items():
            classname = v.get('classname')
            params = v.get('params', {})
            if not classname:
                return
            if classname not in all_classes:
                raise Exception(f'Store {classname} not found')
            self.log('Creating Store {} ({})\n{}'.format(
                classname, i,
                tabulate(params.items(), tablefmt='plain')),
                logging.DEBUG)
            store = all_classes[classname](**params)
            self._instance.stores[i] = store
            self.log(f'Store {i} created', logging.INFO)
        # set broker
        broker = commoncfg.get('broker', None)
        if broker is not None:
            store = self._instance.stores[broker]
            self._instance.cerebro.setbroker(store.getbroker())
            self.log(f'Broker from store {broker} was set', logging.INFO)
        # set starting cash
        if commoncfg.get('cash', None) is not None:
            if hasattr(self._instance.cerebro.broker, 'setcash'):
                cash = commoncfg.get('cash')
                self._instance.cerebro.broker.setcash(cash)
                self.log(f'Starting cash was set to {cash}', logging.INFO)

        self.log('Stores created\n', logging.INFO)
