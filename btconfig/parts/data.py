from __future__ import division, absolute_import, print_function

import logging
import btconfig
import backtrader as bt

from tabulate import tabulate
from btconfig.helper import get_classes, get_data_params


class PartDatas(btconfig.BTConfigPart):
    '''
    Sets up data sources and feeds

    All data sources will be created and after that
    all configured feeds will be created.

        Params:
        -------
        For datas:
            - classname (str): Classname of data source
            - store (str): store id to use (only if classname is not set)
            - dataname (str): Dataname of data source
            - sessionstart: [hour, minute, second, microsecond]
            - sessionend: [hour, minute, second, microsecond]
            - granularity: [timeframe, compression]
            - for (list): List of feed names this data source is used with
            - params (dict): Custom data source params

        All data sources support some common backtrader options.
        Custom data source configuration is being done using params.

        For feeds:
            - timeframe (str): Timeframe as string
            - compression (int): Compression
            - method (str): Possible values: replay, resample, add
            - options (dict): Custom data options

        A data feed is a data source that is being used in backtrader.

        Config Example:
        ---------------
        The following examples creates a data source type data
        and sets the primary data feed from created data source:

        "common": {
            "data_path": "./data"
        },
        "datas": {
            "data_id": {
                "classname": "ClassName",
                "dataname": "name",
                "sessionstart": [22, 0, 0, 0],
                "sessionend": [21, 59, 59, 999999],
                "granularity": ["Minutes", 5],
                "params": {
                    # additional params for feed
                },
                "for": ["primary"]
            },
        },
        "feeds": {
            "primary": {"Minutes", 1, "resample", {}}
        }

        The feed named primary will be available in the strategy as datas0
    '''

    PRIORITY = 50

    def __init__(self, instance: btconfig.BTConfig) -> None:
        '''
        Initialization
        '''
        super(PartDatas, self).__init__(instance)
        self.all_classes = get_classes(self._instance.PATH_FEED)

    def setup(self) -> None:
        feedscfg = self._instance.config.get('feeds', {}).copy()
        datascfg = self._instance.config.get('datas', {})
        commoncfg = self._instance.config.get('common', {})
        tz = commoncfg.get('timezone', None)
        for did in datascfg:
            dcfg = datascfg[did]
            # create and store data source
            data = self._createData(did, dcfg, tz)
            if data is None:
                raise Exception('Data was not created')
            self._instance.datas[did] = data
            # check for feeds
            if not len(dcfg.get('for', [])):
                continue
            # create all feeds
            for fid in dcfg['for']:
                if fid not in feedscfg:
                    txt = f'Feed {fid} is already set or does not exist'
                    self.log(txt, logging.DEBUG)
                    continue
                fcfg = feedscfg[fid]
                self._instance.datas[fid] = self._createFeed(data, fid, fcfg)
                # remove created feed so already created feeds don't
                # get recreated by other data sources
                del(feedscfg[fid])
        self.log('Datas created\n', logging.INFO)

    def _createData(
            self,
            data_id: str,
            cfg: dict,
            tz: str) -> bt.AbstractDataBase:
        '''
        Creates and returns the data source from config

        Args:
        -----
        - cfg (dict)
        - tz (str)

        Returns:
        --------
        bt.AbstractDataBase
        '''
        commoncfg = self._instance.config.get('common', {})
        dtnow = commoncfg.get('time', None)
        dargs = get_data_params(cfg, tz, dtnow)
        classname = cfg.get('classname')
        if classname and classname not in self.all_classes:
            raise Exception(f'Data {classname} not found')
        store = cfg.get('store')
        if store and store not in self._instance.stores:
            raise Exception(f'Store {store} not found')
        if classname:
            if issubclass(
                    self.all_classes[classname],
                    btconfig.BTConfigDataloader):
                self.log('Creating Dataloader {} ({})\n{}'.format(
                        classname, data_id,
                        tabulate(dargs.items(), tablefmt='plain')),
                    logging.DEBUG)
                loader = self.all_classes[classname](
                    self._instance, data_id, cfg, tz)
                d = loader.load()
            else:
                self.log('Creating Data {} ({})\n{}'.format(
                        classname, data_id,
                        tabulate(dargs.items(), tablefmt='plain')),
                    logging.DEBUG)
                d = self.all_classes[classname](**dargs)
        elif store:
            self.log('Creating Data from Store {} ({})\n{}'.format(
                    store,
                    data_id,
                    tabulate(dargs.items(), tablefmt='plain')),
                logging.DEBUG)
            d = self._instance.stores[store].getdata(**dargs)
        else:
            raise Exception('No valid data configuration')
        self.log(f'Data {data_id} created', logging.INFO)
        return d

    def _createFeed(
            self,
            data: bt.AbstractDataBase,
            name: str,
            cfg: dict) -> bt.AbstractDataBase:
        '''
            Creates and returns the data feed from config

            Args:
            -----
            - data (bt.AbstractDataBase)
            - name (str)
            - cfg (dict)

            Returns:
            --------
            bt.AbstractDataBase
            '''
        if len(cfg) < 3:
            raise Exception("Feed configuration error")
        dargs = dict(
            timeframe=bt.TimeFrame.TFrame(cfg[0]),
            compression=cfg[1] or None,
            name=name)
        mode = cfg[2]
        if len(cfg) > 3:
            dargs = {**dargs, **cfg[3]}
        self.log('Creating Feed {} {}: [{}, {}]\n{}'.format(
                name, mode, cfg[0], cfg[1],
                tabulate(dargs.items(), tablefmt='plain')),
            logging.DEBUG)
        if mode == 'replay':
            d = self._instance.cerebro.replaydata(data, **dargs)
        elif mode == 'resample':
            d = self._instance.cerebro.resampledata(data, **dargs)
        elif mode == 'add':
            d = self._instance.cerebro.adddata(data, name=name)
        else:
            raise Exception(f'Unsupported feed mode {mode}')
        self.log(
            f'Feed {name} {mode}: [{cfg[0]}, {cfg[1]}] created',
            logging.INFO)
        return d
