"""
Backtrader setup running lib with support for config files

The backtrader system will be configured and set up by using config files.
The possible configuration options are described below.

Intention
---------

    The intention of btconfig is to provide a basic framework for automatic
    strategy setup using a config file. This allows to collect different
    strategies, indicators, etc. and to setup and execute a strategy in
    different execution modes:

    * LIVE
    * BACKTEST
    * OPTIMIZE
    * OPTIMIZEGENETIC

    Every execution mode can set different settings for data sources, parts to
    use and so on.

    Additionally btconfig helps with data from different data sources, provides
    generic api access to different data providers. It also provides basic
    crypto support.


How to run
----------

    To run a strategy you first need to create a config file.

    If a config file is available:
    btconfig.run(mode, configfile)

    where mode is either LIVE, BACKTEST or OPTIMIZE and configfile
    is the filename of the config file.

    Additional seearch paths and settings can be changed before executing.

    Simple example:
    ```
    import btconfig

    if __name__ == '__main__':
        btconfig.run(btconfig.MODE_BACKTEST, "config.json")
    ```

    Example with customization:

    ```
    import btconfig
    from btconfig import BTConfig

    btconf = BTConfig()
    btconf.PATH_STRATEGY.append('other_stratgies')

    if __name__ == '__main__':
        btconf.run(btconfig.MODE_BACKTEST, "config.json")
    ```

Config file
-----------

    #### [common]
    Common configuration

        * time (datetime): The time btconfig was initialized
        * strategy (string): The name of the strategy to use
        * timezone (string): The timezone of data
        * create_plot (bool): Should the plot be created
        * create_report (bool): Should a report be created
        * create_log (bool): Should a log be created
        * add_observer (bool): Should observers be added
        * add_analyzer (bool): Should analyzers be added
        * broker (string): The broker to use
        * cash (float): The start amount of cash
        * log_path (str): Path for log files
        * report_path (str): Path for backtest files
        * data_path (str): Path for data files

    #### [logging]
    Configuration for logging

        * log_to_console (bool):
          Should log entries be logged to console (true/false)
        * log_to_file (bool):
          Should log entries be logged into files (true/false)
        * log_to_telegram (bool):
          Should log entries be logged to telegram (true/false)
        * telegram (dict):
          Config for telegram
        * level (string):
          Log level to log (ex. "INFO")

    See btconfig.parts.logging for more details

    #### [cerebro]
    Configuration for cerebro

    Supports all backtrader params. Based on the mode different
    defaults will be preset. name/value pairs.

    See btconfig.parts.cerebro for more details

    #### [stores]
    Configuration for stores

        Allows to setup different stores which
        are differentiated by the store_id.

        * store_id (string: dict): Configuration for a single store

        "stores":
            "store_id": {
                "classname": "ClassName",
                "params": {
                    # params for store
                }
            }
        }

        Every store can individually be configured by providing
        different params in the dict.

    See btconfig.parts.store for more details

    #### [datas]
    Configuration for data sources

        Allows to setup different data sources which
        are differentiated by the data_id.

        * data_id (string: dict): Configuration for a data source

        "datas": {
            "data_id": {
                "classname": "ClassName",
                "store": "store_id",
                "name": "EUR_USD",
                "sessionstart": [22, 0, 0, 0],
                "sessionend": [21, 59, 59, 999999],
                "granularity": ["Minutes", 5],
                "backfill_days": null,
                "fromdate": null,
                "todate": null,
                "for": [],
                "params": {
                    # additional data params
                }
            }
        }

    See btconfig.parts.data for more details

    #### [feeds]
    Configuration for data feeds of strategy

        * feed_name (string: list): Configuration for a single feed
        Where list expects the values:
        [Timeframe, Compression, Method, Options]

    See btconfig.parts.data for more details

    #### [sizer]
    Configuration for sizer

        * classname (str): Classname to use
        * params (dict): name/value pairs for class params

    See btconfig.parts.sizer for more details

    #### [comminfo]
    Configuration for comminfo

        * classname (str): Classname to use
        * params (dict): name/value pairs for class params

    See btconfig.parts.comminfo for more details

    #### [plot]
    Configuration for plotting

        * use (string): use=web for web interface, TKAgg etc.
        * volume (bool): Should volume be added to plotting (true/false)
        * bar_dist (float): Distance of markers to bars (ex. 0.0003)
        * style (string): Plot style for bars (ex. "candle")
        * combine (bool): Should different feeds be combined to a
        single plot (true/false)
        * port (int): Web port for btplotting (ex. 80)
        * live_lookback (int): Lockback of bars for live plotting (ex. 50)
        * override (dict): Plot scheme override vales

    See btconfig.parts.plot for more details

    #### [analyzers]
    Configuration for analyzers
    **Only temporary**

        * time_return (list): ["Minutes", 240]
        * sharpe_ratio (list): ["Days", 1, 365, true]
        Timeframe, Compression, Factor, Annualize
        Config based on:
        https://community.backtrader.com/topic/2747/how-to-initialize-bt-analyzers-sharperatio/13

    See btconfig.parts.backtrader for more details

    #### [strategy]
    Configuration for strategy
    Contains dict with config for different classes

        ProtoStrategy:
        Configuration for prototype strategy
            * valuename (string/number):
              Set common strategy param to given value

        ForexProtoStrategy:
        Configuration for forex prototype strategy
            * valuename (string/number):
              Set common strategy param to given value

        StrategyName:
        Configuration for strategy with given name
            * valuename (string/number): Set strategy param to given value

    #### [_live]
    Configuration when using live trading

        * cerebro (dict): Cerebro params

    #### [_backtest]
    Configuration when using backtesting / optimization

        * cerebro (dict): Cerebro params

    #### [_optimize]
    Configuration when using optimization

    Optimization is using the configuration for backtest
    with additional possibilities to set custom config values.

        * cerebro (dict): Cerebro params
        * values (dict): Values to use for optimization
            * valuename: ["list", ["value 1", "value 2"]]:
            List of values to use: list with values
            * valuename: ["range", 8, 10, 1]:
            Range of numerical values to use: start, end, step
"""
from __future__ import division, absolute_import, print_function

