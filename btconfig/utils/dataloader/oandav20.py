from __future__ import division, absolute_import, print_function

import v20
import pandas as pd

from datetime import datetime, tzinfo
from dateutil import parser
from btoandav20.stores import OandaV20Store


class OandaV20DataloaderApp:

    def __init__(self, token, practice, debug=False, **kwargs):
        self.token = token
        self.practice = practice
        self.debug = debug
        self.ctx = v20.Context(OandaV20Store._OAPI_URL[int(practice)],
                               token=token, port=443, ssl=True, **kwargs)

    def request(self, instrument, timeframe, compression,
                fromdate, todate, bidask, useask):

        # set fetch params
        granularity = OandaV20Store._GRANULARITIES.get(
            (timeframe, compression), None)
        params = {'granularity': granularity, 'count': 5000, 'price': 'ABM'}
        ratesHeaders = ['datetime', 'open', 'high', 'low', 'close',
                        'mid_close', 'bid_close', 'ask_close', 'volume']

        data_df = None
        while True:
            params['fromTime'] = fromdate.strftime(OandaV20Store._DATE_FORMAT)
            if data_df is not None:
                params['includeFirst'] = False
            response = self.ctx.instrument.candles(instrument, **params)
            if self.debug:
                print(f'Processing {response.path}')
            candles = response.get('candles', 200)

            data = []
            for candle in candles:
                if not candle.complete:
                    continue
                curtime = datetime.strptime(
                    candle.time,
                    OandaV20Store._DATE_FORMAT)
                volume = candle.volume
                c_data = candle.dict()
                # get candle data
                price = {'bid': {}, 'ask': {}, 'mid': {}}
                for price_side in price:
                    price[price_side]['open'] = float(c_data[price_side]['o'])
                    price[price_side]['high'] = float(c_data[price_side]['h'])
                    price[price_side]['low'] = float(c_data[price_side]['l'])
                    price[price_side]['close'] = float(c_data[price_side]['c'])

                if bidask:
                    if useask:
                        o_price, h_price, l_price, c_price = price['ask'].values()
                    else:
                        o_price, h_price, l_price, c_price = price['bid'].values()
                else:
                    o_price, h_price, l_price, c_price = price['mid'].values()
                # store candle
                data.append({
                    'datetime': curtime,
                    'open': o_price, 'high': h_price,
                    'low': l_price, 'close': c_price,
                    'mid_close': price['mid']['close'],
                    'bid_close': price['bid']['close'],
                    'ask_close': price['ask']['close'],
                    'volume': volume
                })

            # check if data contains any candles
            if len(data) > 0:
                tmp_df = pd.DataFrame(data, columns=ratesHeaders)
            else:
                break

            if data_df is None:
                data_df = tmp_df
            else:
                data_df = pd.concat([data_df, tmp_df])
            fromdate = data_df['datetime'].iloc[-1]
            # stop if start time is higher than end date if defined
            if todate and fromdate > todate:
                break
        if data_df is not None:
            data_df['datetime'] = pd.to_datetime(data_df['datetime'])
        return data_df
