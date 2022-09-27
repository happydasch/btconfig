
from __future__ import division, absolute_import, print_function
import os
import time
import hmac
import json
import logging

import pandas as pd
import backtrader as bt

from threading import Thread
from queue import PriorityQueue, Queue, Empty
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import DefaultDict, List, Dict, Callable

from btconfig import BTConfigDataloader
from btconfig.helper import get_data_dates, get_starttime, parse_dt

from btconfig.utils.api.ftx import create_data_df
from btconfig.utils.dataloader import FTXDataloaderApp
from btconfig.utils.websocket import WebsocketManager

# src: https://github.com/ccxt/ccxt/blob/master/python/ccxt/ftx.py
# hard limit of 7 requests per 200ms
# => 35 requests per 1000ms
# => 1000ms / 35 = 28.5714 ms between requests
# => 0.0285714 s


class FTXWebsocketClient(WebsocketManager):

    _ENDPOINT = 'wss://ftx.com/ws/'

    def __init__(self, api_key, api_secret, ping_interval=0, ping_timeout=0,
                 debug=False) -> None:
        super().__init__(
            ping_interval=ping_interval, ping_timeout=ping_timeout,
            debug=debug)
        self.api_key = api_key
        self.api_secret = api_secret
        self._reset_data()

    def _reset_data(self) -> None:
        self._subscriptions: List[Dict] = []
        self._tickers_cb: DefaultDict[str, Dict] = defaultdict(dict)
        self._trades_cb: DefaultDict[str, Dict] = defaultdict(dict)
        self._orderbook_cb: DefaultDict[str, Dict] = defaultdict(dict)
        self._logged_in = False

    def _get_url(self) -> str:
        return self._ENDPOINT

    def _login(self) -> None:
        ts = int(time.time() * 1000)
        self.send_json({'op': 'login', 'args': {
            'key': self.api_key,
            'sign': hmac.new(
                self.api_secret.encode(),
                f'{ts}websocket_login'.encode(),
                'sha256').hexdigest(),
            'time': ts,
        }})
        self._logged_in = True

    def _reconnect(self, ws):
        super()._reconnect(ws)
        for subscription in self._subscriptions:
            self._subscribe(subscription)

    def _on_message(self, ws, raw_message: str):
        message = json.loads(raw_message)
        message_type = message['type']
        if message_type in {'subscribed', 'unsubscribed'}:
            return
        elif message_type == 'info':
            if message['code'] == 20001:
                return self.reconnect()
        elif message_type == 'error':
            raise Exception(message)
        channel = message['channel']
        if channel == 'ticker':
            self._handle_ticker_message(message)
        elif channel == 'trades':
            self._handle_trades_message(message)
        elif channel == 'orderbook':
            self._handle_orderbook_message(message)

    def _subscribe(self, subscription: Dict) -> None:
        self.send_json({'op': 'subscribe', **subscription})
        if subscription not in self._subscriptions:
            self._subscriptions.append(subscription)

    def _unsubscribe(self, subscription: Dict) -> None:
        self.send_json({'op': 'unsubscribe', **subscription})
        while subscription in self._subscriptions:
            self._subscriptions.remove(subscription)

    def subscribe_ticker(self, market: str, cb: Callable) -> bool:
        subscription = {'channel': 'ticker', 'market': market}
        if subscription not in self._subscriptions:
            self._subscribe(subscription)
        cb_id = id(cb)
        if cb_id in self._tickers_cb[market]:
            return False
        self._tickers_cb[market][cb_id] = cb
        return True

    def unsubscribe_ticker(self, market: str, cb: Callable) -> bool:
        cb_id = id(cb)
        if cb_id not in self._tickers_cb[market]:
            return False
        del(self._tickers_cb[market][cb_id])
        if not len(self._tickers_cb[market]):
            subscription = {'channel': 'ticker', 'market': market}
            if subscription in self._subscriptions:
                self._unsubscribe(subscription)
        return True

    def subscribe_trades(self, market: str, cb: Callable) -> bool:
        subscription = {'channel': 'trades', 'market': market}
        if subscription not in self._subscriptions:
            self._subscribe(subscription)
        cb_id = id(cb)
        if cb_id in self._trades_cb[market]:
            return False
        self._trades_cb[market][cb_id] = cb
        return True

    def unsubscribe_trades(self, market: str, cb: Callable) -> bool:
        cb_id = id(cb)
        if cb_id not in self._trades_cb[market]:
            return False
        del(self._trades_cb[market][cb_id])
        if not len(self._trades_cb[market]):
            subscription = {'channel': 'trades', 'market': market}
            if subscription in self._subscriptions:
                self._unsubscribe(subscription)
        return True

    def subscribe_orderbook(self, market: str, cb: Callable) -> bool:
        subscription = {'channel': 'orderbook', 'market': market}
        if subscription not in self._subscriptions:
            self._subscribe(subscription)
        cb_id = id(cb)
        if cb_id in self._orderbook_cb[market]:
            return False
        self._orderbook_cb[market][cb_id] = cb
        return True

    def unsubscribe_orderbook(self, market: str, cb: Callable) -> bool:
        cb_id = id(cb)
        if cb_id not in self._orderbook_cb[market]:
            return False
        del(self._orderbook_cb[market][cb_id])
        if not len(self._orderbook_cb[market]):
            subscription = {'channel': 'orderbook', 'market': market}
            if subscription in self._subscriptions:
                self._unsubscribe(subscription)
        return True

    def _handle_ticker_message(self, message: Dict) -> None:
        for cb in list(self._tickers_cb[message['market']].values()):
            cb(message['data'])

    def _handle_trades_message(self, message: Dict) -> None:
        for cb in list(self._trades_cb[message['market']].values()):
            cb(message['data'])

    def _handle_orderbook_message(self, message: Dict) -> None:
        for cb in list(self._orderbook_cb[message['market']].values()):
            cb(message['data'])


