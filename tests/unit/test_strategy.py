"""
Unit tests for SCLU trading strategy.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.sclu.strategies.sclu_strategy import SCLUStrategy


class TestSCLUStrategy:
    """Test cases for SCLU trading strategy."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a mock data feed
        self.mock_data = Mock()
        self.mock_data.close = Mock()
        self.mock_data.openinterest = Mock()
        self.mock_data.datetime = Mock()
        self.mock_data.datetime.date.return_value = datetime.now().date()
        
        # Create strategy instance with mock data
        self.strategy = SCLUStrategy()
        self.strategy.datas = [self.mock_data]
        
        # Mock the indicators
        self.strategy.oi_indicator = Mock()
        self.strategy.doi_indicator = Mock()
        self.strategy.d2oi_indicator = Mock()
        self.strategy.oi_ma = Mock()
        
        # Mock other attributes
        self.strategy.position = Mock()
        self.strategy.position.size = 0
        self.strategy.order = None
        self.strategy.dataclose = Mock()
        self.strategy.dataclose.__getitem__ = Mock(return_value=100.0)
    
    def test_initialization(self):
        """Test strategy initialization."""
        strategy = SCLUStrategy()
        
        # Check that strategy has required parameters
        assert hasattr(strategy, 'params')
        assert hasattr(strategy.params, 'sensitivity')
        assert hasattr(strategy.params, 'feeling')
        assert hasattr(strategy.params, 'oi_ma_period')
        
        # Check default parameter values
        assert strategy.params.sensitivity == 10/1000
        assert strategy.params.feeling == 3000000
        assert strategy.params.oi_ma_period == 30
    
    def test_log_method(self):
        """Test the logging method."""
        with patch('builtins.print') as mock_print:
            self.strategy.log("Test message")
            mock_print.assert_called_once()
            args = mock_print.call_args[0][0]
            assert "Test message" in args
    
    def test_should_enter_long_buy_signal(self):
        """Test buy signal generation."""
        # Set up indicators for buy signal
        self.strategy.doi_indicator.__getitem__ = Mock(return_value=-1.0)
        self.strategy.d2oi_indicator.__getitem__ = Mock(return_value=-500.0)
        
        result = self.strategy._should_enter_long()
        assert result is True
    
    def test_should_enter_long_no_signal(self):
        """Test no buy signal when conditions not met."""
        # Set up indicators for no signal
        self.strategy.doi_indicator.__getitem__ = Mock(return_value=1.0)  # Positive DOI
        self.strategy.d2oi_indicator.__getitem__ = Mock(return_value=0.0)
        
        result = self.strategy._should_enter_long()
        assert result is False
    
    def test_should_exit_long_doi_exit(self):
        """Test exit signal based on DOI."""
        # Set up indicators for DOI-based exit
        sens = self.strategy.params.sensitivity
        feel = self.strategy.params.feeling
        
        self.strategy.doi_indicator.__getitem__ = Mock(return_value=sens * feel * 0.5)  # Above threshold
        self.strategy.d2oi_indicator.__getitem__ = Mock(return_value=-100.0)
        
        result = self.strategy._should_exit_long()
        assert result is True
    
    def test_should_exit_long_d2oi_exit(self):
        """Test exit signal based on D2OI."""
        # Set up indicators for D2OI-based exit
        sens = self.strategy.params.sensitivity
        feel = self.strategy.params.feeling
        
        self.strategy.doi_indicator.__getitem__ = Mock(return_value=-100.0)
        self.strategy.d2oi_indicator.__getitem__ = Mock(return_value=sens * feel * 0.05)  # Above threshold
        
        result = self.strategy._should_exit_long()
        assert result is True
    
    def test_check_stop_loss_triggered(self):
        """Test stop loss functionality."""
        self.strategy.position.size = 1  # In position
        self.strategy.buyprice = 100.0
        self.strategy.dataclose.__getitem__ = Mock(return_value=95.0)  # 5% loss
        
        result = self.strategy._check_stop_loss_take_profit()
        assert result is True
    
    def test_check_take_profit_triggered(self):
        """Test take profit functionality."""
        self.strategy.position.size = 1  # In position
        self.strategy.buyprice = 100.0
        self.strategy.dataclose.__getitem__ = Mock(return_value=110.0)  # 10% gain
        
        result = self.strategy._check_stop_loss_take_profit()
        assert result is True
    
    def test_check_stop_loss_not_triggered(self):
        """Test stop loss not triggered when within limits."""
        self.strategy.position.size = 1  # In position
        self.strategy.buyprice = 100.0
        self.strategy.dataclose.__getitem__ = Mock(return_value=98.0)  # 2% loss (within limit)
        
        result = self.strategy._check_stop_loss_take_profit()
        assert result is False
    
    def test_next_method_buy_signal(self):
        """Test next() method with buy signal."""
        # Set up for buy signal
        self.strategy.position.size = 0  # Not in position
        self.strategy.order = None
        
        # Mock the signal generation methods
        with patch.object(self.strategy, '_should_enter_long', return_value=True), \
             patch.object(self.strategy, 'buy') as mock_buy:
            
            self.strategy.next()
            mock_buy.assert_called_once()
    
    def test_next_method_sell_signal(self):
        """Test next() method with sell signal."""
        # Set up for sell signal
        self.strategy.position.size = 1  # In position
        self.strategy.order = None
        
        # Mock the signal generation methods
        with patch.object(self.strategy, '_should_exit_long', return_value=True), \
             patch.object(self.strategy, '_check_stop_loss_take_profit', return_value=False), \
             patch.object(self.strategy, 'sell') as mock_sell:
            
            self.strategy.next()
            mock_sell.assert_called_once()
    
    def test_next_method_pending_order(self):
        """Test next() method with pending order."""
        # Set up with pending order
        self.strategy.order = Mock()  # Pending order
        
        with patch.object(self.strategy, '_should_enter_long') as mock_enter, \
             patch.object(self.strategy, 'buy') as mock_buy:
            
            self.strategy.next()
            
            # Should not place new order when one is pending
            mock_enter.assert_not_called()
            mock_buy.assert_not_called()
    
    def test_notify_order_completed_buy(self):
        """Test order notification for completed buy order."""
        order = Mock()
        order.status = order.Completed
        order.isbuy.return_value = True
        order.executed.price = 50.0
        order.executed.value = 1250.0
        order.executed.comm = 1.25
        
        with patch.object(self.strategy, 'log') as mock_log:
            self.strategy.notify_order(order)
            mock_log.assert_called()
            assert self.strategy.buyprice == 50.0
            assert self.strategy.buycomm == 1.25
    
    def test_notify_order_completed_sell(self):
        """Test order notification for completed sell order."""
        order = Mock()
        order.status = order.Completed
        order.isbuy.return_value = False
        order.executed.price = 55.0
        order.executed.value = 1375.0
        order.executed.comm = 1.375
        
        with patch.object(self.strategy, 'log') as mock_log:
            self.strategy.notify_order(order)
            mock_log.assert_called()
    
    def test_notify_trade_closed(self):
        """Test trade notification when trade is closed."""
        trade = Mock()
        trade.isclosed = True
        trade.pnl = 125.0
        trade.pnlcomm = 122.5
        
        self.strategy.trade_count = 0
        self.strategy.winning_trades = 0
        
        with patch.object(self.strategy, 'log') as mock_log:
            self.strategy.notify_trade(trade)
            mock_log.assert_called()
            assert self.strategy.trade_count == 1
            assert self.strategy.winning_trades == 1  # Positive PnL
    
    def test_notify_trade_losing_trade(self):
        """Test trade notification for losing trade."""
        trade = Mock()
        trade.isclosed = True
        trade.pnl = -75.0
        trade.pnlcomm = -76.25
        
        self.strategy.trade_count = 0
        self.strategy.winning_trades = 0
        
        with patch.object(self.strategy, 'log') as mock_log:
            self.strategy.notify_trade(trade)
            mock_log.assert_called()
            assert self.strategy.trade_count == 1
            assert self.strategy.winning_trades == 0  # Negative PnL
    
    def test_strategy_parameters_customization(self):
        """Test strategy with custom parameters."""
        custom_params = {
            'sensitivity': 0.005,
            'feeling': 5000000,
            'oi_ma_period': 20,
            'stop_loss_pct': 0.03,
            'take_profit_pct': 0.15
        }
        
        # This would typically be done when adding strategy to cerebro
        strategy = SCLUStrategy()
        for param, value in custom_params.items():
            setattr(strategy.params, param, value)
        
        assert strategy.params.sensitivity == 0.005
        assert strategy.params.feeling == 5000000
        assert strategy.params.oi_ma_period == 20
        assert strategy.params.stop_loss_pct == 0.03
        assert strategy.params.take_profit_pct == 0.15
