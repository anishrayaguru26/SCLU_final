#%%

from __future__ import (absolute_import, division, print_function, unicode_literals)
import yfinance as yf
import backtrader as bt
import pandas as pd
#import datetime
from datetime import date, timedelta, datetime
import requests
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
import backtrader.utils.flushfile
from kiteconnect import KiteConnect
import csv
import math
import os


cwd = os.chdir('/Users/anishrayaguru/Desktop/SCLU')

#api_key = 'u41udga7y4fg9c7n'
#api_secret = 'h3ryj18hpw8eg8t9dlcu52x5hzzuasg5'
#kite = KiteConnect(api_key= api_key)
#print(kite.login_url())
#request_token = str(input("input request token after loading above URL- "))
#data = kite.generate_session(request_token, api_secret)
#access_token = data["access_token"]

access_token = open("access_token.txt", 'r').read()
key_secret = open("api_key.txt", 'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)


fields = ['date', 'open', 'high', 'low', 'close', 'volume', 'oi']
count = -1
instrumenttokens = [int(input("enter instrument token"))]
fromdate = input("YYYY-MM-DD, from date") or datetime.today().strftime('%Y-%m-%d')
todate = input("YYYY-MM-DD, to date") or datetime.today().strftime('%Y-%m-%d')
names = [input("filename without the .csv- ")]

try:
   os.mkdir("./datadumps2")
except OSError as e:
   print("Directory exists")

"""
with open("./CSV/" + f + ".csv", newline="") as csvfile:
   [...]
"""

for i in instrumenttokens:
    stock_code = i
    count += 1
    naam = "./datadumps2/" + str(names[count])+ " " + str(i)+ ".csv"
    kitedata5m = kite.historical_data(instrument_token = stock_code, from_date = fromdate, to_date = todate, 
                                      interval = "3minute", oi = True)
    with open(naam, mode="w", newline='') as csvfile0:
        print(str(count + 1) + "successful")
        writer = csv.DictWriter(csvfile0, fieldnames=fields)
        writer.writeheader()
        writer.writerows(kitedata5m)

#/Users/anishrayaguru/Desktop/SCLU/datadumps2
#/Users/anishrayaguru/Desktop/SCLU/datadumpsp2