#
# Dataloader
#


class FTXDataloader(BTConfigDataloader):

    PREFIX = 'FTX'

    def _prepare(self):
        self._cls = FTXData
        pause = self._cfg.get('pause', 0.0285714)
        debug = self._cfg.get('debug', False)
        api_key = self._cfg.get('api_key', '')
        api_secret = self._cfg.get('api_secret', '')
        self.loader = FTXDataloaderApp(
            api_key=api_key, api_secret=api_secret,
            pause=pause, debug=debug)

    def _loadData(self):
        dataname = self._cfg['dataname']
        timeframe = bt.TimeFrame.TFrame(self._cfg['granularity'][0])
        compression = self._cfg['granularity'][1]
        fromdate, todate = get_data_dates(
            self._cfg.get('backfill_days'),
            self._cfg.get('fromdate'),
            self._cfg.get('todate'))
        if self._filedate:
            fromdate = self._filedate
        if not os.path.isfile(self._filename) or not todate:
            data = self.loader.getMarketCandles(
                dataname, timeframe, compression, fromdate, todate)
            return data


class FTXFundingRatesDataloader(BTConfigDataloader):

    PREFIX = 'FTX_FR'

    def _prepare(self):
        self._cls = FTXFundingRates
        api_key = self._cfg.get('api_key', '')
        api_secret = self._cfg.get('api_secret', '')
        pause = self._cfg.get('pause', 0.0285714)
        debug = self._cfg.get('debug', False)
        self.loader = FTXDataloaderApp(
            api_key=api_key, api_secret=api_secret,
            pause=pause, debug=debug)

    def _loadData(self):
        dataname = self._cfg['dataname']
        fromdate, todate = get_data_dates(
            self._cfg.get('backfill_days'),
            self._cfg.get('fromdate'),
            self._cfg.get('todate'))
        if self._filedate:
            fromdate = self._filedate
        if not os.path.isfile(self._filename) or not todate:
            data = self.loader.getFundingRates(dataname, fromdate, todate)
            return data


