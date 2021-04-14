from __future__ import division, absolute_import, print_function

import logging

from tabulate import tabulate

import btconfig
from btconfig import log, cconfig, cmode, MODE_OPTIMIZE, PATH_STRATEGY
from btconfig.proto import ProtoStrategy, ForexProtoStrategy
from btconfig.helper import get_classes, create_opt_params


def setup_strategy():
    '''
    Creates strategy from config
    '''
    commoncfg = cconfig.get('common', {})
    stratname = commoncfg.get('strategy', None)
    all_classes = get_classes(PATH_STRATEGY)
    if stratname not in all_classes:
        raise Exception(f'Strategy {stratname} not found')

    strat = all_classes[stratname]
    args = {}
    if issubclass(strat, ProtoStrategy):
        args.update(cconfig.get(ProtoStrategy.__name__, {}))
    if issubclass(strat, ForexProtoStrategy):
        args.update(cconfig.get(ForexProtoStrategy.__name__, {}))
    args.update(cconfig.get(strat.__name__, {}))

    runtype = 'strategy' if cmode != MODE_OPTIMIZE else 'optstrategy'
    params = '' if not len(args) else '\n{}'.format(
        tabulate(args.items(), tablefmt='plain'))
    txt = 'Creating {}: {}{}'.format(runtype, stratname, params)
    log(txt, logging.DEBUG)

    if cmode != MODE_OPTIMIZE:
        btconfig.cerebro.addstrategy(strat, **args)
    else:
        for x in args:
            args[x] = (args[x],)
        args.update(create_opt_params(cconfig.get('optimize', {})))
        btconfig.cerebro.optstrategy(strat, **args)
    log('Strategy created\n', logging.INFO)
