"""
SCLU Trading Strategy Implementation.

This module contains the SCLU (Smart Capital Live Unleashed) trading strategy
specifically designed for naked option buying during short covering and long 
unwinding rallies, based on Open Interest derivative analysis.
"""

import backtrader as bt
from typing import Optional, Any
from datetime import datetime

from ..indicators.open_interest import (
    OpenInterestIndicator,
    OpenInterestDerivative, 
    OpenInterestSecondDerivative
)


class SCLUStrategy(bt.Strategy):
    """
    SCLU Trading Strategy for Short Covering and Long Unwinding.
    
    This strategy is specifically designed for naked option buying during:
    1. Short covering rallies (Call options)
    2. Long unwinding rallies (Put options)
    
    The strategy works best in:
    - Low VIX environments
    - Near-term options (1-2 DTE, not 0 DTE)
    - ATM and OTM strikes (ATM +1/+2/+3)
    
    Signal Generation:
    - Buy: First derivative negative AND second derivative < -0.5% of 50-period OI MA
    - Sell: First derivative > -0.1% of 50-period OI MA OR second derivative > -0.5% of 50-period OI MA
    
    The premise is that when option sellers' stop losses are hit during forced exits,
    it creates opportunities for option buyers to capitalize on the resulting price swings.
    
    Parameters:
        oi_ma_period (int): Moving average period for OI baseline (default: 50)
        entry_threshold_pct (float): Second derivative entry threshold as % of OI MA (default: 0.005 = 0.5%)
        exit_doi_threshold_pct (float): First derivative exit threshold as % of OI MA (default: 0.001 = 0.1%)
        exit_d2oi_threshold_pct (float): Second derivative exit threshold as % of OI MA (default: 0.005 = 0.5%)
        max_positions (int): Maximum concurrent positions (default: 1)
        min_dte (int): Minimum days to expiry (default: 1)
        max_dte (int): Maximum days to expiry (default: 4)
    """
    
    params = (
        ('oi_ma_period', 50),
        ('entry_threshold_pct', 0.005),  # 0.5% of OI MA for entry
        ('exit_doi_threshold_pct', 0.001),  # 0.1% of OI MA for DOI exit
        ('exit_d2oi_threshold_pct', 0.005),  # 0.5% of OI MA for D2OI exit
        ('max_positions', 1),
        ('min_dte', 1),
        ('max_dte', 4),
        ('stop_loss_pct', 0.15),  # 15% stop loss
        ('take_profit_pct', 0.30),  # 30% take profit for short covering rallies
    )
    
    def __init__(self) -> None:
        """Initialize the strategy with indicators and state variables."""
        super().__init__()
        
        # Data references
        self.dataclose = self.datas[0].close
        
        # Custom Open Interest indicators
        self.oi_indicator = OpenInterestIndicator(self.datas[0])
        self.doi_indicator = OpenInterestDerivative(self.datas[0])
        self.d2oi_indicator = OpenInterestSecondDerivative(self.datas[0])
        
        # 50-period moving average of Open Interest (as per strategy document)
        self.oi_ma = bt.indicators.SimpleMovingAverage(
            self.datas[0].openinterest, 
            period=self.params.oi_ma_period
        )
        
        # State variables
        self.order: Optional[bt.Order] = None
        self.buyprice: Optional[float] = None
        self.buycomm: Optional[float] = None
        
        # Performance tracking
        self.trade_count = 0
        self.winning_trades = 0
        self.short_covering_trades = 0
        self.long_unwinding_trades = 0
    
    def log(self, txt: str, dt: Optional[datetime] = None) -> None:
        """
        Logging function for strategy events.
        
        Args:
            txt: Text message to log
            dt: Optional datetime, uses current bar datetime if None
        """
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')
    
    def notify_order(self, order: bt.Order) -> None:
        """
        Handle order status notifications.
        
        Args:
            order: The order object with status information
        """
        if order.status in [order.Submitted, order.Accepted]:
            return  # Order submitted/accepted - nothing to do
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED - Price: {order.executed.price:.2f}, '
                    f'Cost: {order.executed.value:.2f}, '
                    f'Commission: {order.executed.comm:.2f}'
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell order
                self.log(
                    f'SELL EXECUTED - Price: {order.executed.price:.2f}, '
                    f'Cost: {order.executed.value:.2f}, '
                    f'Commission: {order.executed.comm:.2f}'
                )
            
            self.bar_executed = len(self)
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        
        self.order = None
    
    def notify_trade(self, trade: bt.Trade) -> None:
        """
        Handle trade completion notifications.
        
        Args:
            trade: The completed trade object
        """
        if not trade.isclosed:
            return
        
        self.trade_count += 1
        if trade.pnl > 0:
            self.winning_trades += 1
        
        win_rate = (self.winning_trades / self.trade_count) * 100
        
        self.log(
            f'TRADE CLOSED - PnL: {trade.pnl:.2f}, '
            f'Net PnL: {trade.pnlcomm:.2f}, '
            f'Win Rate: {win_rate:.1f}%'
        )
    
    def _is_short_covering_signal(self) -> bool:
        """
        Check if conditions indicate a short covering opportunity.
        
        As per strategy document:
        - Buy when first derivative is negative AND 
        - Second derivative < -0.5% of 50-period OI moving average
        
        Returns:
            bool: True if short covering signal detected
        """
        # First derivative must be negative (OI decreasing)
        doi_negative = self.doi_indicator[0] < 0
        
        # Second derivative threshold: -0.5% of 50-period OI MA
        d2oi_threshold = -self.params.entry_threshold_pct * self.oi_ma[0]
        d2oi_condition = self.d2oi_indicator[0] < d2oi_threshold
        
        return doi_negative and d2oi_condition
    
    def _should_exit_position(self) -> tuple[bool, str]:
        """
        Check if conditions are met for exiting the position.
        
        As per strategy document:
        - Exit when first derivative > -0.1% of 50-period OI MA OR
        - Second derivative > -0.5% of 50-period OI MA
        
        Returns:
            tuple[bool, str]: (should_exit, exit_reason)
        """
        # First derivative exit condition: > -0.1% of OI MA
        doi_exit_threshold = -self.params.exit_doi_threshold_pct * self.oi_ma[0]
        doi_exit = self.doi_indicator[0] > doi_exit_threshold
        
        # Second derivative exit condition: > -0.5% of OI MA  
        d2oi_exit_threshold = -self.params.exit_d2oi_threshold_pct * self.oi_ma[0]
        d2oi_exit = self.d2oi_indicator[0] > d2oi_exit_threshold
        
        if doi_exit:
            return True, "First derivative exit: OI decline slowing"
        elif d2oi_exit:
            return True, "Second derivative exit: OI acceleration reversing"
        
        return False, ""
    
    def _check_stop_loss_take_profit(self) -> tuple[bool, str]:
        """
        Check if stop loss or take profit should be triggered.
        
        Returns:
            tuple[bool, str]: (should_exit, reason)
        """
        if not self.position or not self.buyprice:
            return False, ""
        
        current_price = self.dataclose[0]
        
        # Calculate stop loss and take profit levels
        stop_loss_price = self.buyprice * (1 - self.params.stop_loss_pct)
        take_profit_price = self.buyprice * (1 + self.params.take_profit_pct)
        
        if current_price <= stop_loss_price:
            return True, f'STOP LOSS triggered at {current_price:.2f}'
        
        if current_price >= take_profit_price:
            return True, f'TAKE PROFIT triggered at {current_price:.2f}'
        
        return False, ""
    
    def _log_signal_details(self, signal_type: str) -> None:
        """Log detailed signal information for analysis."""
        doi = self.doi_indicator[0]
        d2oi = self.d2oi_indicator[0]
        oi_ma = self.oi_ma[0]
        
        # Calculate thresholds
        entry_threshold = -self.params.entry_threshold_pct * oi_ma
        doi_exit_threshold = -self.params.exit_doi_threshold_pct * oi_ma
        d2oi_exit_threshold = -self.params.exit_d2oi_threshold_pct * oi_ma
        
        self.log(
            f'{signal_type} SIGNAL DETAILS:\n'
            f'  OI MA (50): {oi_ma:,.0f}\n'
            f'  DOI: {doi:.2f} (Exit threshold: {doi_exit_threshold:.2f})\n'
            f'  D2OI: {d2oi:.2f} (Entry: {entry_threshold:.2f}, Exit: {d2oi_exit_threshold:.2f})\n'
            f'  Price: {self.dataclose[0]:.2f}'
        )
    
    def next(self) -> None:
        """
        Main strategy logic executed on each bar.
        
        Implements the short covering/long unwinding strategy based on
        Open Interest derivative analysis as described in the strategy document.
        """
        # Skip if we have a pending order
        if self.order:
            return
        
        current_position_size = self.position.size
        
        if not current_position_size:  # Not in position
            # Look for short covering opportunities
            if self._is_short_covering_signal():
                self._log_signal_details('BUY')
                self.log(
                    f'SHORT COVERING DETECTED - Entering long position at {self.dataclose[0]:.2f}'
                )
                self.order = self.buy()
                self.short_covering_trades += 1
        
        else:  # In position
            # Check stop loss and take profit first
            sl_tp_exit, sl_tp_reason = self._check_stop_loss_take_profit()
            if sl_tp_exit:
                self.log(sl_tp_reason)
                self.order = self.sell()
                return
            
            # Check strategy-based exit conditions
            should_exit, exit_reason = self._should_exit_position()
            if should_exit:
                self._log_signal_details('SELL')
                self.log(f'EXIT SIGNAL - {exit_reason}')
                self.order = self.sell()
    
    def stop(self) -> None:
        """Called when the strategy finishes running."""
        if self.trade_count > 0:
            win_rate = (self.winning_trades / self.trade_count) * 100
            self.log(
                f'STRATEGY COMPLETED:\n'
                f'  Total Trades: {self.trade_count}\n'
                f'  Winning Trades: {self.winning_trades}\n'
                f'  Win Rate: {win_rate:.1f}%\n'
                f'  Short Covering Signals: {self.short_covering_trades}'
            )
        else:
            self.log('STRATEGY COMPLETED - No trades executed')


