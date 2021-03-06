from __future__ import division, absolute_import, print_function

import itertools
import pandas as pd
import ib.opt as ibopt
import backtrader as bt

from abc import abstractmethod
from collections import defaultdict
from datetime import datetime, timedelta
from time import sleep, time
from ib.ext.EClientSocket import EClientSocket
from backtrader.feeds import IBData
from backtrader.stores import IBStore


class IBDownloadEngine:
    def __init__(self, app, host, port, clientId):
        self.app = app
        self.host = host
        self.port = port
        self.clientId = clientId
        self.conn = None

    @abstractmethod
    def connect(self):
        ''' Connect method '''

    @abstractmethod
    def disconnect(self):
        ''' Disconnect method '''

    def isConnected(self):
        ''' Returns if connection is connected '''
        try:
            return self.conn.isConnected()
        except AttributeError:
            return False


class IBDownloadEngine_Eclient(IBDownloadEngine):

    def __init__(self, app, host, port, clientId):
        super(IBDownloadEngine_Eclient, self).__init__(
            app, host, port, clientId)
        self.conn = EClientSocket(self)

    def error(self, id=None, errorCode=None, errorMsg=None):
        pass

    def error_0(self, strval):
        pass

    def error_1(self, id, errorCode, errorMsg):
        pass

    def connectionClosed(self):
        pass

    def managedAccounts(self, accountsList):
        pass

    def nextValidId(self, orderId):
        pass

    def connect(self):
        self.conn.eConnect(self.host, self.port, self.clientId)

    def disconnect(self):
        self.conn.eDisconnect()

    def historicalData(self, reqId, date, open, high, low, close,
                       volume, count, WAP, hasGaps):
        self.app._processHistoricalData(
            reqId=reqId, date=date,
            open=open, high=high,
            low=low, close=close,
            volume=volume, count=count,
            WAP=WAP, hasGaps=hasGaps)


class IBDownloadEngine_Conn(IBDownloadEngine):

    def __init__(self, app, host, port, clientId):
        super(IBDownloadEngine_Conn, self).__init__(app, host, port, clientId)
        self.conn = ibopt.ibConnection(
            host=self.host, port=self.port, clientId=self.clientId)
        self.conn.register(self.historicalData, 'HistoricalData')

    def connect(self):
        self.conn.connect()

    def disconnect(self):
        self.conn.disconnect()

    def historicalData(self, msg):
        self.app._processHistoricalData(
            reqId=msg.reqId, date=msg.date,
            open=msg.open, high=msg.high,
            low=msg.low, close=msg.close,
            volume=msg.volume, count=msg.count,
            WAP=msg.WAP, hasGaps=msg.hasGaps)


