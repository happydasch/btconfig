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

    Every execution mode can set different settings for data sources, parts to
    use and so on.

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
        * broker (string): The broker to use
        * cash (float): The start amount of cash
        * log_path (str): Path for log files
        * report_path (str): Path for backtest files
        * data_path (str): Path for data files

    #### [logging]
    Configuration for logging

        * enabled (bool): Should logging be enabled (true/false)
        * console (bool): Should log entries be logged to console (true/false)
        * file (bool): Should log entries be logged into files (true/false)
        * level (string): Log level to log (ex. "INFO")
        * file_path (string): Path for file logs (ex. "./logs")

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
        * plot_volume (bool): Should volume be added to plotting (true/false)
        * bar_dist (float): Distance of markers to bars (ex. 0.0003)
        * style (string): Plot style for bars (ex. "candle")
        * combine (bool): Should different feeds be combined to a
        single plot (true/false)
        * web_port (int): Web port for btplotting (ex. 80)
        * live_lookback (int): Lockback of bars for live plotting (ex. 50)

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

from datetime import datetime

import json
import logging

from .helper import get_classes, merge_dicts

# dev info
__author__ = 'Daniel Schindler <daniel@vcard24.de>'
__status__ = 'development'

# constants
TIMEFORMAT = '%Y-%m-%dT%H:%M:%S'
NUMBERFORMAT = '0,0.000[000]'
MODES = ['LIVE', 'BACKTEST', 'OPTIMIZE']
MODE_LIVE, MODE_BACKTEST, MODE_OPTIMIZE = range(3)

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
CONFIG_OPTIMIZE = {**CONFIG_DEFAULT, **CONFIG_BACKTEST}


class BTConfig:

    # default module paths
    PATH_COMMINFO = [
        'commissions',
        'backtrader.commissions',
        'btoandav20.commissions']
    PATH_SIZER = [
        'sizers',
        'backtrader.sizers',
        'btoandav20.sizers']
    PATH_ANALYZER = [
        'analyzers',
        'backtrader.analyzers',
        'btconfig.analyzers']
    PATH_OBSERVER = [
        'observers',
        'backtrader.observers',
        'btconfig.observers']
    PATH_STORE = [
        'backtrader.stores',
        'btoandav20.stores',
        'ccxtbt.ccxtstore']
    PATH_DATA = [
        'backtrader.feeds',
        'btoandav20.feeds',
        'ccxtbt.ccxtfeed',
        'btconfig.feeds']
    PATH_STRATEGY = ['strategies']
    # default search paths for classes
    PATH_BTCONF_PART = ['btconfig.parts']
    # default different parts to load
    LOAD_BTCONF_PART = ['PartBacktrader', 'PartCerebro', 'PartCommInfo',
                        'PartDatas', 'PartLogging', 'PartPlot', 'PartSizer',
                        'PartStores', 'PartStrategy']

    def __init__(self, mode: int = None, configfile: str = None) -> None:
        '''
        Initialization
        '''
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
        if mode == MODE_LIVE:
            res = CONFIG_LIVE
            merge_dicts(res, self._config.get('_live', {}))
        elif mode == MODE_BACKTEST:
            res = CONFIG_BACKTEST
            merge_dicts(res, self._config.get('_backtest', {}))
        elif mode == MODE_OPTIMIZE:
            res = CONFIG_OPTIMIZE
            merge_dicts(res, self._config.get('_backtest', {}))
            merge_dicts(res, self._config.get('_optimize', {}))
        else:
            raise Exception('Unknown mode provided')
        merge_dicts(res, self._config)
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
        if self._filename is None:
            raise Exception('No config file defined')
        with open(self._filename, 'r') as file:
            self._config = json.load(file)
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
        Sets all parts of backtrader

            Returns:
            --------
            None
        '''
        for p in self._getParts():
            p.setup()

    def _finish(self) -> None:
        '''
        Finishes execution of backtrader

            Returns:
            --------
            None
        '''
        self.result = self.cerebro.run()
        if not len(self.result):
            return
        for p in self._getParts():
            p.finish(self.result)

    def run(self, mode: int = None, configfile: str = None) -> None:
        '''
        Runs backtrader
        '''
        # load different parts of btconfig
        self._loadParts()
        # prepare and setup everything also run strategy
        self._prepare(mode, configfile)
        self._setup()
        self.log('All parts set up and configured, running backtrader\n')
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
        if self.config['logging'].get('enabled', True):
            self.logger.log(level, txt)
        else:
            print(txt)


class BTConfigPart:

    PRIORITY = 0

    def __init__(self, instance: BTConfig) -> None:
        '''
        Initialization
        '''
        self._instance = instance

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

    def finish(self, result) -> None:
        '''
        Finishes part execution
        '''
        pass


class BTConfigDataloader:

    def __init__(self,
                 instance: BTConfig,
                 data_id: str,
                 cfg: dict,
                 tz: str) -> None:
        '''
        Initialization
        '''
        self._instance = instance
        self._data_id = data_id
        self._cfg = cfg
        self._tz = tz

    def log(self, txt: str, level: int = logging.INFO) -> None:
        '''
        Logs messages
        '''
        self._instance.log(txt, level)

    def load(self):
        '''
        Loads a custom data source
        '''
        raise Exception('Method load needs to be overwritten')


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
