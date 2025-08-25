"""
Kite Connect API Client for SCLU Trading System.

This module provides a wrapper around the Zerodha Kite Connect API
for live trading functionality.
"""

import os
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from kiteconnect import KiteConnect

from ..utils.logger import get_logger

logger = get_logger(__name__)


class KiteClient:
    """
    Wrapper class for Kite Connect API operations.
    
    This class handles all interactions with the Zerodha Kite Connect API
    including authentication, data fetching, and order placement.
    
    Attributes:
        api_key (str): Kite Connect API key
        access_token (str): Valid access token for API calls
        kite (KiteConnect): Kite Connect client instance
    """
    
    def __init__(self, api_key: str, access_token: str) -> None:
        """
        Initialize the Kite client.
        
        Args:
            api_key: Kite Connect API key
            access_token: Valid access token
        """
        self.api_key = api_key
        self.access_token = access_token
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        self._instrument_df: Optional[pd.DataFrame] = None
        
        logger.info("Kite client initialized successfully")
    
    @classmethod
    def from_config_files(cls, api_key_file: str, access_token_file: str) -> 'KiteClient':
        """
        Create KiteClient instance from configuration files.
        
        Args:
            api_key_file: Path to file containing API key
            access_token_file: Path to file containing access token
            
        Returns:
            KiteClient: Configured client instance
            
        Raises:
            FileNotFoundError: If config files don't exist
            ValueError: If config files are empty or invalid
        """
        try:
            with open(api_key_file, 'r') as f:
                api_key = f.read().strip().split()[0]
            
            with open(access_token_file, 'r') as f:
                access_token = f.read().strip()
            
            if not api_key or not access_token:
                raise ValueError("API key or access token is empty")
            
            return cls(api_key, access_token)
        
        except FileNotFoundError as e:
            logger.error(f"Configuration file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading configuration files: {e}")
            raise
    
    def get_instruments(self, exchange: str = "NFO") -> pd.DataFrame:
        """
        Fetch and cache instrument data.
        
        Args:
            exchange: Exchange name (default: "NFO" for derivatives)
            
        Returns:
            pd.DataFrame: Instrument data with columns including instrument_token,
                         tradingsymbol, name, etc.
        """
        try:
            if self._instrument_df is None:
                logger.info(f"Fetching instruments for exchange: {exchange}")
                instruments = self.kite.instruments(exchange)
                self._instrument_df = pd.DataFrame(instruments)
                logger.info(f"Loaded {len(self._instrument_df)} instruments")
            
            return self._instrument_df
        
        except Exception as e:
            logger.error(f"Error fetching instruments: {e}")
            raise
    
    def lookup_instrument(self, token: int) -> Optional[str]:
        """
        Look up trading symbol for an instrument token.
        
        Args:
            token: Instrument token to look up
            
        Returns:
            Optional[str]: Trading symbol if found, None otherwise
        """
        try:
            df = self.get_instruments()
            result = df[df.instrument_token == token].tradingsymbol.values
            
            if len(result) > 0:
                return result[0]
            else:
                logger.warning(f"Instrument token {token} not found")
                return None
        
        except Exception as e:
            logger.error(f"Error looking up instrument {token}: {e}")
            return None
    
    def fetch_historical_data(
        self,
        instrument_token: int,
        duration_minutes: int,
        interval: str = "3minute",
        include_oi: bool = True
    ) -> pd.DataFrame:
        """
        Fetch historical OHLC data with open interest.
        
        Args:
            instrument_token: Token for the instrument
            duration_minutes: How many minutes of history to fetch
            interval: Data interval (default: "3minute")
            include_oi: Whether to include open interest data
            
        Returns:
            pd.DataFrame: Historical data with datetime index
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=3 * duration_minutes)
            
            logger.debug(
                f"Fetching historical data for {instrument_token} "
                f"from {start_time} to {end_time}"
            )
            
            data = self.kite.historical_data(
                instrument_token,
                start_time,
                end_time,
                interval,
                oi=include_oi
            )
            
            df = pd.DataFrame(data)
            df.set_index("date", inplace=True)
            
            logger.debug(f"Fetched {len(df)} data points")
            return df
        
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise
    
    def calculate_oi_derivatives(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Open Interest derivatives for the given DataFrame.
        
        Args:
            df: DataFrame with OHLC and OI data
            
        Returns:
            pd.DataFrame: DataFrame with added 'doi' and 'd2oi' columns
        """
        df = df.copy()
        df['doi'] = None
        df['d2oi'] = None
        
        # Calculate first derivative (rate of change)
        for i in range(1, len(df)):
            df.iloc[i, df.columns.get_loc('doi')] = round(
                (df.iloc[i, df.columns.get_loc('oi')] - 
                 df.iloc[i-1, df.columns.get_loc('oi')]) / 3
            )
        
        # Calculate second derivative (acceleration)
        for i in range(2, len(df)):
            df.iloc[i, df.columns.get_loc('d2oi')] = round(
                (df.iloc[i, df.columns.get_loc('oi')] + 
                 df.iloc[i-2, df.columns.get_loc('oi')] - 
                 2 * df.iloc[i-1, df.columns.get_loc('oi')]) / 9
            )
        
        return df
    
    def place_market_order(
        self,
        trading_symbol: str,
        transaction_type: str,
        quantity: int,
        exchange: str = "NFO",
        product: str = "MIS"
    ) -> Optional[str]:
        """
        Place a market order.
        
        Args:
            trading_symbol: Symbol to trade
            transaction_type: "BUY" or "SELL"
            quantity: Number of shares/contracts
            exchange: Exchange (default: "NFO")
            product: Product type (default: "MIS" for intraday)
            
        Returns:
            Optional[str]: Order ID if successful, None otherwise
        """
        try:
            logger.info(
                f"Placing {transaction_type} order for {quantity} "
                f"of {trading_symbol}"
            )
            
            order_id = self.kite.place_order(
                tradingsymbol=trading_symbol,
                exchange=exchange,
                transaction_type=transaction_type,
                quantity=quantity,
                order_type=self.kite.ORDER_TYPE_MARKET,
                product=product,
                variety=self.kite.VARIETY_REGULAR
            )
            
            logger.info(f"Order placed successfully. Order ID: {order_id}")
            return order_id
        
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions.
        
        Returns:
            List[Dict]: List of position dictionaries
        """
        try:
            positions = self.kite.positions()
            return positions.get('net', []) + positions.get('day', [])
        
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []
    
    def get_orders(self) -> List[Dict[str, Any]]:
        """
        Get order history.
        
        Returns:
            List[Dict]: List of order dictionaries
        """
        try:
            return self.kite.orders()
        
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return []
    
    def get_holdings(self) -> List[Dict[str, Any]]:
        """
        Get current holdings.
        
        Returns:
            List[Dict]: List of holding dictionaries
        """
        try:
            return self.kite.holdings()
        
        except Exception as e:
            logger.error(f"Error fetching holdings: {e}")
            return []
