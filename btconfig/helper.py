from __future__ import division, absolute_import, print_function

import sys
import importlib
import inspect
import pkgutil

from datetime import datetime
from dateutil import parser


def seq(start: float, stop: float, step: float = 1.) -> list:
    '''
    Returns a list with a given sequence

    Args:
    ----
    * start (float): Start of sequence
    * stop (float): Stop of sequence
    * step (float): Step size of sequence

    Returns:
    --------
    list with number sequences (float)
    '''
    n = int(round((stop - start) / float(step)))
    if n > 1:
        return([start + step * i for i in range(n + 1)])
    elif n == 1:
        return([start])
    else:
        return([])


def parse_time(date: str) -> datetime:
    '''
    Datetime parser for csv datetime

    Args:
    -----
    * date (str): Date as string

    Returns:
    --------
    Parsed datetime object
    '''
    return parser.parse(date)


def sqn2rating(sqn_score: float) -> str:
    '''
    Returns a human readable SQN score

    Args:
    -----
    * sqn_score (float): numerical SQN score

    Returns:
    --------
    Human readable SQN string
    '''
    if sqn_score < 1.6:
        return 'Poor'
    elif sqn_score < 1.9:
        return 'Below average'
    elif sqn_score < 2.4:
        return 'Average'
    elif sqn_score < 2.9:
        return 'Good'
    elif sqn_score < 5.0:
        return 'Excellent'
    elif sqn_score < 6.9:
        return 'Superb'
    else:
        return 'Holy Grail'


def create_opt_params(params: dict) -> dict:
    '''
    Creates a dict with optimization params
    '''
    res = {}
    for v in params:
        p = params[v]
        if p[0] == 'list':
            res[v] = p[1]
        elif p[0] == 'range':
            res[v] = seq(p[1], p[2], p[3])
        else:
            raise Exception('Unknown param type for opt')
    return res


def merge_dicts(dict1: dict, dict2: dict) -> None:
    '''
    Merges dictionaries recursively

    Args:
    -----
    dict1: Base dictionary to merge
    dict2: Dictionary to merge on top of base dictionary

    Returns:
    --------
    None
    '''
    for k in dict2.keys():
        if (k in dict1 and isinstance(dict1[k], dict)
                and isinstance(dict2[k], dict)):
            merge_dicts(dict1[k], dict2[k])
        else:
            dict1[k] = dict2[k]


def get_classes(modules: list or str, register: bool = True) -> dict:
    '''
    Returns all classes from given search paths

    Args:
    -----
    - modules (list or str)
    - register (bool): Default=True

    Returns:
    --------
    dict
    '''

    def _iter_classes_submodules(path: str, register: bool) -> dict:
        '''
        Iterates over submodules and returns all contained classes
        '''
        spec = importlib.util.find_spec(path)
        if spec is None:
            return {}
        res = {}
        module = _import_module(spec)
        if register:
            _register_module(module)
        for m in inspect.getmembers(module, inspect.isclass):
            res[m[0]] = m[1]
        for mod in pkgutil.iter_modules([path]):
            path = '.'.join([x, mod.name])
            res.update(_iter_classes_submodules(path, register))
        return res

    def _import_module(spec):
        '''
        Imports a module by spec
        '''
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _register_module(module):
        '''
        Registers a module globally
        '''
        sys.modules[module.__name__] = module

    if type(modules) == str:
        modules = [modules]
    res = {}
    for x in modules:
        res.update(_iter_classes_submodules(x, register))
    return res
