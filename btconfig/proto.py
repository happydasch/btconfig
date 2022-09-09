from __future__ import division, absolute_import, print_function

import logging
import pytz
import backtrader as bt

from btconfig.helper import strfdelta
from btconfig.utils.rounding import (
    get_pips_from_value, get_value_from_pips, get_price_value,
    get_round_to_pip)


class ProtoStrategy(bt.Strategy):
    '''
    Prototype strategy

    * Logging
        set param use_logging=true, logs will be stored in logs/
        logging needs to be set up

    * Datafeed status tracking
        self.datastatus == 0 -> Delayed data
        self.datastatus > 0 -> Live data
    '''

    params = dict(
        # use logging (if false, print will be used)
        use_logging=False,
        # logging
        log_candles=True,
        log_signals=True,
        log_orders=True,
        log_trades=True,
        log_data=True,
        log_store=True
    )

    def __init__(self):
        '''
        Initialization
        '''
        # control vars
        self.datastatus = 1  # data status (live or delayed)
        super(ProtoStrategy, self).__init__()

    def log(self, txt, dt=None, level=logging.INFO):
        '''
        Logging function for strategy
        '''
        if len(self.data):
            dt = dt or self.data.datetime.datetime(0)
            txt = f'{dt.isoformat()}: {txt}'
        if not self.p.use_logging:
            return
        self.cerebro.btconfig.log(txt, level)

    def notify_store(self, msg, *args, **kwargs):
        '''
        Store notification
        '''
        self.log_store(msg, *args, **kwargs)

    def notify_data(self, data, status, *args, **kwargs):
        '''
        Data notification
        '''
        self.log_data(data, status, *args, **kwargs)
        if status == data.LIVE:
            self.datastatus = 1
        elif status == data.DELAYED:
            self.datastatus = 0

    def log_candle(self, *args, **kwargs):
        '''
        Log current candle
        '''
        if not self.p.log_candles:
            return
        data = kwargs.get('data', self.data)
        level = kwargs.get('level', logging.INFO)
        offset = kwargs.get('offset', 0)
        frompre = kwargs.get('frompre', False)
        if not len(data):
            return
        contractdetails = {}
        if hasattr(data, 'contractdetails'):
            contractdetails = data.contractdetails
        pip_location = contractdetails.get('pipLocation', 0)
        precision = contractdetails.get('displayPrecision', 1)
        diff_oc = 0.0
        diff_hl = 0.0
        if len(data) > abs(offset):
            if data.close[offset] > data.open[offset]:
                diff_oc = data.close[offset] - data.close[offset - 1]
            elif data.close[offset] < data.open[offset]:
                diff_oc = -(data.close[offset - 1] - data.close[offset])
            diff_hl = data.high[offset] - data.low[offset]
        diff_oc = self.pips_from_value(
            value=round(diff_oc, precision),
            pip_location=pip_location, pip_precision=1)
        diff_hl = self.pips_from_value(
            value=round(diff_hl, precision),
            pip_location=pip_location, pip_precision=1)

        offset_str = f'{offset}' if offset < 0 else ''

        txt = []
        if frompre:
            txt.append('FILLING')
        else:
            src_data = data if data._owner is None else data._owner
            if not src_data.islive() or src_data._laststatus == data.LIVE:
                txt.append('LIVE')
            else:
                txt.append('DELAYED')

        txt.append(f'{diff_oc:+.1f}({diff_hl:.1f})')
        txt.append('%s %04d%s' % (data._name, len(data), offset_str))
        o_price = self.price_value(data.open[offset], precision)
        h_price = self.price_value(data.high[offset], precision)
        l_price = self.price_value(data.low[offset], precision)
        c_price = self.price_value(data.close[offset], precision)
        txt.append(f'O: {o_price:.{precision}f}')
        txt.append(f'H: {h_price:.{precision}f}')
        txt.append(f'L: {l_price:.{precision}f}')
        txt.append(f'C: {c_price:.{precision}f}')
        for i in args:
            txt.append(i)
        candle = ', '.join(txt)
        self.log(f'[CANDLE] {candle}',
                 dt=data.datetime.datetime(offset),
                 level=level)

    def log_signal(self, *args, level=logging.INFO):
        '''
        Log given signals
        '''
        if not self.p.log_signals:
            return
        signal = ', '.join([str(x) for x in args])
        self.log(f'[SIGNAL] {signal}')

    def log_order(self, order, level=logging.INFO):
        '''
        Log given order
        '''
        if not self.p.log_orders:
            return
        txt = []
        if isinstance(order, (bt.OrderBase)):
            txt.append(f'Data {order.data._name}')
            txt.append(f'Ref {order.ref}')
            txt.append(f'Status {order.getstatusname()}')
            txt.append(f'Type {order.ordtypename()}')
            txt.append(f'ExecType {order.getordername()}')
            txt.append(f'Size {order.size}')
            txt.append(f'Alive {order.alive()}')
            txt.append(f'Price {order.executed.price}')
            txt.append(f'Position {self.getposition(order.data).size}')
        else:
            txt.append(str(order))
        info = ' / '.join(txt)
        self.log(f'[ORDER] {info}')

    def log_trade(self, trade, level=logging.INFO):
        '''
        Log given trade
        '''
        if not self.p.log_trades:
            return
        txt = []
        if isinstance(trade, bt.Trade):
            txt.append(f'Data {trade.data._name}')
            txt.append(f'Status {trade.status_names[trade.status]}')
            txt.append(f'Price {trade.price:f}')
            if trade.size > 0:
                txt.append(f'Size {trade.size:f}')
            if trade.dtopen > 0:
                txt.append(f'Opened at {trade.open_datetime()}')
            if trade.isclosed:
                pnl = trade.pnl
                pnlcomm = trade.pnlcomm
                comm = trade.commission
                if trade.dtclose > 0:
                    duration = trade.close_datetime() - trade.open_datetime()
                    txt.append(f'Closed at {trade.close_datetime()}')
                    if duration.days > 0:
                        txt.append(
                            strfdelta(duration, "Duration %D days %H:%M:%S"))
                    else:
                        txt.append(
                            strfdelta(duration, "Duration %H:%M:%S"))
                txt.append('PnL {:.2f}'.format(pnl))
                txt.append('PnLComm {:.2f}'.format(pnlcomm))
                txt.append('Comm {:.2f}'.format(comm))
                txt.append(f'Length bars {trade.barlen}')
        else:
            txt.append(str(trade))
        info = ' / '.join(txt)
        self.log(f'[TRADE] {info}')

    def log_data(self, data, status, *args, **kwargs):
        '''
        Log data notification
        '''
        if not self.p.log_data:
            return
        txt = [data._name,
               data._getstatusname(status),
               *args]
        info = ' / '.join(txt)
        self.log(f'[DATA] {info}')

    def log_store(self, msg, *args, **kwargs):
        '''
        Log store notification
        '''
        txt = [msg,
               *args]
        info = ' / '.join(txt)
        self.log(f'[STORE] {info}')