import os
import json
import time
import logging
import requests
import random
import pandas as pd
import backtrader as bt

from copy import deepcopy
from datetime import datetime, timedelta
from dateutil import parser
from urllib.parse import urlencode
from .helper import get_classes, merge_dicts, get_data_params, parse_dt
from threading import Lock


# dev info
__author__ = 'Daniel Schindler <daniel@vcard24.de>'
__status__ = 'development'

# constants
TIMEFORMAT = '%Y-%m-%d %H:%M:%S'
NUMBERFORMAT = '0,0[.]00[000000]'
MODES = ['LIVE', 'BACKTEST', 'OPTIMIZE', 'OPTIMIZEGENETIC']
MODE_LIVE, MODE_BACKTEST, MODE_OPTIMIZE, MODE_OPTIMIZEGENETIC = range(len(MODES))

# default config dicts
CONFIG_DEFAULT = {
    'common': {}, 'cerebro': {
        'stdstats': False, 'tradehistory': True
    }, 'stores': {}, 'broker': {},
    'datas': {}, 'feeds': {}, 'sizer': {}, 'comminfo': {},
    'plot': {}, 'logging': {}, 'analyzers': {}, 'strategy': {},
    '_live': {}, '_backtest': {}, '_optimize': {}}
CONFIG_LIVE = {
    **CONFIG_DEFAULT, **{'cerebro': {'live': True}}}
CONFIG_BACKTEST = {
    **CONFIG_DEFAULT, **{'cerebro': {'live': False}}}
CONFIG_OPTIMIZE = {
    **CONFIG_DEFAULT, **CONFIG_BACKTEST,
    **{'cerebro': {'optreturn': False}}}

# default module paths
PATH_COMMINFO = ['backtrader.commissions']
PATH_SIZER    = ['backtrader.sizers']
PATH_ANALYZER = ['backtrader.analyzers', 'btconfig.analyzers']
PATH_OBSERVER = ['backtrader.observers', 'btconfig.observers']
PATH_STORE    = ['backtrader.stores', 'btconfig.stores']
PATH_FEED     = ['backtrader.feeds', 'btconfig.feeds']
PATH_STRATEGY = []

# default search paths for classes
PATH_BTCONF_PART = ['btconfig.parts']

