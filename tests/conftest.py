"""
Pytest configuration and shared fixtures for SCLU tests.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from pathlib import Path
import tempfile
import shutil

from src.sclu.utils import Config
from src.sclu.api import KiteClient


@pytest.fixture
def sample_config():
    """Provide a sample configuration for testing."""
    config = Config()
    config._config.api.api_key = "test_api_key"
    config._config.api.access_token = "test_access_token"
    config._config.trading.sensitivity = 0.01
    config._config.trading.feeling = 3000000
    config._config.trading.max_daily_trades = 10
    return config


@pytest.fixture
def sample_ohlcv_data():
    """Provide sample OHLCV data for testing."""
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=10),
        end=datetime.now(),
        freq='3T'
    )
    
    data = {
        'open': [100 + i * 0.1 for i in range(len(dates))],
        'high': [101 + i * 0.1 for i in range(len(dates))],
        'low': [99 + i * 0.1 for i in range(len(dates))],
        'close': [100.5 + i * 0.1 for i in range(len(dates))],
        'volume': [1000 + i * 10 for i in range(len(dates))],
        'oi': [500000 + i * 1000 for i in range(len(dates))]
    }
    
    df = pd.DataFrame(data, index=dates)
    return df


@pytest.fixture
def sample_csv_data(sample_ohlcv_data, tmp_path):
    """Create a temporary CSV file with sample data."""
    csv_file = tmp_path / "sample_data.csv"
    
    # Reset index to include datetime as a column
    data_with_datetime = sample_ohlcv_data.reset_index()
    data_with_datetime.rename(columns={'index': 'datetime'}, inplace=True)
    
    # Format datetime to match expected format
    data_with_datetime['datetime'] = data_with_datetime['datetime'].dt.strftime(
        '%Y-%m-%d %H:%M:%S+05:30'
    )
    
    data_with_datetime.to_csv(csv_file, index=False)
    return str(csv_file)


@pytest.fixture
def mock_kite_client():
    """Provide a mocked Kite client for testing."""
    mock_client = Mock(spec=KiteClient)
    
    # Mock typical responses
    mock_client.get_instruments.return_value = pd.DataFrame({
        'instrument_token': [10716162, 10684418],
        'tradingsymbol': ['FINNIFTY24000CE', 'FINNIFTY23800PE'],
        'name': ['FINNIFTY', 'FINNIFTY'],
        'exchange': ['NFO', 'NFO']
    })
    
    mock_client.lookup_instrument.return_value = 'FINNIFTY24000CE'
    mock_client.place_market_order.return_value = 'order_123'
    
    return mock_client


@pytest.fixture
def temp_data_directory():
    """Provide a temporary directory for data files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_trade_data():
    """Provide sample trade execution data."""
    return {
        'symbol': 'FINNIFTY24000CE',
        'price': 50.75,
        'quantity': 25,
        'timestamp': datetime.now(),
        'doi': -25.5,
        'd2oi': -5.2,
        'signal': 'BUY'
    }


@pytest.fixture(scope="session")
def test_data_path():
    """Provide path to test data directory."""
    return Path(__file__).parent / "test_data"


# Markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow


# Custom assertion helpers
def assert_valid_signal(signal):
    """Assert that a signal is valid."""
    assert signal in ['BUY', 'SELL', 'HOLD'], f"Invalid signal: {signal}"


def assert_valid_price(price):
    """Assert that a price is valid."""
    assert isinstance(price, (int, float)), "Price must be numeric"
    assert price >= 0, "Price must be non-negative"


def assert_valid_dataframe(df, required_columns=None):
    """Assert that a DataFrame is valid for trading."""
    assert isinstance(df, pd.DataFrame), "Must be a pandas DataFrame"
    assert len(df) > 0, "DataFrame must not be empty"
    
    if required_columns:
        missing_cols = set(required_columns) - set(df.columns)
        assert not missing_cols, f"Missing required columns: {missing_cols}"


# Add custom assertion helpers to pytest namespace
pytest.assert_valid_signal = assert_valid_signal
pytest.assert_valid_price = assert_valid_price
pytest.assert_valid_dataframe = assert_valid_dataframe
