from __future__ import division, absolute_import, print_function

import os
import subprocess
import logging
import btconfig

from datetime import timedelta
from tabulate import tabulate
from btconfig.proto import ProtoStrategy, ForexProtoStrategy
from btconfig.helper import get_classes, create_opt_params

import hyperactive
from hyperactive import Hyperactive
from hyperactive.dashboards import ProgressBoard


class ProcessProgressBoard(ProgressBoard):

    process = None

    def create_lock(self, progress_id):
        pass

    def open_dashboard(self):
        abspath = os.path.dirname(
            hyperactive.dashboards.progress_board.__file__)
        paths = " ".join(self.progress_ids)
        self.process = subprocess.Popen(
            ["streamlit", "run", os.path.join(abspath, 'run_streamlit.py'), paths])


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
        self.optimizer_iterations = commoncfg.get('optimizer_iterations', 1000)
        self.optimizer_exceptions = commoncfg.get('optimizer_exceptions', True)
        self.optimizer_func = commoncfg.get('optimizer_func', self._optimizer_func)
        if commoncfg.get('create_plot', False):
            self.optimizer_jobs = 1
            self.show_progress_board = False
        else:
            self.optimizer_jobs = commoncfg.get('optimizer_jobs', -1)
            self.show_progress_board = True
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
            self.log(f'Optimizer {self.optimizer_result.__class__.__name__}'
                     '\nResults:\n')
            for x in self.optimizer_result.results_list:
                results = tabulate(x.items(), tablefmt='plain')
                self.log(results)
        else:
            sorted_results = sorted(
                result, key=lambda x: x[0].broker.getvalue(), reverse=True)
            best_result = sorted_results[0][0]
            best_para = {}
            for x in self.args:
                best_para[x] = best_result.params._get(x)
            para = tabulate(best_para.items(), tablefmt='plain')
            self.log(f'Built-In Optimizer\nParameters:\n{para}\n')

    def _optimizer_func(self, instance):
        return round(instance.cerebro.broker.getvalue()
                     - instance.cerebro.broker.startingcash, 2)

    def _run_optimizegenetic(self):
        self.optimizer_result = run_optimizer(
            self.optimizer,
            self.run_instance,
            self.args,
            self.optimizer_iterations,
            self.optimizer_jobs,
            self.show_progress_board)
        return self.optimize

    def run_instance(self, p):
        inst = btconfig.BTConfig(mode=btconfig.MODE_BACKTEST)
        # instance args convert numpy numbers to float or int
        # FIXME with hyperactive this should not be needed
        # FIXME para_dict is coming from hyperactive, gradient free optimizer do not need that
        for i, v in p.para_dict.items():
            p.para_dict[i] = int(v) if int(v) == float(v) else float(v)
        instargs = self.cfgargs.copy()
        instargs.update(p.para_dict)
        # config for instance
        cfg = self._instance._getConfigForMode(btconfig.MODE_BACKTEST)
        commoncfg = cfg['common']
        for i in ['create_plot', 'create_log', 'create_report',
                  'create_tearsheet']:
            commoncfg[i] = False
        cfg['strategy'] = {self.stratname: instargs}
        inst.setConfig(cfg)
        strargs = tabulate(p.para_dict.items(), tablefmt='plain')
        self.log(f'Running optimizer instance with:\n{strargs}', logging.DEBUG)
        try:
            inst.run()
            if len(inst.result):
                self.optimize.append(inst.result)
            res = self.optimizer_func(inst)
        except Exception as e:
            if self.optimizer_exceptions:
                raise(e)
            self.log('Optimizer instance did not finish\n')
            res = 0
        if inst.duration:
            duration = timedelta(seconds=inst.duration)
            self.log(
                f'Optimizer instance finished with: {res}'
                f' (Duration: {duration})\n',
                logging.INFO)
        return res


def run_optimizer(class_name, runstrat, search_space,
                  iterations=200, jobs=1,
                  show_progress_board=False):
    module = __import__('hyperactive.optimizers')
    class_ = getattr(module, class_name)
    progress_board = None
    if show_progress_board:
        progress_board = ProcessProgressBoard()
    hyper = Hyperactive()
    opt = class_()
    hyper.add_search(
        runstrat, search_space,
        n_iter=iterations, n_jobs=jobs,
        progress_board=progress_board,
        optimizer=opt)
    hyper.run()
    # only gradient free optimizers
    #module = __import__('gradient_free_optimizers')
    #opt = class_(search_space)
    #opt.search(runstrat, n_iter=iterations, verbosity=[])
    #return opt
    return hyper