# default different parts to load
LOAD_BTCONF_PART = ['PartBacktrader', 'PartCerebro', 'PartCommInfo',
                    'PartDatas', 'PartLogging', 'PartPlot', 'PartSizer',
                    'PartStores', 'PartStrategy', 'PartReport',
                    'PartTearsheet']

instances = []


class BTConfig:

    parts_thread_lock = Lock()

    def __init__(self, mode: int = None, configfile: str = None,
                 add_local_paths: bool = True) -> None:
        '''
        Initialization
        '''
        global instances
        instances.append(self)
        # misc vars
        self._filename = configfile  # filename of config
        self._config = None          # complete configuration
        self._parts = {}             # all loaded parts
        # global vars
        self.logger = logging.getLogger('btconfig')
        self.cerebro = None          # cerebro instance
        self.mode = mode             # current mode
        self.config = None           # current configuration
        self.stores = {}             # current stores available
        self.datas = {}              # current data sources
        self.result = []             # store execution result
        self.duration = None         # duration of last execution

        # paths
        self.PATH_COMMINFO = PATH_COMMINFO.copy()
        self.PATH_SIZER    = PATH_SIZER.copy()
        self.PATH_ANALYZER = PATH_ANALYZER.copy()
        self.PATH_OBSERVER = PATH_OBSERVER.copy()
        self.PATH_STORE    = PATH_STORE.copy()
        self.PATH_FEED     = PATH_FEED.copy()
        self.PATH_STRATEGY = PATH_STRATEGY.copy()
        self.PATH_BTCONF_PART = PATH_BTCONF_PART.copy()
        self.LOAD_BTCONF_PART = LOAD_BTCONF_PART.copy()
        if add_local_paths:
            self.PATH_COMMINFO.append('commissions')
            self.PATH_SIZER.append('sizers')
            self.PATH_ANALYZER.append('analyzers')
            self.PATH_OBSERVER.append('observers')
            self.PATH_STORE.append('stores')
            self.PATH_FEED.append('feeds')
            self.PATH_STRATEGY.append('strategies')

    def _loadParts(self) -> None:
        '''
        Loads all available parts
        '''
        all_classes = get_classes(self.PATH_BTCONF_PART)
        for classname in self.LOAD_BTCONF_PART:
            if classname not in all_classes:
                raise Exception(f'Part {classname} not found')
            self._parts[classname] = all_classes[classname](self)

    def _getParts(self) -> list:
        '''
        Returns a sorted list of all available parts
        '''
        keys = sorted(
            self._parts,
            key=lambda x: self._parts[x].PRIORITY,
            reverse=False)
        return [self._parts[x] for x in keys]

    def _getConfigForMode(self, mode: int) -> dict:
        '''
        Returns the config for the given mode

            Args:
            -----
            - mode (int): The mode the config will be generated for

            Returns:
            --------
            dict
        '''
        # use default config based on mode and merge with config
        res = deepcopy(self._config)
        if mode == MODE_LIVE:
            merge_dicts(res, CONFIG_LIVE)
            merge_dicts(res, res.get('_live', {}))
        elif mode == MODE_BACKTEST:
            merge_dicts(res, CONFIG_BACKTEST)
            merge_dicts(res, res.get('_backtest', {}))
        elif mode in [MODE_OPTIMIZE, MODE_OPTIMIZEGENETIC]:
            merge_dicts(res, CONFIG_OPTIMIZE)
            merge_dicts(res, res.get('_backtest', {}))
            merge_dicts(res, res.get('_optimize', {}))
        else:
            raise Exception('Unknown mode provided')
        # remove override sections
        for v in ['_live', '_backtest', '_optimize']:
            if v in res:
                del(res[v])
        # return config for given mode
        return res

    def _prepare(self, mode: int, configfile: str) -> None:
        '''
        Initialization of btconfig using a config file

            Args:
            -----
            - mode (int): Optional, the mode to execute
            - configfile (str): Optional, configfile to use

            Returns:
            --------
            None
        '''
        # load config from filename
        if configfile is not None:
            self._filename = configfile
        if self._filename:
            with open(self._filename, 'r') as file:
                self._config = json.load(file)
        if self._config is None:
            raise Exception('No config provided')
        merge_dicts(self._config, CONFIG_DEFAULT)
        # store time at which btconfig was initialized
        self._config['common']['time'] = datetime.now()

        # set mode
        if mode is not None:
            self.mode = mode
        if self.mode is None:
            raise Exception('No run mode defined')
        # set config for mode
        self.config = self._getConfigForMode(self.mode)

        # set empty dicts
        self.stores = {}
        self.datas = {}

        # reset result
        self.result = []

    def _setup(self) -> None:
        '''
        Sets all parts

            Returns:
            --------
            None
        '''
        for p in self._getParts():
            p.setup()

    def _run(self) -> None:
        '''
        Runs all parts

            Returns:
            --------
            None
        '''
        t = time.process_time()
        res = []
        for p in self._getParts():
            tmp = p.run()
            if tmp is None:
                continue
            if not isinstance(tmp, list):
                continue
            if not len(tmp):
                continue
            res.extend(tmp)
        self.result = res
        self.duration = time.process_time() - t

    def _finish(self) -> None:
        '''
        Finishes execution

            Returns:
            --------
            None
        '''
        for p in self._getParts():
            p.finish(self.result)

    def setConfig(self, config):
        '''
        Sets the config dict
        '''
        self._config = config

    def run(self, mode: int = None, configfile: str = None) -> None:
        '''
        Runs backtrader
        '''
        with BTConfig.parts_thread_lock:
            # load different parts of btconfig
            self._loadParts()
            # prepare and setup everything also run strategy
            self._prepare(mode, configfile)
            self.log('Preparing execution\n')
            self._setup()
        self.log('All parts set up and configured, running strategy\n')
        self._run()
        duration = timedelta(seconds=self.duration)
        self.log(f'Strategy executed in {duration}, finishing execution\n')
        self._finish()

    def log(self, txt: str, level: int = logging.INFO) -> None:
        '''
        Logs text

            Args:
            -----
            - txt (str): The text to log
            - level (int): The log level

            Returns:
            --------
            None
        '''
        if self.config is None:
            raise Exception('No config loaded')
        if self.config['common'].get('create_log', False):
            self.logger.log(level, txt)


