"""
Integration tests for backtesting functionality.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

import backtrader as bt
from src.sclu.strategies import SCLUStrategy
from src.sclu.data import DataLoader


@pytest.mark.integration
class TestBacktestIntegration:
    """Integration tests for the complete backtesting pipeline."""
    
    def test_complete_backtest_workflow(self, sample_csv_data):
        """Test complete backtest from data loading to results."""
        # Create cerebro instance
        cerebro = bt.Cerebro()
        
        # Load data using DataLoader
        loader = DataLoader()
        data_feed = loader.create_backtrader_feed(sample_csv_data)
        
        # Add data to cerebro with resampling
        cerebro.resampledata(data_feed, timeframe=bt.TimeFrame.Minutes, compression=3)
        
        # Add strategy
        cerebro.addstrategy(SCLUStrategy, sensitivity=0.01, feeling=3000000)
        
        # Set broker parameters
        cerebro.broker.setcash(100000.0)
        cerebro.broker.setcommission(commission=0.001)
        
        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # Record starting value
        starting_value = cerebro.broker.getvalue()
        
        # Run backtest
        results = cerebro.run()
        
        # Get final value
        final_value = cerebro.broker.getvalue()
        
        # Basic assertions
        assert results is not None
        assert len(results) == 1
        assert starting_value > 0
        assert final_value >= 0  # Could be negative with losses
        
        # Check that analyzers ran
        strategy_result = results[0]
        assert hasattr(strategy_result, 'analyzers')
        assert hasattr(strategy_result.analyzers, 'sharpe')
        assert hasattr(strategy_result.analyzers, 'drawdown')
        assert hasattr(strategy_result.analyzers, 'trades')
    
    def test_strategy_with_different_parameters(self, sample_csv_data):
        """Test strategy with different parameter sets."""
        test_params = [
            {'sensitivity': 0.005, 'feeling': 2000000},
            {'sensitivity': 0.015, 'feeling': 4000000},
            {'sensitivity': 0.01, 'feeling': 3000000, 'oi_ma_period': 20}
        ]
        
        results = []
        
        for params in test_params:
            cerebro = bt.Cerebro()
            
            # Load data
            loader = DataLoader()
            data_feed = loader.create_backtrader_feed(sample_csv_data)
            cerebro.resampledata(data_feed, timeframe=bt.TimeFrame.Minutes, compression=3)
            
            # Add strategy with specific parameters
            cerebro.addstrategy(SCLUStrategy, **params)
            
            # Set broker
            cerebro.broker.setcash(100000.0)
            
            # Run backtest
            starting_value = cerebro.broker.getvalue()
            result = cerebro.run()
            final_value = cerebro.broker.getvalue()
            
            results.append({
                'params': params,
                'starting_value': starting_value,
                'final_value': final_value,
                'return': (final_value - starting_value) / starting_value
            })
        
        # Verify all backtests completed
        assert len(results) == len(test_params)
        
        # All should have valid results
        for result in results:
            assert result['starting_value'] > 0
            assert result['final_value'] >= 0
            assert isinstance(result['return'], float)
    
    @pytest.mark.slow
    def test_extended_backtest_with_multiple_timeframes(self, sample_ohlcv_data):
        """Test backtest with multiple timeframe compressions."""
        timeframes = [1, 3, 5, 15]  # Different minute compressions
        
        for tf in timeframes:
            cerebro = bt.Cerebro()
            
            # Create data feed directly from DataFrame
            data_feed = bt.feeds.PandasData(
                dataname=sample_ohlcv_data,
                datetime=None,  # Use index
                open='open',
                high='high',
                low='low',
                close='close',
                volume='volume',
                openinterest='oi'
            )
            
            # Resample to target timeframe
            cerebro.resampledata(data_feed, timeframe=bt.TimeFrame.Minutes, compression=tf)
            
            # Add strategy
            cerebro.addstrategy(SCLUStrategy)
            cerebro.broker.setcash(100000.0)
            
            # Run and verify
            starting_value = cerebro.broker.getvalue()
            results = cerebro.run()
            final_value = cerebro.broker.getvalue()
            
            assert results is not None
            assert starting_value > 0
            assert final_value >= 0
    
    def test_data_loader_integration(self, sample_csv_data):
        """Test DataLoader integration with backtesting."""
        loader = DataLoader()
        
        # Test CSV loading
        df = loader.load_csv_data(sample_csv_data)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        
        # Required columns for backtesting
        required_cols = ['open', 'high', 'low', 'close', 'volume', 'oi']
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"
        
        # Test backtrader feed creation
        data_feed = loader.create_backtrader_feed(sample_csv_data)
        assert data_feed is not None
        
        # Test integration with cerebro
        cerebro = bt.Cerebro()
        cerebro.resampledata(data_feed, timeframe=bt.TimeFrame.Minutes, compression=3)
        cerebro.addstrategy(SCLUStrategy)
        cerebro.broker.setcash(10000.0)
        
        results = cerebro.run()
        assert results is not None
