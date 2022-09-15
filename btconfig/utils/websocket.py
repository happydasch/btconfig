import json
import time
from threading import Thread, Lock

from websocket import WebSocketApp


class WebsocketManager:

    # @src: https://github.com/ftexchange/ftx/blob/master/websocket/websocket_manager.py # noqa: *

    _CONNECT_TIMEOUT_S = 10

    def __init__(self, ping_interval=0, ping_timeout=0, debug=False):
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout
        self.thread_check = Thread(target=self._check_thread)
        self.connect_lock = Lock()
        self.ws = None
        self.wst = None
        self.running = True
        self.debug = debug

    def _check_thread(self):
        while self.running:
            if self.wst and not self.wst.is_alive():
                self.reconnect()
            time.sleep(0.5)

    def _get_url(self):
        raise NotImplementedError()

    def _on_message(self, ws, message):
        raise NotImplementedError()

    def _on_close(self, ws, close_status, close_reason):
        raise Exception(f'{close_status}: {close_reason}')

    def _on_error(self, ws, error):
        raise Exception(error)

    def _connect(self):
        assert not self.ws, "ws should be closed before attempting to connect"
        if not self.running:
            return
        self.ws = WebSocketApp(
            self._get_url(),
            on_message=self._on_message,
            on_close=self._on_close,
            on_error=self._on_error)

        self.wst = Thread(
            target=self._run_websocket,
            args=(self.ws,),
            kwargs={
                'ping_interval': self._ping_interval,
                'ping_timeout': self._ping_timeout},
            daemon=True)
        self.wst.start()

        if not self.thread_check.is_alive():
            self.thread_check.start()

        # Wait for socket to connect
        ts = time.time()
        while self.ws and (not self.ws.sock or not self.ws.sock.connected):
            if time.time() - ts > self._CONNECT_TIMEOUT_S:
                self.ws = None
                return
            time.sleep(0.1)

    def _run_websocket(self, ws, ping_interval=0, ping_timeout=0):
        try:
            ws.run_forever(
                skip_utf8_validation=True,
                ping_interval=ping_interval,
                ping_timeout=ping_timeout)
        except Exception as e:
            # the catched exception ends current thread
            if self.debug:
                print(e)

    def _reconnect(self, ws):
        assert ws is not None, ('_reconnect should only be called'
                                ' with an existing ws')
        if ws is self.ws:
            self.ws = None
            ws.close()
            self.connect()

    def connect(self):
        if self.ws:
            return
        with self.connect_lock:
            while not self.ws:
                self._connect()
                if self.ws:
                    return

    def reconnect(self):
        if self.ws is not None:
            self._reconnect(self.ws)

    def send(self, message):
        self.connect()
        if not self.ws:
            return
        self.ws.send(message)

    def send_json(self, message):
        self.send(json.dumps(message))
