from __future__ import division, absolute_import, print_function

import logging
import btconfig

from tabulate import tabulate
from btconfig.proto import ProtoStrategy, ForexProtoStrategy
from btconfig.helper import get_classes, create_opt_params


class PartStrategy(btconfig.BTConfigPart):

    PRIORITY = 80
    OPTIMIZERS = [
        'HillClimbingOptimizer',
        'RepulsingHillClimbingOptimizer',
        'SimulatedAnnealingOptimizer',
        'RandomSearchOptimizer',
        'RandomRestartHillClimbingOptimizer',
        'RandomAnnealingOptimizer',
        'ParallelTemperingOptimizer',
        'ParticleSwarmOptimizer',
        'EvolutionStrategyOptimizer',
        'BayesianOptimizer',
        'TreeStructuredParzenEstimators',
        'DecisionTreeOptimizer']

    def setup(self):
        commoncfg = self._instance.config.get('common', {})
        stratcfg = self._instance.config.get('strategy', {})
        stratname = commoncfg.get('strategy', None)
        all_classes = get_classes(self._instance.PATH_STRATEGY)
        if stratname not in all_classes:
            raise Exception(f'Strategy {stratname} not found')
        strat = all_classes[stratname]
        args = {}
        cfgargs = {}
        for x in [ProtoStrategy, ForexProtoStrategy, strat]:
            if issubclass(strat, x):
                cfgargs.update(stratcfg.get(x.__name__, {}))
        runtype = ('strategy'
                   if self._instance.mode != btconfig.MODE_OPTIMIZE
                   else 'optstrategy')
        params = '' if not len(cfgargs) else '\n{}'.format(
            tabulate(cfgargs.items(), tablefmt='plain'))
        txt = f'Creating {runtype} {stratname}{params}'
        self.log(txt, logging.DEBUG)
        if self._instance.mode in [
                btconfig.MODE_OPTIMIZE,
                btconfig.MODE_OPTIMIZEGENETIC]:
            args = create_opt_params(self._instance.config.get('optimize', {}))
            if self._instance.mode == btconfig.MODE_OPTIMIZE:
                for x in cfgargs:
                    cfgargs[x] = (cfgargs[x],)
                instargs = cfgargs.copy()
                instargs.update(args)
                self._instance.cerebro.optstrategy(strat, **instargs)
        else:
            self._instance.cerebro.addstrategy(strat, **cfgargs)
        self.cfgargs = cfgargs
        self.args = args
        self.stratname = stratname
        self.optimize = []
        self.optimizer = commoncfg.get('optimizer', self.OPTIMIZERS[0])
        self.optimizer_result = None
        self.optimizer_iterations = commoncfg.get('optimizer_iterations', 100)
        self.optimizer_exceptions = commoncfg.get('optimizer_exceptions', True)
        self.log(f'Strategy {stratname} created\n', logging.INFO)

    def run(self):
        if self._instance.mode == btconfig.MODE_OPTIMIZEGENETIC:
            res = self._run_optimizegenetic()
        else:
            res = self._instance.cerebro.run()
        return res

    def finish(self, result):
        if not len(result):
                return
        if self._instance.mode not in [
                btconfig.MODE_OPTIMIZE, btconfig.MODE_OPTIMIZEGENETIC]:
            return
        if self._instance.mode == btconfig.MODE_OPTIMIZEGENETIC:
            self.log(f'Optimizer {self.optimizer_result.__class__.__name__}:'
                     f' score:{self.optimizer_result.best_score}'
                     f' para:{self.optimizer_result.best_para}')
        else:
            sorted_results = sorted(
                result, key=lambda x: x[0].broker.getvalue(), reverse=True)
            best_result = sorted_results[0][0]
            best_para = {}
            for x in self.args:
                best_para[x] = best_result.params._get(x)
            self.log(f'Built-In Optimizer: para:{best_para}')


    def _run_optimizegenetic(self):
        self.optimizer_result = run_optimizer(
            self.optimizer,
            self.run_instance,
            self.args,
            self.iterations)
        return self.optimize

    def run_instance(self, p):
        cfg = self._instance._getConfigForMode(btconfig.MODE_BACKTEST)
        inst = btconfig.BTConfig(mode=btconfig.MODE_BACKTEST)
        for i in ['PartPlot', 'PartReport', 'PartTearsheet']:
            inst.LOAD_BTCONF_PART.remove(i)
        instargs = self.cfgargs.copy()
        instargs.update(p)
        cfg['strategy'] = {self.stratname: instargs}
        inst.setConfig(cfg)
        try:
            inst.run()
            if len(inst.result):
                self.optimize.append(inst.result)
        except Exception as e:
            if self.optimizer_exceptions:
                raise(e)
        return inst.cerebro.broker.getvalue()


def run_optimizer(class_name, runstrat, search_space, iterations=200):
    module = __import__('gradient_free_optimizers')
    class_ = getattr(module, class_name)
    opt = class_(search_space)
    opt.search(runstrat, n_iter=iterations, verbosity=[])
    return opt
