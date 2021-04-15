from __future__ import division, absolute_import, print_function

import os
import logging
import btconfig

from btplotting.tabs.log import init_log_tab


class PartLogging(btconfig.BTConfigPart):
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

    PRIORITY = 10

    def setup(self) -> None:
        logcfg = self._instance.config.get('logging', {})
        commoncfg = self._instance.config.get('common', {})
        enabled = logcfg.get('enabled', True)
        level = logcfg.get('level', 'INFO')
        logconsole = logcfg.get('log_to_console', True)
        logfile = logcfg.get('log_to_file', True)
        path = logcfg.get('path', './logs')
        # check if logging is enabled
        if not enabled:
            return

        # set default log level
        self._instance._logger.setLevel(level)
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
        if 'ProtoStrategy' in self._instance.config['strategy']:
            config = self._instance.config['strategy']['ProtoStrategy']
            config['use_logging'] = True
        # initialize btplotting logger
        init_log_tab(['btconfig'])
        # log execution
        self.log('Backtrader btconfig execution {}\n'.format(
            commoncfg['time'].strftime('%Y-%m-%d %H:%M:%S')
        ))
        self.log('Logging started\n', logging.INFO)