class FTXDataloaderLive(FTXDataloader):

    def _prepare(self):
        super(FTXDataloaderLive, self)._prepare()
        self._cls = FTXDataLive

    def _createFeed(self):
        data = super(FTXDataloaderLive, self)._createFeed()
        if hasattr(self._instance, 'ftx_loader'):
            data.ftx_loader = self._instance.ftx_loader
        else:
            data.ftx_loader = self.loader
        if not hasattr(FTXWebsocketClient, 'instance'):
            debug = self._cfg.get('debug', False)
            FTXWebsocketClient.instance = FTXWebsocketClient(
                self.loader.api_key, self.loader.api_secret,
                ping_interval=10, ping_timeout=5, debug=debug)
        data.ws_client = FTXWebsocketClient.instance
        return data


class FTXFundingRatesDataloaderLive(FTXFundingRatesDataloader):

    def _prepare(self):
        super(FTXFundingRatesDataloaderLive, self)._prepare()
        self._cls = FTXFundingRatesLive

    def _createFeed(self):
        data = super(FTXFundingRatesDataloaderLive, self)._createFeed()
        if hasattr(self._instance, 'ftx_loader'):
            data.ftx_loader = self._instance.ftx_loader
        else:
            data.ftx_loader = self.loader
        return data


#
# Feeds
#


class FTXData(bt.feeds.GenericCSVData):

    params = dict(
        adjstarttime=False,
        roundvalues=False,
        roundprecision=8,
        dtformat=parse_dt,
        datetime=0, open=1, high=2, low=3, close=4, volume=5,
        openinterest=-1
    )

    def _loadline(self, linetokens):
        res = super(FTXData, self)._loadline(linetokens)
        # if values should be rounded, all lines will get rounded
        if self.p.roundvalues:
            for linefield in self.getlinealiases():
                csvidx = getattr(self.params, linefield)
                if linefield == 'datetime' or csvidx is None or csvidx < 0:
                    continue
                line = getattr(self.lines, linefield)
                if line[0] == line[0]:
                    line[0] = round(line[0], self.p.roundprecision)
        # ensure that utc time is being used
        dt = self.datetime.datetime(0, tz=timezone.utc)
        if self.p.adjstarttime:
            # move to bar endtime
            # subtract 0.1 miliseconds to move from edge of candle
            # (ensures no rounding issues, 10 microseconds is minimum)
            dt = get_starttime(
                self._timeframe, self._compression, dt,
                self.p.sessionstart, 1)
            dt -= timedelta(microseconds=100)
        self.datetime[0] = bt.date2num(dt)
        return res


