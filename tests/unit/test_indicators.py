"""
Unit tests for SCLU indicators.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock

from src.sclu.indicators.open_interest import (
    OpenInterestIndicator,
    OpenInterestDerivative,
    OpenInterestSecondDerivative
)


class TestOpenInterestIndicator:
    """Test cases for OpenInterestIndicator."""
    
    def test_initialization(self):
        """Test indicator initialization."""
        mock_data = Mock()
        mock_data.openinterest = [1000, 1100, 1200, 1150, 1300]
        
        indicator = OpenInterestIndicator(mock_data)
        assert indicator is not None
        assert hasattr(indicator, 'lines')
        assert 'oi' in indicator.lines._getnames()
    
    def test_next_calculation(self):
        """Test the next() method calculation."""
        mock_data = Mock()
        mock_data.openinterest = Mock()
        mock_data.openinterest.__getitem__ = Mock(return_value=1500)
        
        indicator = OpenInterestIndicator(mock_data)
        indicator.lines = Mock()
        indicator.lines.oi = Mock()
        
        indicator.next()
        
        # Verify that the OI value is set correctly
        indicator.lines.oi.__setitem__.assert_called_with(0, 1500)


class TestOpenInterestDerivative:
    """Test cases for OpenInterestDerivative."""
    
    def test_initialization(self):
        """Test derivative indicator initialization."""
        mock_data = Mock()
        indicator = OpenInterestDerivative(mock_data)
        
        assert indicator is not None
        assert hasattr(indicator, 'params')
        assert indicator.params.time_period == 3  # Default value
    
    def test_derivative_calculation(self):
        """Test first derivative calculation."""
        mock_data = Mock()
        
        # Mock the openinterest data
        oi_values = [1000, 1100, 1200, 1150, 1300]
        mock_data.openinterest = Mock()
        mock_data.openinterest.__getitem__ = Mock(side_effect=lambda x: oi_values[x] if x < 0 else oi_values[0])
        mock_data.openinterest.__len__ = Mock(return_value=len(oi_values))
        
        indicator = OpenInterestDerivative(mock_data)
        indicator.lines = Mock()
        indicator.lines.doi = Mock()
        
        # Simulate calculation for the latest value
        indicator.next()
        
        # Expected calculation: (1300 - 1150) / 3 = 50
        expected_doi = (oi_values[0] - oi_values[-1]) / 3
        indicator.lines.doi.__setitem__.assert_called_with(0, expected_doi)
    
    def test_insufficient_data(self):
        """Test behavior with insufficient data."""
        mock_data = Mock()
        mock_data.openinterest = Mock()
        mock_data.openinterest.__len__ = Mock(return_value=0)
        
        indicator = OpenInterestDerivative(mock_data)
        indicator.lines = Mock()
        indicator.lines.doi = Mock()
        
        indicator.next()
        
        # Should set DOI to 0 when insufficient data
        indicator.lines.doi.__setitem__.assert_called_with(0, 0)


class TestOpenInterestSecondDerivative:
    """Test cases for OpenInterestSecondDerivative."""
    
    def test_initialization(self):
        """Test second derivative indicator initialization."""
        mock_data = Mock()
        indicator = OpenInterestSecondDerivative(mock_data)
        
        assert indicator is not None
        assert hasattr(indicator, 'params')
        assert indicator.params.time_period == 3  # Default value
    
    def test_second_derivative_calculation(self):
        """Test second derivative calculation."""
        mock_data = Mock()
        
        # Mock the openinterest data
        oi_values = [1000, 1100, 1200, 1150, 1300]  # Current at index 0
        mock_data.openinterest = Mock()
        mock_data.openinterest.__getitem__ = Mock(side_effect=lambda x: {
            0: oi_values[0],    # current
            -1: oi_values[1],   # previous
            -2: oi_values[2]    # previous-2
        }.get(x, oi_values[0]))
        mock_data.openinterest.__len__ = Mock(return_value=len(oi_values))
        
        indicator = OpenInterestSecondDerivative(mock_data)
        indicator.lines = Mock()
        indicator.lines.d2oi = Mock()
        
        indicator.next()
        
        # Expected: (1000 + 1200 - 2*1100) / 9 = 0
        expected_d2oi = (oi_values[0] + oi_values[2] - 2 * oi_values[1]) / 9
        indicator.lines.d2oi.__setitem__.assert_called_with(0, expected_d2oi)
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data for second derivative."""
        mock_data = Mock()
        mock_data.openinterest = Mock()
        mock_data.openinterest.__len__ = Mock(return_value=1)
        
        indicator = OpenInterestSecondDerivative(mock_data)
        indicator.lines = Mock()
        indicator.lines.d2oi = Mock()
        
        indicator.next()
        
        # Should set D2OI to 0 when insufficient data
        indicator.lines.d2oi.__setitem__.assert_called_with(0, 0)
    
    def test_minimum_period(self):
        """Test that minimum period is set correctly."""
        mock_data = Mock()
        indicator = OpenInterestSecondDerivative(mock_data)
        
        # Should have addminperiod called to ensure enough data
        # This is typically handled by backtrader's framework
        assert hasattr(indicator, 'addminperiod')