class BTConfigPart:

    PRIORITY = 0

    def __init__(self, instance: BTConfig) -> None:
        '''
        Initialization
        '''
        self._instance = instance
        self.prepare()

    def prepare(self):
        '''
        Prepare method
        '''
        pass

    def log(self, txt: str, level: int = logging.INFO) -> None:
        '''
        Logs messages
        '''
        self._instance.log(txt, level)

    def setup(self) -> None:
        '''
        Sets up part
        '''
        pass

    def run(self):
        '''
        Runs the part
        '''
        pass

    def finish(self, result) -> None:
        '''
        Finishes part execution
        '''
        pass


class BTConfigDataloader:

    PREFIX = None

    def __init__(self,
                 instance: BTConfig,
                 data_id: str,
                 cfg: dict,
                 tz: str) -> None:
        '''
        Initialization
        '''
        self._cls = bt.feeds.GenericCSVData
        self._instance = instance
        self._data_id = data_id
        self._cfg = cfg
        self._tz = tz
        self._additional = []
        self._filename = None
        self._filelen = 0
        self._filedate = None
        self._setFile()
        self._prepare()

    def _setFile(self):
        '''
        Sets the file for dataloader source
        '''
        commoncfg = self._instance.config.get('common', {})
        path = commoncfg.get('data_path', './data')
        dataname = self._cfg['dataname']
        fromdate = self._cfg.get('fromdate', None)
        todate = self._cfg.get('todate', None)
        backfill_days = self._cfg.get('backfill_days', None)
        if backfill_days:
            fromdate = None
            todate = None
        # filename
        file_args = ([self.PREFIX]
                     + self._additional
                     + [dataname,
                        self._cfg['granularity'][0],
                        self._cfg['granularity'][1],
                        fromdate, todate, backfill_days])
        file_args = [str(x) for x in file_args]
        filename = f'{"_".join(file_args)}.csv'
        filename = os.path.join(path, filename)
        self._filename = filename
        try:
            data = pd.read_csv(filename, parse_dates=[0])
            self._filelen = len(data)
            self._filedate = data.iloc[-1]['datetime']
        except IOError:
            self._filelen = 0
            self._filedate = None

    def _updateFile(self, data):
        if data is None or not len(data):
            return
        if not os.path.isdir(os.path.dirname(self._filename)):
            os.makedirs(os.path.dirname(self._filename))
        if self._filelen == 0:
            data.to_csv(
                self._filename, index=False)
        else:
            data.set_index('datetime', inplace=True)
            data = data[self._filedate:].iloc[1:]
            if len(data):
                data.to_csv(
                    self._filename, index=True,
                    header=None, mode='a')
            data.reset_index(inplace=True)
        if len(data):
            self._filelen += len(data)
            self._filedate = data.iloc[-1]['datetime']

    def _createFeed(self):
        commoncfg = self._instance.config.get('common', {})
        dtnow = commoncfg.get('time', None)
        params = get_data_params(self._cfg, self._tz, dtnow)
        params['dataname'] = self._filename
        params['headers'] = True
        params['dtformat'] = parse_dt
        data = self._cls(**params)
        return data

    def _prepare(self):
        '''
        Prepare method

        This method can be overwritten to prepare
        needed functionality.
        '''
        pass

    def _loadData(self):
        '''
        Load data method
        '''
        pass

    def log(self, txt: str, level: int = logging.INFO) -> None:
        '''
        Logs messages
        '''
        self._instance.log(txt, level)

    def getData(self, fromdate=None, todate=None) -> pd.DataFrame:
        '''
        Returns the data
        '''
        data = self._updateFile(self._loadData())
        if fromdate or todate:
            data.set_index('datetime', inplace=True)
            if fromdate:
                data = data[fromdate:]
            if todate:
                data = data[:todate]
            data.reset_index(inplace=True)
        return data

    def createDataFeed(self):
        '''
        Returns the data feed
        '''
        self._updateFile(self._loadData())
        return self._createFeed()


