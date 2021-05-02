from __future__ import division, absolute_import, print_function

import os
import logging
import btconfig

from telegram.ext import Updater
from btplotting.tabs.log import init_log_tab


class PartLogging(btconfig.BTConfigPart):
    '''
    Sets up logging functionality

        Params:
        -------
        - enabled: Is logging enabled
        - log_to_console: Should log entries be logged to console
        - log_to_file: Should log entries be logged to file
        - log_to_telegram: Should log entries be logged to telegram
        - telegram: dict with config (token, whitelist, blacklist)
        - level: Log level to use

        Config Example:
        ---------------
        "common": {
            "log_path": "./logs"
        },
        "logging": {
            "enabled": true,
            "log_to_console": true,
            "log_to_file": true,
            "log_to_telegram": false,
            "telegram": {
                "token": "",
                "whitelist": [],
                "blacklist": []
            },
            "level": "INFO"
        }
    '''

    PRIORITY = 10

    def setup(self) -> None:
        logcfg = self._instance.config.get('logging', {})
        commoncfg = self._instance.config.get('common', {})
        path = commoncfg.get('log_path', './logs')
        level = logcfg.get('level', 'INFO')
        logconsole = logcfg.get('log_to_console', True)
        logfile = logcfg.get('log_to_file', True)
        logtelegram = logcfg.get('log_to_telegram', False)
        enabled = logcfg.get('enabled', True)
        if not enabled:
            return
        # set default log level
        self._instance.logger.setLevel(level)
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
        # add telegram handler
        if logtelegram:
            telegramcfg = logcfg.get('telegram', {})
            token = telegramcfg.get('token', '')
            self.telegramupdater = Updater(
                token, use_context=True)
            self.telegramupdater.start_polling()
            #self.telegramupdater.idle()

            telegram = TelegramHandler(self.telegramupdater)
            logging.getLogger().addHandler(telegram)
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


class TelegramHandler(logging.Handler):

    def __init__(self, updater, level=logging.NOTSET):
        super(TelegramHandler, self).__init__(level=level)
        self.updater = updater

    def emit(self, record):
        message = record.msg
        print("MESSAGE", message)
