from __future__ import division, absolute_import, print_function

import pandas as pd
import sys
import importlib
import inspect
import pkgutil
import json
import yaml
import backtrader as bt

from zipimport import zipimporter
from datetime import datetime, time, timedelta
from dateutil import parser
from string import Template


class DeltaTemplate(Template):
    delimiter = '%'


def strfdelta(tdelta, fmt):
    d = {'D': tdelta.days}
    d['H'], rem = divmod(tdelta.seconds, 3600)
    d['M'], d['S'] = divmod(rem, 60)
    d['M'] = '%02d' % d['M']
    d['S'] = '%02d' % d['S']
    t = DeltaTemplate(fmt)
    return t.substitute(**d)


def load_json(filename):
    with open(filename, 'r') as file:
        res = json.load(file)
    return res


def load_yaml(filename):
    with open(filename, 'r') as file:
        res = yaml.safe_load(file)
    return res


def seq(start, stop, step=1) -> list:
    '''
    Returns a list with a given sequence

    Args:
    ----
    * start: Start of sequence
    * stop: Stop of sequence
    * step: Step size of sequence

    Returns:
    --------
    list with number sequences (float|int)
    '''
    n = int(round((stop - start) / step))
    res = []
    if n > 1:
        res = [start + step * i for i in range(n + 1)]
    elif n == 1:
        res = [start]
    for i, v in enumerate(res):
        res[i] = int(v) if int(v) == float(v) else float(v)
    return res


def sqn_rating(sqn_score: float) -> str:
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


def make_equal_dfs(datas, key=None, dropna=True):
    if not key:
        key = list(datas.keys())[0]
    src_df = pd.DataFrame(datas[key]['datetime'])
    for i in datas:
        if i == key:
            continue
        df_new = pd.merge(
            left=src_df,
            right=datas[i],
            on='datetime',
            how='left')
        if dropna:
            df_new = df_new.dropna()
        datas[i] = df_new.reset_index(drop=True)
    return datas


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
        if isinstance(spec.loader, zipimporter):
            exec(
                spec.loader.get_code(mod.__name__),
                mod.__dict__)
        else:
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
    for m in inspect.getmembers(sys.modules['__main__'], inspect.isclass):
        res[m[0]] = m[1]
    for x in modules:
        res.update(_iter_classes_submodules(x, register))
    return res


def parse_dt(dt):
    return parser.parse(dt)


def get_starttime(timeframe, compression, dt, sessionstart=None, offset=0):
    '''
    This method will return the start of the period based on current
    time (or provided time).
    '''
    if sessionstart is None:
        # use UTC 22:00 (5:00 pm New York) as default
        sessionstart = time(hour=22, minute=0, second=0)
    if dt is None:
        dt = datetime.utcnow()
    if timeframe == bt.TimeFrame.Seconds:
        dt = dt.replace(
            second=(dt.second // compression) * compression,
            microsecond=0)
        if offset:
            dt = dt + timedelta(seconds=compression * offset)
    elif timeframe == bt.TimeFrame.Minutes:
        if compression >= 60:
            hours = 0
            minutes = 0
            # get start of day
            dtstart = get_starttime(bt.TimeFrame.Days, 1, dt, sessionstart)
            # diff start of day with current time to get seconds
            # since start of day
            dtdiff = dt - dtstart
            hours = dtdiff.seconds // ((60 * 60) * (compression // 60))
            minutes = compression % 60
            dt = dtstart + timedelta(hours=hours, minutes=minutes)
        else:
            dt = dt.replace(
                minute=(dt.minute // compression) * compression,
                second=0,
                microsecond=0)
        if offset:
            dt = dt + timedelta(minutes=compression * offset)
    elif timeframe == bt.TimeFrame.Days:
        if dt.hour < sessionstart.hour:
            dt = dt - timedelta(days=1)
        if offset:
            dt = dt + timedelta(days=offset)
        dt = dt.replace(
            hour=sessionstart.hour,
            minute=sessionstart.minute,
            second=sessionstart.second,
            microsecond=sessionstart.microsecond)
    elif timeframe == bt.TimeFrame.Weeks:
        if dt.weekday() != 6:
            # sunday is start of week at 5pm new york
            dt = dt - timedelta(days=dt.weekday() + 1)
        if offset:
            dt = dt + timedelta(days=offset * 7)
        dt = dt.replace(
            hour=sessionstart.hour,
            minute=sessionstart.minute,
            second=sessionstart.second,
            microsecond=sessionstart.microsecond)
    elif timeframe == bt.TimeFrame.Months:
        if offset:
            dt = dt + timedelta(days=(min(28 + dt.day, 31)))
        # last day of month
        last_day_of_month = dt.replace(day=28) + timedelta(days=4)
        last_day_of_month = last_day_of_month - timedelta(
            days=last_day_of_month.day)
        last_day_of_month = last_day_of_month.day
        # start of month (1 at 0, 22 last day of prev month)
        if dt.day < last_day_of_month:
            dt = dt - timedelta(days=dt.day)
        dt = dt.replace(
            hour=sessionstart.hour,
            minute=sessionstart.minute,
            second=sessionstart.second,
            microsecond=sessionstart.microsecond)
    return dt


def get_data_params(cfg: dict, tz: str, dtnow=None) -> dict:
    '''
    Returns params to use for data sources
    '''
    timeframe = bt.TimeFrame.TFrame(cfg['granularity'][0])
    compression = cfg['granularity'][1]
    # basic params
    dargs = dict(
        dataname=cfg['dataname'],
        timeframe=timeframe,
        compression=compression,
        tz=tz)
    # session start and end
    dargs['sessionstart'] = get_data_session(cfg.get('sessionstart', []))
    dargs['sessionend'] = get_data_session(cfg.get('sessionend', []))
    # fromdate and todate
    fromdate, todate = get_data_dates(
        cfg.get('backfill_days', 0),
        cfg.get('fromdate'),
        cfg.get('todate'),
        dtnow)
    dargs['fromdate'] = fromdate
    dargs['todate'] = todate
    # append args from params
    dargs.update(cfg.get('params', {}))
    return dargs


def get_data_session(session):
    '''
    Returns a session time object
    '''
    res = None
    if isinstance(session, list) and len(session) >= 4:
        res = time(
            session[0], session[1], session[2], session[3])
    return res


def get_data_dates(backfill_days, fromdate, todate, dtnow=None):
    '''
    Returns fromdate and todate datetime objects
    '''
    if dtnow is None:
        dtnow = datetime.now()
    if fromdate:
        fromdate = parser.parse(fromdate)
        if todate:
            todate = parser.parse(todate)
    elif backfill_days and backfill_days > 0:
        # date for backfill start
        fromdate = dtnow - timedelta(days=backfill_days)
    return fromdate, todate
