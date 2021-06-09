from btconfig.utils.dataloader.ib import IBDataloaderApp
import backtrader as bt
import datetime as dt

From = dt.date(2021, 4, 1)
To = dt.date(2021, 6, 4)

downloader = IBDataloaderApp(port=7497)
downloader.request("EUR.USD-CASH-IDEALPRO", bt.TimeFrame.Minutes, 1, fromdate=From, todate=To, what="MIDPOINT", useRTH=True)

df = downloader.get_df()