class ForexProtoStrategy(ProtoStrategy):
    '''
    Prototype strategy for forex

    This class provides a unifed access to forex specific settings.

    * Convert pips to value
        value = self.value_from_pips(pips)

    * Convert value to pips
        pips = self.pips_from_value(value)

    Parameter:
    Set the strategy paramters according to the instrument in use.

    ex. EUR/USD ->  pip_location=4,
                    display_precision=5,
                    min_trail_stop_dist=0.0005
    '''

    # constants for markets
    (MARKET_SYDNEY, MARKET_TOKYO, MARKET_LONDON,
     MARKET_NEW_YORK, MARKET_CUSTOM) = range(0, 5)
    MARKETS = ['Sydney', 'Tokyo', 'London', 'New York', 'Custom']
    MARKET_HOURS = [
        # Sydney 5pm to 2am EST(10pm to 7am UTC)
        [(22, 0, 23, 59), (0, 0, 6, 59)],
        # Tokyo 7pm to 4am EST(12am to 9am UTC)
        [(0, 0, 8, 59)],
        # London 3am to 12 noon EST(8pm to 5pm UTC)
        [(8, 0, 16, 59)],
        # New York 8am to 5pm EST(1pm to 10pm UTC)
        [(13, 0, 21, 59)],
    ]

    params = dict(
        # pip location
        pip_location=0,
        # display precision
        display_precision=1,
        # minimum trailing stop distance
        min_trail_stop_dist=0,
        # what markets to use
        markets=[],
        # custom market hours
        # can contain lists with 4 values:
        # start hour, start minute, end hour, end minute
        # for example:
        # [(1, 0, 1, 59)] for 1am-2am
        # [(1, 0, 1, 59), (3, 0, 4, 59)] for 1am-2am and 3am-5am
        # the time needs to be in UTC if no timezone provided
        # to provide a timezone, add a 5 value:
        # [(1, 0, 1, 59, 'Europe/London')] for 1am-2am in Europe/London
        custom_market_hours=[]
    )

    def __init__(self):
        ''' Initialization '''
        # control vars
        self.margin = None
        # check for contractdetails
        cd = dict(
            pipLocation=self.p.pip_location,
            displayPrecision=self.p.display_precision,
            minimumTrailingStopDistance=self.p.min_trail_stop_dist
        )
        # look for possible contractdetails definition
        dcd = None
        if hasattr(self.datas[0], 'contractdetails'):
            dcd = self.datas[0].contractdetails
        # merge dict into contractdetails dict
        if isinstance(dcd, dict):
            cd.update(dcd)
            for d in self.datas:
                if d._name != self.datas[0]._name:
                    d.contractdetails = cd.copy()
        else:
            for d in self.datas:
                d.contractdetails = cd.copy()
        self.contractdetails = cd

        super(ForexProtoStrategy, self).__init__()

    def pip_location(self, value, to_one=True):
        '''
        Returns the pip location for given value

        Ex.
        value=0 - pip location=0
        value=1 - pip location=0
        value=5 - pip location=1 (to_one = True)
        value=5 - pip location=0 (to_one = False)
        value=10 - pip location=1
        value=25 - pip location=2 (to_one = True)
        value=25 - pip location=1 (to_one = False)
        value=0.5 - pip location=0 (to_one = True)
        value=0.5 - pip location=-1 (to_one = False)
        value=0.25 - pip location=0 (to_one = True)
        value=0.25 - pip location=-1 (to_one = False)
        value=0.1 - pip location=-1
        value=0.05 - pip location=-1 (to_one = True)
        value=0.05 - pip location=-2 (to_one = False)
        value=0.01 - pip location=-2
        value=0.001 - pip location=-3
        '''
        pip_location = 0
        if value == 0:
            return pip_location
        while True:
            mult = float(10 ** -pip_location)
            pips = value * mult
            if value >= 1:
                if pips <= 1:
                    if pips < 1 and not to_one:
                        pip_location -= 1
                    break
                pip_location += 1
            else:
                if pips > 1:
                    if to_one:
                        pip_location += 1
                    break
                elif pips == 1:
                    break
                pip_location -= 1
        return pip_location

    def pips_from_value(self, value, pip_precision=0, pip_location=None):
        '''
        Returns pips from a price value
        '''
        if pip_location is None:
            pip_location = self.contractdetails.get(
                'pipLocation', 0)
        return get_pips_from_value(value, pip_location, pip_precision)

    def value_from_pips(self, pips, pip_location=None, precision=None):
        '''
        Returns price difference from pips
        '''
        if pip_location is None:
            pip_location = self.contractdetails.get(
                'pipLocation', 0)
        if precision is None:
            precision = self.contractdetails.get(
                'displayPrecision', 1)
        return get_value_from_pips(pips, pip_location, precision)

    def price_value(self, price, precision=None):
        '''
        Returns a rounded price value
        '''
        if precision is None:
            precision = self.contractdetails.get(
                'displayPrecision', 1)
        return get_price_value(price, precision)

    def round_to_pip(self, value, round_up=True, round_to_pip=0.5,
                     ensure_dist=False, pip_location=None, precision=None):
        '''
        Rounding to pip
        '''
        if pip_location is None:
            pip_location = self.contractdetails.get(
                'pipLocation', 0)
        if precision is None:
            precision = self.contractdetails.get(
                'displayPrecision', 1)
        return get_round_to_pip(value, pip_location, precision,
                                round_up=round_up, round_to_pip=round_to_pip,
                                ensure_dist=ensure_dist)

    def is_within_market_hours(self):
        '''
        Checks if current time is within market hours
        '''
        # collect all valid market hours
        hours = self.p.custom_market_hours
        for i, v in enumerate(self.MARKETS):
            if v not in self.p.markets:
                continue
            # get hours
            if i != self.MARKET_CUSTOM:
                hours += self.MARKET_HOURS[i]

        # if no market hours set, no need to check anything
        if not len(hours):
            return True

        # check if trade data datetime is within set market hours
        within = False
        for h in hours:
            if len(h) > 4:
                current = self.data.datetime.datetime(
                    tz=pytz.timezone(h[4]))
            else:
                current = self.data.datetime.datetime(
                    tz=pytz.utc)
            # ensure time is not below start
            if ((current.hour == h[0] and current.minute >= h[1])
                    or current.hour > h[0]
                    or current.hour == h[2]):
                # ensure time is not over end
                if (current.hour < h[2]
                        or (current.hour == h[2] and current.minute < h[3])):
                    within = True
                    break
        return within
