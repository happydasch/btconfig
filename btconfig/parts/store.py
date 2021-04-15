from __future__ import division, absolute_import, print_function

import backtrader as bt

import logging
import btconfig

#from btconfig.stores import create_oandav20, create_ib, create_ccxt


class PartStores(btconfig.BTConfigPart):
    '''
    Sets up configured stores

    This creates all stores and sets a broker
    from store if this is configured.

        Available Stores:
        -----------------
        - oandav20
        - ib

        Config Example:
        ---------------
        The following example would create a store
        named store and set the broker from the given
        store:

        "common": {
            "broker": "store"
        }
        "stores": {
            "store": {}
        }
    '''

    PRIORITY = 40

    def setup(self) -> None:
        commoncfg = self._instance.config.get('common', {})
        storescfg = self._instance.config.get('stores', {})
        # create all configured stores
        for s in storescfg:
            self._instance.stores[s] = self._createStore(
                s, storescfg.get(s, {}))
        # set broker
        broker = commoncfg.get('broker', None)
        if broker is not None:
            store = self._instance.stores[broker]
            self._instance.cerebro.setbroker(store.getbroker())
            self.log(f'Broker was set: {broker}', logging.DEBUG)
        # set starting cash
        if commoncfg.get('cash', None) is not None:
            if hasattr(self._instance.cerebro.broker, 'setcash'):
                cash = commoncfg.get('cash')
                self._instance.cerebro.broker.setcash(cash)
                self.log(f'Starting cash was set to {cash}', logging.DEBUG)
        # log execution
        self.log('Stores created\n', logging.INFO)

    def _createStore(self,  store: str, cfg: dict) -> bt.Store:
        '''
        Creates and configures the store

        Args:
        -----
        store (str)
        cfg (dict)

        Returns:
        --------
        bt.Store instance
        '''
        if store == 'oandav20':
            s = create_oandav20(cfg)
        elif store == 'ib':
            s = create_ib(cfg)
        elif store == 'ccxt':
            s = create_ccxt(cfg)
        else:
            raise Exception('Unknown store: %s\n' % store)
        self.log('Store created: %s\n' % store, logging.DEBUG)
        return s
