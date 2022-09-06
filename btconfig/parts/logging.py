from __future__ import division, absolute_import, print_function

import os
import logging
import btconfig
import telethon.sync  # noqa: * keep for async->sync wrapper

from telethon import TelegramClient
from btplotting.tabs.log import init_log_tab


class PartLogging(btconfig.BTConfigPart):
    '''
    Sets up logging functionality

        Params:
        -------
        - log_to_console: Should log entries be logged to console
        - log_to_file: Should log entries be logged to file
        - log_to_telegram: Should log entries be logged to telegram
        - telegram: dict with config
            chat_id, token, api_id, api_hash, whitelist, blacklist
        - level: Log level to use

        Config Example:
        ---------------
        "common": {
            "create_log": true,
            "log_path": "./logs"
        },
        "logging": {
            "log_to_console": true,
            "log_to_file": true,
            "log_to_telegram": false,
            "telegram": {
                "chat_id": [],
                "token": "",
                "api_id: "",
                "api_hash": "",
                "whitelist": [],
                "blacklist": []
            },
            "level": "INFO"
        }
    '''

    PRIORITY = 10

    def setup(self) -> None:
        if len(btconfig.instances) > 1:
            return
        commoncfg = self._instance.config.get('common', {})
        if not commoncfg.get('create_log', False):
            return
        logger = self._instance.logger
        logcfg = self._instance.config.get('logging', {})
        path = commoncfg.get('log_path', './logs')
        if not os.path.isdir(path):
            os.makedirs(path)
        level = logcfg.get('level', 'INFO')
        logconsole = logcfg.get('log_to_console', True)
        logfile = logcfg.get('log_to_file', True)
        logtelegram = logcfg.get('log_to_telegram', False)
        # set default log level
        logger.setLevel(level)
        # add console handler
        if logconsole:
            console = logging.StreamHandler()
            logger.addHandler(console)
        else:
            logger.addHandler(logging.NullHandler())
        # add file handler
        if logfile:
            strategy = commoncfg['strategy']
            exectime = commoncfg['time'].strftime(btconfig.FILE_TIMEFORMAT)
            filename = os.path.join(
                path, 'log_{}_{}.txt'.format(
                    strategy, exectime))
            file = logging.FileHandler(filename=filename, encoding="UTF-8")
            file.setLevel(level)
            logger.addHandler(file)
        # add telegram handler
        if logtelegram:
            telegramcfg = logcfg.get('telegram', {})
            telegram = TelegramHandler(telegramcfg)
            logger.addHandler(telegram)
            self._instance.telegram_handler = telegram
        # enable logging in strategy
        if 'ProtoStrategy' in self._instance.config['strategy']:
            config = self._instance.config['strategy']['ProtoStrategy']
            config['use_logging'] = True
        # initialize btplotting logger
        init_log_tab(['btconfig'])
        # log execution
        self.log('Backtrader btconfig execution {}\n'.format(
            commoncfg['time'].strftime(btconfig.TIMEFORMAT)
        ))
        self.log('Logging started\n', logging.INFO)


class TelegramHandler(logging.Handler):

    def __init__(self, cfg, level=logging.NOTSET):
        super(TelegramHandler, self).__init__(level=level)
        self.cfg = cfg
        self.token = self.cfg.get('token', '')
        self.api_id = self.cfg.get('api_id', '')
        self.api_hash = self.cfg.get('api_hash', '')
        self.chat_id = self.cfg.get('chat_id', [])
        self.whitelist = self.cfg.get('whitelist', [])
        self.blacklist = self.cfg.get('blacklist', [])
        self.client = None
        self._createTelegram()

    def _createTelegram(self):
        self.client = TelegramClient('logger', self.api_id, self.api_hash)
        self.client.start(bot_token=self.token)

    def send_message(self, msg=None, image=None):
        for c in self.chat_id:
            if msg is not None:
                self.client.send_message(c, msg, file=image)
            elif image is not None:
                self.client.send_file(c, image)

    def send_file(self, filename):
        for c in self.chat_id:
            self.client.send_file(c, filename)

    def emit(self, record):
        if not len(self.whitelist) and not len(self.blacklist):
            return
        msg = record.msg
        if len(self.whitelist):
            found = False
            for x in self.whitelist:
                if x in msg:
                    found = True
                    break
            if not found:
                return
        if len(self.blacklist):
            found = False
            for x in self.blacklist:
                if x in msg:
                    found = True
                    break
            if found:
                return
        self.send_message(msg)
