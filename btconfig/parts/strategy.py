from __future__ import division, absolute_import, print_function

from tabulate import tabulate

import logging
import btconfig

from btconfig.proto import ProtoStrategy, ForexProtoStrategy
from btconfig.helper import get_classes, create_opt_params


class PartStrategy(btconfig.BTConfigPart):

    PRIORITY = 80

    def setup(self):
        commoncfg = self._instance.config.get('common', {})
        stratname = commoncfg.get('strategy', None)
        stratcfg = self._instance.config.get('strategy', {})
        all_classes = get_classes(self._instance.PATH_STRATEGY)
        if stratname not in all_classes:
            raise Exception(f'Strategy {stratname} not found')

        strat = all_classes[stratname]
        args = {}
        for x in [ProtoStrategy, ForexProtoStrategy, strat]:
            if issubclass(strat, x):
                args.update(stratcfg.get(x.__name__, {}))

        runtype = ('strategy'
                   if self._instance.mode != btconfig.MODE_OPTIMIZE
                   else 'optstrategy')
        params = '' if not len(args) else '\n{}'.format(
            tabulate(args.items(), tablefmt='plain'))
        txt = f'Creating {runtype} {stratname}{params}'
        self.log(txt, logging.DEBUG)

        if self._instance.mode != btconfig.MODE_OPTIMIZE:
            self._instance.cerebro.addstrategy(strat, **args)
        else:
            for x in args:
                args[x] = (args[x],)
            args.update(create_opt_params(
                self._instance.config.get('optimize', {})))
            self._instance.cerebro.optstrategy(strat, **args)
        self.log('Strategy created\n', logging.INFO)