class BTConfigApiClient:

    def __init__(self, base_url, headers={}, debug=False, pause=0):
        '''
        Initialization
        '''
        self.base_url = base_url
        self.headers = headers
        self.debug = debug
        self.pause = pause

    def _getUrl(self, path, **kwargs):
        '''
        Returns the complete api url
        '''
        params = '?' + urlencode(kwargs) if len(kwargs) else ''
        url = self.base_url + path + params
        return url

    def _request(self, path, exceptions=True, json=False, **kwargs):
        '''
        Runs a request to the given api path
        '''
        url = self._getUrl(path, **kwargs)
        response = self._requestUrl(url)
        if response.status_code == 200:
            if json:
                return response.json()
        else:
            if exceptions:
                raise Exception(f'{url}: {response.text}')
            if json:
                return []
        return response

    def _requestUrl(self, url):
        '''
        Runs a request to the given url
        '''
        if self.debug:
            print('Requesting', url)
        response = requests.get(url, headers=self.headers)
        if self.pause != 0:
            pause = self.pause
            if pause == -1:
                pause = random.randint(2, 5)
            time.sleep(pause)
        return response


def run(mode: int = None, configfile: str = None) -> BTConfig:
    '''
    Runs the strategy

    Main method to setup backtrader and run a strategy
    using configuration from a configfile.

        Args:
        -----
        - mode (int): Optional, the mode to run
        - configfile (str): Optional, configfile to use

        Returns:
        --------
        BTConfig
    '''
    config = BTConfig()
    config.run(mode, configfile)
    return config


def run_live(configfile: str = None) -> BTConfig:
    '''
    Shortcut method to execute live mode

        Args:
        -----
        - configfile (str): Config filename to use

        Returns:
        --------
        BTConfig
    '''
    return run(MODE_LIVE, configfile)


def run_backtest(configfile: str = None) -> BTConfig:
    '''
    Shortcut method to execute backtest mode

        Args:
        -----
        - configfile (str): Config filename to use

        Returns:
        --------
        BTConfig
    '''
    return run(MODE_BACKTEST, configfile)


def run_optimize(configfile: str = None) -> BTConfig:
    '''
    Shortcut method to execute optimization mode

        Args:
        -----
        - configfile (str): Config filename to use

        Returns:
        --------
        BTConfig
    '''
    return run(MODE_OPTIMIZE, configfile)


def run_optimizegenetic(configfile: str = None) -> BTConfig:
    '''
    Shortcut method to execute genetic optimization mode

        Args:
        -----
        - configfile (str): Config filename to use

        Returns:
        --------
        BTConfig
    '''
    return run(MODE_OPTIMIZEGENETIC, configfile)
