from __future__ import division, absolute_import, print_function

import pandas as pd
from dateutil import parser

import v20

from btoandav20.stores import OandaV20Store


class OandaV20DownloadApp:

    def __init__(self, token, practice):
        self.token = token
        self.practice = practice
        self.ctx = v20.Context(OandaV20Store._OAPI_URL[int(practice)],
                               token=token, port=443, ssl=True)

    def download(self, filename, instrument, timeframe, compression,
                 fromdate, todate, bidask, useask):

        # set fetch params
        granularity = OandaV20Store._GRANULARITIES.get(
            (timeframe, compression), None)
        params = {'granularity': granularity, 'count': 5000, 'price': 'ABM'}
        ratesHeaders = ['time', 'open', 'high', 'low', 'close', 'mid_close',
                        'bid_close', 'ask_close', 'volume']

        # Get start values
        try:
            data = pd.read_csv(filename)
            data_len = len(data)
            start = data.iloc[-1].time
            start = parser.parse(start)
        except IOError:
            data_len = 0
            start = fromdate
        end = None
        if todate:
            end = todate

        while True:
            # set new start time
            params['fromTime'] = start.strftime(OandaV20Store._DATE_FORMAT)

            # don't include first row if any row available, since start time is the
            # date of last row already downloaded
            if data_len > 0:
                params['includeFirst'] = False

            # fetch data
            response = self.ctx.instrument.candles(instrument, **params)
            try:
                candles = response.get('candles', 200)
            except Exception as e:
                print(e, response.body)
                return

            data = []
            for candle in candles:
                if not candle.complete:
                    continue
                curtime = candle.time
                volume = candle.volume
                c_data = candle.dict()
                # get candle data
                price = {'bid': {}, 'ask': {}, 'mid': {}}
                for price_side in price:
                    price[price_side]['open'] = c_data[price_side]['o']
                    price[price_side]['high'] = c_data[price_side]['h']
                    price[price_side]['low'] = c_data[price_side]['l']
                    price[price_side]['close'] = c_data[price_side]['c']

                if bidask:
                    if useask:
                        o_price, h_price, l_price, c_price = price['ask'].values()
                    else:
                        o_price, h_price, l_price, c_price = price['bid'].values()
                else:
                    o_price, h_price, l_price, c_price = price['mid'].values()
                # store candle
                data.append({
                    'time': curtime, 'volume': volume,
                    'open': o_price, 'high': h_price,
                    'low': l_price, 'close': c_price,
                    'mid_close': price['mid']['close'],
                    'bid_close': price['bid']['close'],
                    'ask_close': price['ask']['close']
                })

            # check if data contains any candles
            if len(data) > 0:
                ratesFromServer = pd.DataFrame(data, columns=ratesHeaders)
            else:
                break

            # if first line then output also headers
            if data_len == 0:
                ratesFromServer.to_csv(filename, index=False)
            else:
                ratesFromServer.to_csv(filename, header=None,
                                       index=False, mode='a')

            # set new start time and update number of downloaded rows
            start = parser.parse(ratesFromServer.iloc[-1].time)
            data_len += len(ratesFromServer)

            # stop if start time is higher than end date if defined
            if end and start > end:
                break
