"""
SCLU - Smart Capital Live Unleashed

An algorithmic trading system for options trading using Open Interest analysis.
Designed for Indian stock markets (NSE) with support for backtesting and live trading.
"""

__version__ = "1.0.0"
__author__ = "Anish Rayaguru"
__email__ = "your.email@example.com"

from .strategies import SCLUStrategy
from .indicators import OpenInterestIndicator, OpenInterestDerivative, OpenInterestSecondDerivative

__all__ = [
    'SCLUStrategy',
    'OpenInterestIndicator', 
    'OpenInterestDerivative',
    'OpenInterestSecondDerivative'
]