class SCLUStrikeSelector:
    """
    Helper class for selecting optimal strikes for SCLU strategy.
    
    Based on strategy document:
    - Focus on ATM and OTM options (ATM +1/+2/+3 strikes)
    - Calls for short covering, Puts for long unwinding
    - Greatest effect on outermost strikes due to delta drifting
    """
    
    @staticmethod
    def select_strikes(spot_price: float, available_strikes: list, 
                      movement_type: str = "short_covering", 
                      max_strikes: int = 3) -> list:
        """
        Select optimal strikes for the strategy.
        
        Args:
            spot_price: Current spot price of underlying
            available_strikes: List of available strike prices
            movement_type: "short_covering" or "long_unwinding"
            max_strikes: Maximum number of strikes to select
            
        Returns:
            list: Selected strike prices
        """
        # Find ATM strike
        atm_strike = min(available_strikes, key=lambda x: abs(x - spot_price))
        atm_index = available_strikes.index(atm_strike)
        
        selected_strikes = []
        
        if movement_type == "short_covering":
            # For short covering, focus on calls (strikes above spot)
            # ATM and OTM calls (ATM +1/+2/+3)
            for i in range(max_strikes):
                strike_index = atm_index + i
                if strike_index < len(available_strikes):
                    selected_strikes.append(available_strikes[strike_index])
        
        elif movement_type == "long_unwinding":
            # For long unwinding, focus on puts (strikes below spot)
            # ATM and OTM puts (ATM -1/-2/-3)
            for i in range(max_strikes):
                strike_index = atm_index - i
                if strike_index >= 0:
                    selected_strikes.append(available_strikes[strike_index])
        
        return selected_strikes
    
    @staticmethod
    def calculate_days_to_expiry(expiry_date: datetime, current_date: datetime) -> int:
        """
        Calculate days to expiry.
        
        Args:
            expiry_date: Option expiry date
            current_date: Current date
            
        Returns:
            int: Days to expiry
        """
        return (expiry_date - current_date).days
    
    @staticmethod
    def is_suitable_for_strategy(dte: int, min_dte: int = 1, max_dte: int = 4) -> bool:
        """
        Check if the option is suitable for SCLU strategy based on DTE.
        
        As per strategy document: 1-2 DTE preferred, not 0 DTE.
        
        Args:
            dte: Days to expiry
            min_dte: Minimum acceptable DTE
            max_dte: Maximum acceptable DTE
            
        Returns:
            bool: True if suitable for strategy
        """
        return min_dte <= dte <= max_dte