class IBDataloaderApp:

    # Set a base for the data requests (historical/realtime) to distinguish the
    # id in the error notifications from orders, where the basis (usually
    # starting at 1) is set by TWS
    REQIDBASE = 0x01000000

    def __init__(self, host='127.0.0.1', port=7496, clientId=35,
                 e=IBDownloadEngine_Eclient, pause=None, debug=False):
        '''
        Initializes download app
        '''
        self.engine = e(self, host, port, clientId)
        self.data = IBData()
        self.store = IBStore()
        self.pause = pause
        self.debug = debug
        self._tickerId = itertools.count(self.REQIDBASE)  # unique tickerIds
        self._prepare()

    def _prepare(self):
        '''
        Prepares all download app
        '''
        self._requests = dict()
        self._columns = defaultdict(list)
        self._df = None

    def _getContract(self, instrument):
        '''
        Returns a contract object for a instrument
        '''
        c = self.data.parsecontract(instrument)
        return c

    def _appendRequest(self, contract, enddate, duration, barsize,
                       what, useRTH):
        '''
        Appends a request which will be processed in _processRequests
        '''
        tickerid = next(self._tickerId)
        endtime = enddate.strftime('%Y%m%d %H:%M:%S')
        self._requests[tickerid] = dict(contract=contract, endtime=endtime,
                                        duration=duration, barsize=barsize,
                                        what=what, useRTH=useRTH)

    def _processRequests(self):
        '''
        Processes all pending requests
        '''
        self.engine.connect()
        num_requests = len(self._requests)
        starttime = time()
        prevtime = starttime
        i = 1
        for r in list(self._requests.keys()):
            request = self._requests[r]
            self.engine.conn.reqHistoricalData(
                tickerId=r,
                contract=request['contract'],
                endDateTime=str(request['endtime']),
                durationStr=str(request['duration']),
                barSizeSetting=str(request['barsize']),
                whatToShow=str(request['what']),
                useRTH=int(request['useRTH']),
                formatDate=1)
            while r in self._requests and self.engine.isConnected():
                sleep(.5)
            if self.debug:
                currtime = time()
                prevdiff = timedelta(seconds=int(currtime-prevtime))
                totaldiff = timedelta(seconds=int(currtime-starttime))
                print(f'Processing {i} / {num_requests} Requests.'
                      + f' Time lapsed {prevdiff}.'
                      + f' Total time lapsed {totaldiff}.')
                prevtime = currtime
            if self.pause:
                sleep(self.pause)
            i += 1
            if not self.engine.isConnected():
                break

        if self.engine.isConnected():
            self.engine.disconnect()

        return self.get_df()

    def _processHistoricalData(self, reqId, date, open, high, low, close,
                               volume, count, WAP, hasGaps):
        '''
        Response for historical data request
        '''
        if date in self._columns['datetime']:
            # ensure there are no double entries
            return
        if not date.startswith('finished-'):
            self._columns['datetime'].append(date)
            self._columns['open'].append(open)
            self._columns['high'].append(high)
            self._columns['low'].append(low)
            self._columns['close'].append(close)
            self._columns['volume'].append(volume)
        else:
            self._df = pd.DataFrame.from_dict(self._columns, orient='columns')
            del(self._requests[reqId])

    def get_df(self):
        '''
        Returns the latest DataFrame
        '''
        res = None
        if self._df is None:
            return None
        res = self._df.copy()
        res['datetime'] = pd.to_datetime(res['datetime'])
        return res

    def request(self, instrument, timeframe, compression,
                fromdate, todate, what, useRTH):
        '''
        Requests historical data and returns a DataFrame
        '''
        if self.engine.isConnected():
            return
        if timeframe < bt.TimeFrame.Seconds:
            raise Exception('Ticks are not supported')

        self._prepare()
        start = None
        end = None
        contract = self._getContract(instrument)
        durations = self.store.getdurations(timeframe, compression)
        if not durations:
            raise Exception('No duration for historical data request for '
                            'timeframe/compression')
        barsize = self.store.tfcomp_to_size(timeframe, compression)
        if barsize is None:
            raise Exception('No supported barsize for historical data '
                            'request for timeframe/compresison')

        if todate is None:
            end = datetime.utcnow()
        else:
            end = todate

        if fromdate is None:
            # no start date so request maximum amount of data in a
            # single request
            duration = durations[-1]
            self._appendRequest(contract, end, duration, barsize,
                                what, useRTH)
        else:
            start = fromdate
            starttemp = start
            # collect all required requests
            while True:
                # get the best possible duration to reduce number of requests
                duration = None
                for dur in durations:
                    intdate = self.store.dt_plus_duration(starttemp, dur)
                    if intdate >= end:
                        intdate = end
                        duration = dur  # begin -> end fits in single request
                        break

                if duration is None:
                    # request does not contain all required data yet
                    duration = durations[-1]
                    starttemp = intdate
                    self._appendRequest(contract, starttemp, duration, barsize,
                                        what, useRTH)
                else:
                    # request contains all required data
                    self._appendRequest(contract, end, duration, barsize,
                                        what, useRTH)
                    break

            # process all requests
            return self._processRequests()
