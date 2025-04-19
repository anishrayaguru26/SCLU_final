from __future__ import (absolute_import, division, print_function, unicode_literals)
#primary backtesting library is backtrader
#documentation link- https://www.backtrader.com/
import backtrader as bt
from datetime import datetime
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
import backtrader.utils.flushfile

import csv

import os
import sys 

cwd = os.chdir('/Users/anishrayaguru/Desktop/SCLU/datadumps2')
count = 0

#Declaration of custom indicators for first and second derivative of open interest
class OI(bt.Indicator):
    lines = ('oi',)
    plotinfo = dict(subplot=True)
    def next(self):
        self.lines.oi[0] = self.data.openinterest[0]

class dOI(bt.Indicator):
    #first derivative of open interest with respect to time as an indicator
    lines = ('doi',)
    plotinfo = dict(subplot=True)
    
    def init(self):
        self.lines.doi = self.data.openinterest
    def next(self):
        # if self.data.openinterest[0] != self.data.openinterest[-1]:
        #     self.lines.doi[0] = (self.data.openinterest[0] - self.data.openinterest[-1])
        #reasoning for the formula is attached in the report
        self.lines.doi[0] = (self.data.openinterest[0] - self.data.openinterest[-1])/3

class d2OI(bt.Indicator):
    #second derivative of open interest with respect to time as an indicator
    lines = ('d2oi',)
    plotinfo = dict(subplot=True)
    def init(self):
        self.lines.d2oi = 0
    def next(self):
        global count
        if count < 2:
            self.lines.d2oi[0] = 0
            count += 1
        else:
            #reasoning for the formula is given in the report
            self.lines.d2oi[0] = (self.data.openinterest[0] + self.data.openinterest[-2] - 
                                  2*(self.data.openinterest[-1]))/9

# Create a Strategy- backtrader definition of a strategy
class SCLU(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        #runs once at the start of the strategy
        # Keep a reference to the all relevant lines in the strategy-
        #close, open interest, first, second derivative and a 50 period moving avergae of open interest
        self.dataclose = self.datas[0].close
        self.oi_indicator = OI(self.datas[0])
        self.doi_indic = dOI(self.datas[0])
        self.d2oi_indic = d2OI(self.datas[0])
        self.oi50ma = bt.indicators.SimpleMovingAverage(self.datas[0].openinterest, period = 30)
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.refoima = 0


    def notify_order(self, order):
        #tells backtrader what to do when an order is placed, allows us to output the buy/sell price
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Checks if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    #gives us profit and loss when a trade is complete
    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
        

    def next(self):
        sens = 10/1000
        feel = 3*1000000
        if not self.position:#checks if we are in a trade- only one position at a time
            # Not yet ... we MIGHT BUY if ...
            if self.doi_indic[0] < 0 and self.d2oi_indic[0] < -0.1*sens*feel: 
                #^^primary buy conditions- if rate of change and second derivative meet the criteriion
                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                #print(self.oi50ma[0], "moving averge oi")
                self.refoima = self.oi50ma[-1]
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:

            # Already in the market ... we might sell
            if self.doi_indic[0] > -1*sens*feel and self.d2oi_indic[0] > -0.1*sens*feel:
                if self.doi_indic[0] > -1*sens*feel:
                    print("first derivative exit")
                else:
                    print("second derivative exit")
                #primary exit condition- again on first and second derivative of open interest
                #print(self.doi_indic[0])
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()




if __name__ == '__main__':
    # Create a cerebro entity- backtrader specification
    cerebro = bt.Cerebro()

    data0 = btfeeds.GenericCSVData(
    dataname=input("enter OHLCVOi filename- ") or '54000 ce 09-24.csv',
    #headers = False,
    #nullvalue=0.0,
    dtformat=(f'%Y-%m-%d %H:%M:%S+05:30'),
    #2024-07-03 09:15:00+05:30- how the date looks in our datasheet


    timeframe=bt.TimeFrame.Minutes,
    #compression = 3,

    datetime=0,
    #date = -1,
    time=-1,
    high=2,
    low=3,
    open=1,
    close=4,
    volume=5,
    openinterest=6
    )
    # Add the Data Feed to Cerebro

    cerebro.resampledata(data0,timeframe=bt.TimeFrame.Minutes,compression=3) 
    #one minute data is converted into 3 minute data, beacause open interest is only refreshed,
    #by NSE every 3 minutes
    
    # Set our desired cash start
    cerebro.broker.setcash(1000)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.addstrategy(SCLU)
    # Run over everything
    cerebro.run()
    #cerebro.plot(style = "candlestick")
    cerebro.plot() #makes our graph representing each trade
    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())