"""
Data loading utilities for SCLU trading system.

This module provides functionality to load historical market data
from various sources including CSV files and live API feeds.
"""

import os
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

import backtrader.feeds as btfeeds

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataLoader:
    """
    Data loading and management class for SCLU trading system.
    
    Handles loading historical data from CSV files and formatting
    it for use with backtrader or direct analysis.
    """
    
    def __init__(self, data_directory: Optional[str] = None) -> None:
        """
        Initialize the DataLoader.
        
        Args:
            data_directory: Directory containing historical data files
        """
        self.data_directory = Path(data_directory) if data_directory else None
        logger.info(f"DataLoader initialized with directory: {self.data_directory}")
    
    def load_csv_data(
        self,
        filename: str,
        datetime_format: str = '%Y-%m-%d %H:%M:%S+05:30',
        **kwargs
    ) -> pd.DataFrame:
        """
        Load OHLCV+OI data from a CSV file.
        
        Args:
            filename: Name of the CSV file (with or without path)
            datetime_format: Format string for parsing datetime
            **kwargs: Additional arguments passed to pd.read_csv
            
        Returns:
            pd.DataFrame: Loaded and formatted data
            
        Raises:
            FileNotFoundError: If the specified file doesn't exist
            ValueError: If the data format is invalid
        """
        # Determine full file path
        if self.data_directory and not os.path.isabs(filename):
            filepath = self.data_directory / filename
        else:
            filepath = Path(filename)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        logger.info(f"Loading data from: {filepath}")
        
        try:
            # Default CSV reading parameters for SCLU data format
            default_params = {
                'parse_dates': [0],
                'date_parser': lambda x: pd.to_datetime(x, format=datetime_format),
                'index_col': 0
            }
            default_params.update(kwargs)
            
            df = pd.read_csv(filepath, **default_params)
            
            # Validate required columns
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                # Try to map common column variations
                column_mapping = {
                    'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume',
                    'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
                }
                
                df = df.rename(columns=column_mapping)
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Add open interest column if not present
            if 'oi' not in df.columns and 'openinterest' not in df.columns:
                logger.warning("Open Interest column not found, adding zeros")
                df['oi'] = 0
            elif 'openinterest' in df.columns:
                df['oi'] = df['openinterest']
            
            logger.info(f"Loaded {len(df)} data points from {filepath}")
            return df
        
        except Exception as e:
            logger.error(f"Error loading data from {filepath}: {e}")
            raise
    
    def create_backtrader_feed(
        self,
        filename: str,
        datetime_format: str = '%Y-%m-%d %H:%M:%S+05:30',
        timeframe_minutes: int = 3,
        **kwargs
    ) -> btfeeds.GenericCSVData:
        """
        Create a backtrader data feed from a CSV file.
        
        Args:
            filename: CSV file name/path
            datetime_format: DateTime format string
            timeframe_minutes: Timeframe in minutes for resampling
            **kwargs: Additional parameters for GenericCSVData
            
        Returns:
            btfeeds.GenericCSVData: Configured backtrader data feed
        """
        # Determine full file path
        if self.data_directory and not os.path.isabs(filename):
            filepath = str(self.data_directory / filename)
        else:
            filepath = filename
        
        logger.info(f"Creating backtrader feed for: {filepath}")
        
        # Default parameters for SCLU CSV format
        default_params = {
            'dataname': filepath,
            'dtformat': datetime_format,
            'timeframe': btfeeds.TimeFrame.Minutes,
            'datetime': 0,
            'time': -1,
            'open': 1,
            'high': 2,
            'low': 3,
            'close': 4,
            'volume': 5,
            'openinterest': 6
        }
        default_params.update(kwargs)
        
        return btfeeds.GenericCSVData(**default_params)
    
    def list_available_files(self, pattern: str = "*.csv") -> List[str]:
        """
        List available data files in the data directory.
        
        Args:
            pattern: File pattern to match (default: "*.csv")
            
        Returns:
            List[str]: List of matching file names
        """
        if not self.data_directory:
            logger.warning("No data directory specified")
            return []
        
        try:
            files = list(self.data_directory.glob(pattern))
            file_names = [f.name for f in files]
            logger.info(f"Found {len(file_names)} files matching pattern '{pattern}'")
            return sorted(file_names)
        
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    def get_file_info(self, filename: str) -> Dict[str, Any]:
        """
        Get information about a data file.
        
        Args:
            filename: Name of the file to analyze
            
        Returns:
            Dict[str, Any]: File information including size, date range, etc.
        """
        if self.data_directory and not os.path.isabs(filename):
            filepath = self.data_directory / filename
        else:
            filepath = Path(filename)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        try:
            # Get basic file info
            stat = filepath.stat()
            info = {
                'filename': filepath.name,
                'size_bytes': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
            }
            
            # Try to get data info
            try:
                df = self.load_csv_data(str(filepath))
                info.update({
                    'record_count': len(df),
                    'date_range': {
                        'start': df.index.min(),
                        'end': df.index.max()
                    },
                    'columns': list(df.columns)
                })
            except Exception as e:
                logger.warning(f"Could not analyze data content: {e}")
                info['data_error'] = str(e)
            
            return info
        
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            raise
