"""
Open Interest Indicators for SCLU Trading Strategy.

This module contains custom indicators for analyzing Open Interest data
in options trading. The indicators include:
- Open Interest Indicator
- First Derivative of Open Interest (rate of change)
- Second Derivative of Open Interest (acceleration/deceleration)
"""

import backtrader as bt
from typing import Any


class OpenInterestIndicator(bt.Indicator):
    """
    Basic Open Interest Indicator.
    
    This indicator simply tracks the open interest values from the data feed.
    Useful for plotting and analysis purposes.
    """
    
    lines = ('oi',)
    plotinfo = dict(subplot=True)
    
    def next(self) -> None:
        """Calculate the indicator value for the current period."""
        self.lines.oi[0] = self.data.openinterest[0]


class OpenInterestDerivative(bt.Indicator):
    """
    First Derivative of Open Interest Indicator.
    
    Calculates the rate of change of open interest over time as used in SCLU strategy.
    This measures the rate at which option sellers are closing/opening positions.
    
    As per SCLU strategy: When rate of change of OI decreases (negative), we buy.
    
    Formula: (Current OI - Previous OI) / time_period
    
    Parameters:
        time_period (int): Time period for derivative calculation (default: 3 for NSE 3-minute cycle)
    """
    
    lines = ('doi',)
    plotinfo = dict(subplot=True)
    params = (('time_period', 3),)
    
    def __init__(self) -> None:
        """Initialize the indicator."""
        super().__init__()
        self.lines.doi = self.data.openinterest
    
    def next(self) -> None:
        """
        Calculate the first derivative of open interest.
        
        As per SCLU strategy document:
        - Negative values indicate OI is decreasing (sellers exiting)
        - This is when we look for buying opportunities during short covering
        
        The formula divides by time_period to normalize the rate of change
        based on the NSE's 3-minute refresh cycle for open interest data.
        """
        if len(self.data.openinterest) > 1:
            self.lines.doi[0] = (
                self.data.openinterest[0] - self.data.openinterest[-1]
            ) / self.params.time_period
        else:
            self.lines.doi[0] = 0


class OpenInterestSecondDerivative(bt.Indicator):
    """
    Second Derivative of Open Interest Indicator.
    
    Calculates the acceleration/deceleration of open interest changes as used in SCLU strategy.
    This measures the rate of change of the rate of change of sellers in the market.
    
    As per SCLU strategy: 
    - Entry when second derivative < -0.5% of 50-period OI MA
    - Exit when second derivative > -0.5% of 50-period OI MA
    
    Formula: (Current OI + Previous-2 OI - 2*Previous OI) / time_period²
    
    Parameters:
        time_period (int): Time period for derivative calculation (default: 3)
    """
    
    lines = ('d2oi',)
    plotinfo = dict(subplot=True)
    params = (('time_period', 3),)
    
    def __init__(self) -> None:
        """Initialize the indicator."""
        super().__init__()
        self.addminperiod(2)  # Need at least 2 periods for second derivative
    
    def next(self) -> None:
        """
        Calculate the second derivative of open interest.
        
        As per SCLU strategy document:
        - Strong negative values indicate accelerating seller exit (opportunity)
        - Values returning towards zero indicate rally cooling off (exit signal)
        
        The formula uses the discrete second derivative approximation
        and normalizes by time_period squared (9 for 3-minute periods).
        """
        data_length = len(self.data.openinterest)
        
        if data_length < 2:
            self.lines.d2oi[0] = 0
        else:
            # Second derivative formula: f(n) + f(n-2) - 2*f(n-1)
            current_oi = self.data.openinterest[0]
            prev_oi = self.data.openinterest[-1]
            prev2_oi = self.data.openinterest[-2] if data_length > 2 else prev_oi
            
            self.lines.d2oi[0] = (
                current_oi + prev2_oi - 2 * prev_oi
            ) / (self.params.time_period ** 2)
