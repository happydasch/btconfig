"""
Backtrader setup running lib with support for config files

The backtrader system will be configured and set up by using config files.
The possible configuration options are described below.


Intention
---------

The intention of btconfig is to provide a basic framework for automatic
strategy setup using a config file. This allows to collect different
strategies, indicators, etc. and to setup and execute a strategy in different
execution modes:
live, backtest, optimization.

Every execution mode can set different settings for data sources, parts to
use and so on.


How to run
----------

To execute a strategy you first need to create a config file.

If a config file is available:
btconfig.execute(mode, configfile)

where mode is either live, backtest or optimize and configfile
is the filename of the config file.

Additional seearch paths and settings can be changed before executing.

import btconfig

if __name__ == '__main__':
    btconfig.execute(btconfig.MODE_BACKTEST, "config.json")


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
    are differentiated by the store_name.

    * store_name (string: dict): Configuration for a single store

    The following stores are supported:

    * oandav20: Oanda V20
    * ib: Interactive Brokers

    Every store can individually be configured by providing
    different params in the dict.

See btconfig.parts.store for more details

#### [feeds]
Configuration for data feeds of strategy

    * feed_name (string: list): Configuration for a single feed
      Where list expects the values:
      [Timeframe, Compression, Method, Options]

See btconfig.parts.data for more details

#### [datas]
Configuration for data sources

    * identifier (string: dict)
      Where dict contains data config values

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
    * path (string): Path for backtest output
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
        * valuename (string/number): Set common strategy param to given value

    ForexProtoStrategy:
    Configuration for forex prototype strategy
        * valuename (string/number): Set common strategy param to given value

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

import json
import logging

from datetime import datetime

from .helper import merge_dicts
from .proto import ProtoStrategy, ForexProtoStrategy  # noqa: F401

# dev info
__author__ = "Daniel Schindler <daniel@vcard24.de>"
__status__ = "development"

# constants
TIMEFORMAT = '%Y-%m-%dT%H:%M:%S'
NUMBERFORMAT = '0,0.000[000]'
MODE_LIVE, MODE_BACKTEST, MODE_OPTIMIZE = range(3)
MODES = ['LIVE', 'BACKTEST', 'OPTIMIZE']

# default config dicts
CONFIG_DEFAULT = {
    'common': {}, 'cerebro': {}, 'stores': {}, 'broker': {},
    'datas': {}, 'feeds': {}, 'sizer': {}, 'comminfo': {},
    'plot': {}, 'logging': {}, 'analyzers': {}, 'strategy': {},
    '_live': {}, '_backtest': {}, '_optimize': {}}
CONFIG_LIVE = {**CONFIG_DEFAULT, **{
    'cerebro': {'stdstats': False, 'live': True}}}
CONFIG_BACKTEST = {**CONFIG_DEFAULT, **{
    'cerebro': {'stdstats': False,
                'live': False,
                'optreturn': False,
                'tradehistory': True}}}
CONFIG_OPTIMIZE = {**CONFIG_DEFAULT, **CONFIG_BACKTEST}

# default search paths for classes
PATH_COMMINFO = ['commissions',
                 'backtrader.commissions',
                 'btoandav20.commissions']
PATH_SIZER = ['sizers', 'backtrader.sizers', 'btoandav20.sizers']
PATH_ANALYZER = ['analyzers', 'backtrader.analyzers', 'btconfig.analyzers']
PATH_OBSERVER = ['observers', 'backtrader.observers', 'btconfig.observers']
PATH_STRATEGY = ['strategies']

# misc vars
logger = logging.getLogger('btconfig')
filename = None         # filename of config
config = None           # complete configuration
result = None           # store execution result
initialized = False     # is btconfig initialized

# global vars
cerebro = None     # cerebro instance
cmode = None       # current mode
cconfig = None     # current configuration
cstores = {}       # current stores available
cdatas = {}        # current data sources


def initialize(mode: int = None, configfile: str = None) -> None:
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
    global filename, initialized, config, result
    global cconfig, cmode, cstores, cdatas

    # reset result
    result = None
    # load config from filename
    if configfile is not None:
        filename = configfile
    if filename is None:
        raise Exception('No config file defined')
    with open(filename, 'r') as file:
        config = json.load(file)
    merge_dicts(config, CONFIG_DEFAULT)
    # store time when btconfig was initialized
    config['common']['time'] = datetime.now()
    # create config for mode
    if mode is not None:
        cmode = mode
    if cmode is None:
        raise Exception('No run mode defined')
    cconfig = _get_config(mode)
    # set empty dicts
    cstores = {}
    cdatas = {}
    # mark as initialized
    initialized = True


def execute(mode: int = None, configfile: str = None) -> None:
    '''
    Executes the strategy

    Main method to setup backtrader and execute a strategy
    using configuration from a configfile.

    Args:
    -----
    - mode (int): Optional, the mode to execute
    - configfile (str): Optional, configfile to use

    Returns:
    --------
    None
    '''
    if not initialized:
        initialize(mode, configfile)
    _setup()
    _finish()


def run_live(configfile: str = None) -> None:
    '''
    Shortcut method to execute live mode

    Args:
    -----
    - configfile (str): Config filename to use

    Returns:
    --------
    None
    '''
    execute(MODE_LIVE, configfile)


def run_backtest(configfile: str = None) -> None:
    '''
    Shortcut method to execute backtest mode

    Args:
    -----
    - configfile (str): Config filename to use

    Returns:
    --------
    None
    '''
    execute(MODE_BACKTEST, configfile)


def run_optimize(configfile: str = None) -> None:
    '''
    Shortcut method to execute optimization mode

    Args:
    -----
    - configfile (str): Config filename to use

    Returns:
    --------
    None
    '''
    execute(MODE_OPTIMIZE, configfile)


def log(txt: str, level: int = logging.INFO) -> None:
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
    global logger, cconfig
    if cconfig is None:
        raise Exception('No config loaded')
    if cconfig['logging'].get('enabled', True):
        logger.log(level, txt)
    else:
        print(txt)


def _setup() -> None:
    '''
    Sets all parts of backtrader

    Returns:
    --------
    None
    '''
    from .parts import (
        setup_logging, setup_cerebro,
        setup_backtrader, setup_stores,
        setup_datas, setup_sizer,
        setup_comminfo, setup_strategy,
        setup_plot)

    setup_logging()
    setup_cerebro()
    setup_backtrader()
    setup_stores()
    setup_datas()
    setup_sizer()
    setup_comminfo()
    setup_strategy()
    setup_plot()


def _finish():
    '''
    Finishes execution of backtrader

    Returns:
    --------
    None
    '''
    from .parts import (
        finish_plot, finish_backtrader)

    global result
    result = cerebro.run()
    finish_backtrader(result)
    finish_plot(result)


def _get_config(mode: int) -> dict:
    '''
    Returns the config for the given mode

    Args:
    -----
    - mode (int): The mode the config will be generated for

    Returns:
    --------
    dict
    '''
    global config
    # use default config based on mode and merge with config
    if mode == MODE_LIVE:
        res = CONFIG_LIVE
        merge_dicts(res, config.get('_live', {}))
    elif mode == MODE_BACKTEST:
        res = CONFIG_BACKTEST
        merge_dicts(res, config.get('_backtest', {}))
    elif mode == MODE_OPTIMIZE:
        res = CONFIG_OPTIMIZE
        merge_dicts(res, config.get('_backtest', {}))
        merge_dicts(res, config.get('_optimize', {}))
    else:
        raise Exception('Unknown mode provided')
    merge_dicts(res, config)
    # remove override sections
    for v in ['_live', '_backtest', '_optimize']:
        if v in res:
            del(res[v])
    # return config for given mode
    return res
