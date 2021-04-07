from __future__ import division, absolute_import, print_function

import os
import logging

from btconfig import log, logger, cconfig
from btplotting.tabs.log import init_log_tab


def setup_logging() -> None:
    '''
    Sets up logging functionality

    Params:
    -------
    - enabled: Is logging enabled
    - console: Should log entries be logged to console
    - file: Should log entries be logged to file
    - level: Log level to use
    - file_path: Path for file logs

    Config Example:
    ---------------
    "logging": {
        "enabled": true,
        "log_to_console": true,
        "log_to_file": true,
        "level": "INFO",
        "path": "./logs"
    }
    '''
    logcfg = cconfig.get('logging', {})
    commoncfg = cconfig.get('common', {})
    enabled = logcfg.get('enabled', True)
    level = logcfg.get('level', 'INFO')
    logconsole = logcfg.get('log_to_console', True)
    logfile = logcfg.get('log_to_file', True)
    path = logcfg.get('path', './logs')
    # check if logging is enabled
    if not enabled:
        return
    # set default log level
    logger.setLevel(level)
    # add console handler
    if logconsole:
        console = logging.StreamHandler()
        logging.getLogger().addHandler(console)
    else:
        logging.basicConfig(handlers=[logging.NullHandler()])
    # add file handler
    if logfile:
        strategy = commoncfg['strategy']
        exectime = commoncfg['time'].strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(
            path, 'log_{}_{}.txt'.format(
                strategy, exectime))
        file = logging.FileHandler(filename=filename)
        file.setLevel(level)
        logging.getLogger().addHandler(file)
    # enable logging in strategy
    cconfig['ProtoStrategy']['use_logging'] = True
    # initialize btplotting logger
    init_log_tab(['strategy'])
    # log execution
    log('Logging started\n', logging.INFO)