class FTXDataLive(FTXData):

    # Extends ftx data with live data
    #
    # self.loader is an instance of
    # btconfig.utils.dataloader.FTXDataloaderApp
    # -> does not use cache and does not create any csv files
    #
    # self.ftx_loader is an instance of
    # utils.data.CryptoFTX
    # -> creates csv files and caches data
    #

    _ST_START, _ST_PRELIVE, _ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(5)

    params = {
        'instrument': None,
        'emit_interval': 0.0,
        'adjust_interval': False,
        'max_interval': 15.0,
        'fill_gap': False,
        'enable_ticker': True,
        'load_multiple_candles': False
    }

    def __init__(self, debug=False, *args, **kwargs):
        super(FTXDataLive, self).__init__(*args, **kwargs)
        self._laststatus = None
        self._state = self._ST_START
        self._queue = PriorityQueue()
        self._trades = Queue()
        self._ticks = Queue()
        self._debug = debug
        self._last_emit = None
        self._last_qsize = 0
        self._current_interval = 0.0
        self.reset_emit_interval()

    def _prefill_ws(self):
        candles = []
        if self.datetime[-1] == self.datetime[-1]:
            start_dt = self.datetime.datetime(-1)
            lowest = list(self.ftx_loader.client.RESOLUTIONS.keys())[0]
            lowest = self.ftx_loader.client.RESOLUTIONS[lowest]
            candles = self.ftx_loader.client.getMarketCandles(
                self.p.instrument,
                start_time=start_dt.timestamp(),
                resolution=lowest)
        if len(candles):
            data = create_data_df(candles)
            for row in data.iterrows():
                candle = dict(
                    datetime=row[1].datetime.to_pydatetime(),
                    open=row[1].open,
                    high=row[1].high,
                    low=row[1].low,
                    close=row[1].close,
                    volume=row[1].volume)
                if self.p.adjstarttime:
                    # move to bar endtime
                    # subtract 0.1 miliseconds to move from edge of candle
                    # (ensures no rounding issues, 10 microseconds is minimum)
                    candle['datetime'] = get_starttime(
                        self._timeframe, self._compression, candle['datetime'],
                        self.p.sessionstart, 1)
                    candle['datetime'] -= timedelta(microseconds=100)
                self._queue.put((bt.date2num(candle['datetime']), candle))
        self._state = self._ST_LIVE

    def _subscribe_ws(self):
        self.ws_client.subscribe_trades(
            self.p.instrument, self._cb_ws_trades)
        if self._debug:
            dtnow = datetime.utcnow()
            tradeslen = len(self.ws_client._trades_cb)
            logging.debug(
                f'Market Candles {dtnow}: Subscribe to'
                f' {self.p.instrument} ({tradeslen} subscriptions)')
        if self.p.enable_ticker:
            self.enable_ticker()

    def _unsubscribe_ws(self):
        self.ws_client.unsubscribe_ticker(
            self.p.instrument, self._cb_ws_ticker)
        self.ws_client.unsubscribe_trades(
            self.p.instrument, self._cb_ws_trades)
        if self._debug:
            dtnow = datetime.utcnow()
            tradeslen = len(self.ws_client._trades_cb)
            logging.debug(
                f'Market Candles {dtnow}: Unsubscribe from'
                f' {self.p.instrument} ({tradeslen} subscriptions)')

    def _add_tick_to_queue(self, tick):
        '''
        Adds tick to queue
        '''
        dt = tick['datetime']
        emit = False
        if self._last_emit is None:
            # never emitted anything, set start time and wait for more ticks
            self._last_emit = dt
        else:
            # already emitted, check if not over boundry of lowest candle or
            # not passed emit interval
            c_idx = self._last_emit.timestamp() // self.p.max_interval
            n_idx = dt.timestamp() // self.p.max_interval
            emit_diff = dt - self._last_emit
            emit_diff = emit_diff.total_seconds()
            if emit_diff > self._current_interval or c_idx != n_idx:
                emit = True
        # emit candle before adding current tick since this tick triggered
        # the emitting so it is already a tick for the next candle
        if emit:
            self._emit_candle()
            self._last_emit = dt
        self._ticks.put(tick)

    def _cb_ws_trades(self, data):
        '''
        Websocket callback for trades
        '''
        dt = None
        for trade in data:
            dt = datetime.fromisoformat(
                trade['time']).replace(tzinfo=None)
            t = dict(datetime=dt,
                     open=trade['price'],
                     high=trade['price'],
                     low=trade['price'],
                     close=trade['price'],
                     volume=trade['size'])
            self._add_tick_to_queue(t)

    def _cb_ws_ticker(self, data):
        '''
        Websocket callback for ticker
        '''
        dt = datetime.utcfromtimestamp(data['time'])
        tick = dict(
                datetime=dt,  open=data['last'], high=data['last'],
                low=data['last'], close=data['last'], volume=0)
        self._add_tick_to_queue(tick)

    def _emit_candle(self):
        '''
        Emit collected ticks as a candle
        '''
        if not self._ticks.qsize():
            return
        dtnow = datetime.utcnow()
        candle = self._ticks.get()
        first_dt = candle['datetime']
        ticks = 1
        while True:
            if not self._ticks.qsize():
                break
            tick = self._ticks.get()
            candle['datetime'] = tick['datetime']
            candle['high'] = max(candle['high'], tick['high'])
            candle['low'] = min(candle['low'], tick['low'])
            candle['close'] = tick['close']
            ticks += 1
        last_dt = candle['datetime']
        while True:
            if not self._trades.qsize():
                break
            trade = self._trades.get()
            candle['volume'] += trade['size']
        if self._debug:
            logging.debug(
                f'Market Candles {dtnow}: Emitting candle for'
                f' {self.p.instrument} at {candle["datetime"]}'
                f' interval: {self._current_interval}'
                f' ticks used: {ticks}'
                f' first dt: {first_dt}'
                f' last dt: {last_dt}'
                f' duration: {last_dt-first_dt}')
        self._queue.put((bt.date2num(candle['datetime']), candle))

    def _load_candle(self, candle):
        datetime = candle['datetime']
        o_price = candle['open']
        h_price = candle['high']
        l_price = candle['low']
        c_price = candle['close']
        volume = candle['volume']

        dt = bt.date2num(datetime)
        if dt <= self.l.datetime[-1]:
            return False  # time already seen

        self.l.datetime[0] = dt
        self.l.open[0] = o_price
        self.l.high[0] = h_price
        self.l.low[0] = l_price
        self.l.close[0] = c_price
        self.l.volume[0] = volume
        self.l.openinterest[0] = 0.0
        return True

    def _load(self):
        if self._state == self._ST_OVER:
            return False
        if self._state == self._ST_START:
            self._state = self._ST_HISTORBACK
            self.put_notification(self.DELAYED)
        if self._state == self._ST_HISTORBACK:
            res = super(FTXDataLive, self)._load()
            if self.datetime[0] > 0:
                self._last_date = bt.num2date(
                    self.datetime[0], tz=timezone.utc)
            if res:
                return res
            if self.p.fill_gap:
                self._state = self._ST_PRELIVE
                self._subscribe_ws()
                Thread(target=self._prefill_ws).start()
            else:
                self._state = self._ST_LIVE
        if self._state == self._ST_LIVE:
            while True:
                try:
                    dt, candle = self._queue.get(timeout=self.p.qcheck)
                    if self.p.load_multiple_candles:
                        candle_idx = (
                            candle['datetime'].timestamp()
                            // self.p.max_interval)
                        for i in range(self._queue.qsize()):
                            tmpdt, tmp = self._queue.get()
                            tmp_idx = (
                                tmp['datetime'].timestamp()
                                // self.p.max_interval)
                            if tmp_idx != candle_idx:
                                self._queue.put((tmpdt, tmp))
                                break
                            candle['datetime'] = tmp['datetime']
                            candle['close'] = tmp['close']
                            candle['high'] = max(candle['high'], tmp['high'])
                            candle['low'] = min(candle['low'], tmp['low'])
                            candle['volume'] += tmp['volume']
                except Empty:
                    return None
                res = self._load_candle(candle)
                if res:
                    qsize = self._queue.qsize()
                    if qsize == 0:
                        # set to live after first time queue was emptied
                        if self._laststatus != self.LIVE:
                            self.put_notification(self.LIVE)
                    elif qsize > 2:
                        if self._laststatus != self.DELAYED:
                            self.put_notification(self.DELAYED)
                    # if adjust interval check if current size - 2 is
                    # bigger then last size then speed down, use 2 to
                    # prevent too quick speed downs
                    if (self.p.adjust_interval and self._last_qsize
                            and qsize <= 2):
                        if self._current_interval > 10:
                            diff = 10
                        elif self._current_interval > 1:
                            diff = 1
                        elif self._current_interval > 0.1:
                            diff = 0.1
                        else:
                            diff = 0.01
                        if qsize > self._last_qsize:
                            self._current_interval = min(
                                self.p.max_interval,
                                self._current_interval + diff)
                        elif qsize <= self._last_qsize:
                            self._current_interval = max(
                                self.p.emit_interval,
                                self._current_interval - diff)
                    elif self.p.adjust_interval and self._last_qsize:
                        if qsize > self._last_qsize:
                            self._current_interval = min(
                                self.p.max_interval,
                                self._current_interval * 2)
                    if self._debug:
                        if qsize > self._last_qsize:
                            dtnow = datetime.utcnow()
                            logging.debug(
                                f'Market Candles {dtnow}:'
                                f'{self.p.instrument} - queue is growing,'
                                f' was: {self._last_qsize} - is: {qsize}'
                                f' emit interval: {self._current_interval}')
                        elif qsize < self._last_qsize:
                            dtnow = datetime.utcnow()
                            logging.debug(
                                f'Market Candles {dtnow}:'
                                f'{self.p.instrument} - queue is shrinking,'
                                f' was: {self._last_qsize} - is: {qsize}'
                                f' emit interval: {self._current_interval}')
                        else:
                            dtnow = datetime.utcnow()
                            logging.debug(
                                f'Market Candles {dtnow}:'
                                f'{self.p.instrument} - queue not changed,'
                                f' was: {self._last_qsize} - is: {qsize}'
                                f' emit interval: {self._current_interval}')
                    self._last_qsize = qsize
                    return True

    def reset_emit_interval(self):
        self._current_interval = self.p.emit_interval

    def update_emit_interval(self, interval):
        self._current_interval = interval

    def enable_ticker(self):
        self.ws_client.subscribe_ticker(
            self.p.instrument, self._cb_ws_ticker)

    def disable_ticker(self):
        self.ws_client.unsubscribe_ticker(
            self.p.instrument, self._cb_ws_ticker)

    def start(self):
        super().start()
        if not self.p.fill_gap:
            self._subscribe_ws()

    def stop(self):
        super().stop()
        self._unsubscribe_ws()

    def haslivedata(self):
        return (self._queue.qsize() > 0)

    def islive(self):
        return True


class FTXFundingRates(bt.feeds.GenericCSVData):

    params = dict(
        adjstarttime=False,
        roundvalues=False,
        roundprecision=8,
        dtformat=parse_dt,
        datetime=0, open=1, high=1, low=1, close=1,
        volume=-1, openinterest=-1
    )

    def _loadline(self, linetokens):
        res = super(FTXFundingRates, self)._loadline(linetokens)
        # if values should be rounded, all lines will get rounded
        if self.p.roundvalues:
            for linefield in self.getlinealiases():
                csvidx = getattr(self.params, linefield)
                if linefield == 'datetime' or csvidx is None or csvidx < 0:
                    continue
                line = getattr(self.lines, linefield)
                if line[0] == line[0]:
                    line[0] = round(line[0], self.p.roundprecision)
        # ensure that utc time is being used
        dt = self.datetime.datetime(0, tz=timezone.utc)
        if self.p.adjstarttime:
            # subtract 0.1 miliseconds to move to end of candle
            # (ensures no rounding issues, 10 microseconds is minimum)
            dt = get_starttime(
                self._timeframe, self._compression, dt,
                self.p.sessionstart, 0)
            dt -= timedelta(microseconds=100)
        self.datetime[0] = bt.date2num(dt)
        return res


class FTXFundingRatesLive(FTXFundingRates):

    # Extends ftx funding rates with live data

    _ST_START, _ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(4)
    params = {
        'instrument': None,
        'check_interval': 1.0,
        'poll_interval': 30.0
    }
    _thread = None
    newest = None
    running = True

    def __init__(self, debug=False, *args, **kwargs):
        super(FTXFundingRatesLive, self).__init__(*args, **kwargs)
        self._laststatus = None
        self._state = self._ST_START
        self._queue = Queue()
        self._debug = debug
        self._last_date = datetime.utcnow()
        self._last_success = None
        self._last_check = None
        self._live = False

    @staticmethod
    def _start_thread(ftx_loader, interval, debug):
        if FTXFundingRatesLive._thread is not None:
            return
        thread = Thread(
            target=FTXFundingRatesLive._t_poll,
            args=[ftx_loader, interval, debug],
            daemon=True)
        thread.start()
        FTXFundingRatesLive._thread = thread

    @staticmethod
    def _t_poll(ftx_loader, interval, debug):
        dtcurr = None
        duration = None
        while FTXFundingRatesLive.running:
            dtnow = datetime.utcnow()
            if debug:
                logging.debug(
                    f'Funding Rates {dtnow}: Requesting funding rates'
                    + (f' since {dtcurr}' if dtcurr else ''))
            data = ftx_loader.getAllFundingRates(fromdate=dtcurr)
            if data is not None and len(data):
                if not duration and len(data) > 1:
                    dt_unique = data.datetime.unique()
                    duration = pd.Timedelta(
                        dt_unique[1] - dt_unique[0]).to_pytimedelta()
                if dtcurr:
                    # ensure to also get current time, so the df does not
                    # end up being empty, if there is only current time
                    # available in new data
                    data = data[data.datetime >= dtcurr]
            # replace funding rates with latest fetched
            if len(data) and len(data[data.datetime > dtcurr]):
                if debug:
                    logging.debug(
                        f'Funding Rates {dtnow}: New funding rates recieved')
                FTXFundingRatesLive.newest = data
            # wait before next request
            if debug:
                logging.debug(
                    f'Funding Rates {dtnow}: Waiting for {interval}'
                    ' seconds before next request')
            time.sleep(interval)

    def _check_newest(self):
        if FTXFundingRatesLive.newest is None:
            return
        dtnow = datetime.utcnow()
        if self._last_check:
            dtdiff = dtnow - timedelta(seconds=self.p.check_interval)
            if (dtdiff < self._last_check):
                return
        data = FTXFundingRatesLive.newest
        newest = data[data.future == self.p.instrument]
        newest = newest[newest.datetime > self._last_date]
        for x in newest.index:
            candle = dict(newest.loc[x])
            candle['datetime'] = candle['datetime'].to_pydatetime()
            self._queue.put(candle)
        self._last_check = dtnow

    def _load(self):
        if self._state == self._ST_OVER:
            return False
        if self._state == self._ST_START:
            self._state = self._ST_HISTORBACK
            self.put_notification(self.DELAYED)
        if self._state == self._ST_HISTORBACK:
            result = super(FTXFundingRatesLive, self)._load()
            if self.l.datetime[0] > 0:
                self._last_date = bt.num2date(
                    self.l.datetime[0], tz=timezone.utc)
            if result:
                return result
            self._state = self._ST_LIVE
            FTXFundingRatesLive._start_thread(
                self.ftx_loader, self.p.poll_interval, self._debug)
        if self._state == self._ST_LIVE:
            self._check_newest()
            try:
                candle = self._queue.get(timeout=self.p.qcheck)
                result = self._load_candle(candle)
                if result:
                    self._live = True
                    return result
            except Empty:
                pass
            if self._live and self._laststatus != self.LIVE:
                self.put_notification(self.LIVE)
            return None
        return False

    def _load_candle(self, candle):
        dt = candle['datetime']
        close = candle['close']
        if self.p.adjstarttime:
            # subtract 0.1 miliseconds to move to end of candle
            # (ensures no rounding issues, 10 microseconds is minimum)
            dt = get_starttime(
                self._timeframe, self._compression, dt,
                self.p.sessionstart, 0)
            dt -= timedelta(microseconds=100)
        dtnum = bt.date2num(dt)
        if dtnum <= self.l.datetime[-1]:
            return False  # time already seen
        self.l.datetime[0] = dtnum
        self.l.open[0] = close
        self.l.high[0] = close
        self.l.low[0] = close
        self.l.close[0] = close
        self.l.volume[0] = 0
        self.l.openinterest[0] = 0.0
        self._last_date = dt
        return True

    def stop(self):
        FTXFundingRatesLive.running = False

    def haslivedata(self):
        return (self._queue.qsize() > 0)

    def islive(self):
        return True
