"""
Data processing utilities for SCLU trading system.

This module provides data cleaning, transformation, and analysis
functionality for market data used in the SCLU trading strategy.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataProcessor:
    """
    Data processing and analysis utilities for market data.
    
    Provides methods for cleaning, transforming, and analyzing
    OHLCV+OI data for use in trading strategies.
    """
    
    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate market data.
        
        Args:
            df: Raw market data DataFrame
            
        Returns:
            pd.DataFrame: Cleaned data
        """
        logger.info("Cleaning market data")
        df = df.copy()
        
        # Remove rows with missing OHLC data
        ohlc_cols = ['open', 'high', 'low', 'close']
        initial_count = len(df)
        df = df.dropna(subset=ohlc_cols)
        
        if len(df) < initial_count:
            logger.warning(f"Removed {initial_count - len(df)} rows with missing OHLC data")
        
        # Validate OHLC relationships
        invalid_ohlc = (
            (df['high'] < df['low']) |
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close'])
        )
        
        if invalid_ohlc.any():
            logger.warning(f"Found {invalid_ohlc.sum()} rows with invalid OHLC data")
            df = df[~invalid_ohlc]
        
        # Handle negative volumes and open interest
        if 'volume' in df.columns:
            negative_volume = df['volume'] < 0
            if negative_volume.any():
                logger.warning(f"Found {negative_volume.sum()} negative volume values, setting to 0")
                df.loc[negative_volume, 'volume'] = 0
        
        if 'oi' in df.columns:
            negative_oi = df['oi'] < 0
            if negative_oi.any():
                logger.warning(f"Found {negative_oi.sum()} negative OI values, setting to 0")
                df.loc[negative_oi, 'oi'] = 0
        
        # Sort by datetime index
        df = df.sort_index()
        
        logger.info(f"Data cleaning completed. Final data points: {len(df)}")
        return df
    
    @staticmethod
    def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add common technical indicators to the data.
        
        Args:
            df: OHLCV data
            
        Returns:
            pd.DataFrame: Data with added technical indicators
        """
        logger.info("Adding technical indicators")
        df = df.copy()
        
        # Simple Moving Averages
        for period in [5, 10, 20, 50]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
        
        # Exponential Moving Averages
        for period in [12, 26]:
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Volume indicators
        if 'volume' in df.columns:
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        logger.info("Technical indicators added successfully")
        return df
    
    @staticmethod
    def add_oi_analysis(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add Open Interest analysis indicators.
        
        Args:
            df: Data with Open Interest column
            
        Returns:
            pd.DataFrame: Data with OI analysis indicators
        """
        if 'oi' not in df.columns:
            logger.warning("No Open Interest data found, skipping OI analysis")
            return df
        
        logger.info("Adding Open Interest analysis")
        df = df.copy()
        
        # Basic OI indicators
        df['oi_sma_10'] = df['oi'].rolling(window=10).mean()
        df['oi_sma_30'] = df['oi'].rolling(window=30).mean()
        df['oi_ratio'] = df['oi'] / df['oi_sma_30']
        
        # OI derivatives (matching SCLU strategy)
        df['oi_change'] = df['oi'].diff()
        df['oi_pct_change'] = df['oi'].pct_change()
        
        # First derivative (rate of change)
        df['oi_derivative'] = df['oi_change'] / 3  # 3-minute normalization
        
        # Second derivative (acceleration)
        df['oi_second_derivative'] = (
            df['oi'] + df['oi'].shift(2) - 2 * df['oi'].shift(1)
        ) / 9  # 3^2 normalization
        
        # OI momentum
        df['oi_momentum'] = df['oi'] - df['oi'].shift(4)
        
        # Price-OI divergence
        price_change = df['close'].pct_change()
        oi_change = df['oi'].pct_change()
        df['price_oi_divergence'] = price_change - oi_change
        
        logger.info("Open Interest analysis completed")
        return df
    
    @staticmethod
    def resample_data(
        df: pd.DataFrame,
        timeframe: str,
        agg_methods: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:
        """
        Resample data to a different timeframe.
        
        Args:
            df: Input data
            timeframe: Target timeframe (e.g., '5T', '15T', '1H')
            agg_methods: Custom aggregation methods for columns
            
        Returns:
            pd.DataFrame: Resampled data
        """
        logger.info(f"Resampling data to {timeframe} timeframe")
        
        # Default aggregation methods
        default_agg = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'oi': 'last'
        }
        
        if agg_methods:
            default_agg.update(agg_methods)
        
        # Only include columns that exist in the dataframe
        agg_dict = {col: method for col, method in default_agg.items() if col in df.columns}
        
        # Add mean aggregation for other columns
        for col in df.columns:
            if col not in agg_dict:
                agg_dict[col] = 'mean'
        
        resampled = df.resample(timeframe).agg(agg_dict)
        resampled = resampled.dropna()
        
        logger.info(f"Resampling completed. Data points: {len(resampled)}")
        return resampled
    
    @staticmethod
    def detect_market_sessions(df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect and mark market sessions in the data.
        
        Args:
            df: Market data with datetime index
            
        Returns:
            pd.DataFrame: Data with session markers
        """
        logger.info("Detecting market sessions")
        df = df.copy()
        
        # Extract time components
        df['hour'] = df.index.hour
        df['minute'] = df.index.minute
        df['time_minutes'] = df['hour'] * 60 + df['minute']
        
        # Define Indian market sessions (IST)
        # Pre-market: 9:00-9:15
        # Normal session: 9:15-15:30
        # Post-market: 15:40-16:00
        
        df['session'] = 'closed'
        df.loc[(df['time_minutes'] >= 540) & (df['time_minutes'] < 555), 'session'] = 'pre_market'
        df.loc[(df['time_minutes'] >= 555) & (df['time_minutes'] < 930), 'session'] = 'normal'
        df.loc[(df['time_minutes'] >= 940) & (df['time_minutes'] < 960), 'session'] = 'post_market'
        
        # Mark first and last bars of each session
        df['session_start'] = df['session'] != df['session'].shift(1)
        df['session_end'] = df['session'] != df['session'].shift(-1)
        
        # Calculate time since session start
        session_groups = df.groupby((df['session'] != df['session'].shift(1)).cumsum())
        df['minutes_in_session'] = session_groups.cumcount()
        
        logger.info("Market session detection completed")
        return df
    
    @staticmethod
    def calculate_performance_metrics(df: pd.DataFrame, returns_col: str = 'returns') -> Dict[str, float]:
        """
        Calculate performance metrics for returns data.
        
        Args:
            df: Data with returns column
            returns_col: Name of the returns column
            
        Returns:
            Dict[str, float]: Performance metrics
        """
        if returns_col not in df.columns:
            logger.error(f"Returns column '{returns_col}' not found")
            return {}
        
        returns = df[returns_col].dropna()
        
        if len(returns) == 0:
            logger.warning("No valid returns data found")
            return {}
        
        # Basic metrics
        total_return = (1 + returns).prod() - 1
        annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = returns.std() * np.sqrt(252)
        
        # Risk metrics
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Drawdown analysis
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Win/Loss analysis
        positive_returns = returns[returns > 0]
        negative_returns = returns[returns < 0]
        
        win_rate = len(positive_returns) / len(returns) if len(returns) > 0 else 0
        avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0
        avg_loss = negative_returns.mean() if len(negative_returns) > 0 else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        metrics = {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_trades': len(returns)
        }
        
        logger.info("Performance metrics calculated successfully")
        return metrics
