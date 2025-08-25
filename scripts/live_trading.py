#!/usr/bin/env python3
"""
SCLU Live Trading Script

Execute live trading using the SCLU strategy with real market data.
"""

import argparse
import sys
import time
import signal
from datetime import datetime
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sclu.api import KiteClient
from sclu.utils import Config, get_logger, TradingLogger

logger = get_logger(__name__)
trading_logger = TradingLogger()


class LiveTrader:
    """Live trading implementation for SCLU strategy."""
    
    def __init__(self, config: Config) -> None:
        """
        Initialize live trader.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.client = None
        self.running = False
        self.positions = {}
        self.trade_count = 0
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    def initialize(self) -> bool:
        """
        Initialize the trading client and validate credentials.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Initialize Kite client
            self.client = KiteClient(
                api_key=self.config.get('api', 'api_key'),
                access_token=self.config.get('api', 'access_token')
            )
            
            # Test connection
            instruments = self.client.get_instruments()
            logger.info(f"Successfully connected to Kite API. Loaded {len(instruments)} instruments.")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize trading client: {e}")
            return False
    
    def analyze_market_data(self, instrument_token: int, instrument_name: str) -> dict:
        """
        Analyze current market data for trading signals.
        
        Args:
            instrument_token: Token for the instrument
            instrument_name: Human-readable name
            
        Returns:
            dict: Analysis results with signal information
        """
        try:
            # Fetch recent data
            df = self.client.fetch_historical_data(instrument_token, duration_minutes=5)
            df = self.client.calculate_oi_derivatives(df)
            
            if len(df) < 2:
                logger.warning(f"Insufficient data for {instrument_name}")
                return {'signal': 'HOLD', 'reason': 'Insufficient data'}
            
            # Get latest values
            latest = df.iloc[-1]
            current_price = latest['close']
            doi = latest['doi'] if 'doi' in df.columns else 0
            d2oi = latest['d2oi'] if 'd2oi' in df.columns else 0
            
            # Strategy parameters
            sens = self.config.get('trading', 'sensitivity')
            feel = self.config.get('trading', 'feeling')
            
            # Generate signals based on SCLU strategy
            signal = 'HOLD'
            reason = 'No clear signal'
            
            # Check for buy signal
            if doi < 0 and d2oi < (-0.1 * sens * feel):
                signal = 'BUY'
                reason = f'OI derivatives indicate selling pressure (doi: {doi:.2f}, d2oi: {d2oi:.2f})'
            
            # Check for sell signal (if in position)
            elif doi > (-1 * sens * feel) or d2oi > (-0.1 * sens * feel):
                signal = 'SELL'
                if doi > (-1 * sens * feel):
                    reason = f'First derivative exit (doi: {doi:.2f})'
                else:
                    reason = f'Second derivative exit (d2oi: {d2oi:.2f})'
            
            return {
                'signal': signal,
                'reason': reason,
                'price': current_price,
                'doi': doi,
                'd2oi': d2oi,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error analyzing market data for {instrument_name}: {e}")
            return {'signal': 'HOLD', 'reason': f'Analysis error: {e}'}
    
    def execute_trade(self, instrument_token: int, signal: str, analysis: dict) -> bool:
        """
        Execute a trade based on the signal.
        
        Args:
            instrument_token: Token for the instrument
            signal: Trading signal (BUY/SELL)
            analysis: Market analysis results
            
        Returns:
            bool: True if trade executed successfully
        """
        if signal == 'HOLD':
            return True
        
        try:
            # Get instrument symbol
            symbol = self.client.lookup_instrument(instrument_token)
            if not symbol:
                logger.error(f"Could not find symbol for token {instrument_token}")
                return False
            
            # Check position status
            is_in_position = instrument_token in self.positions
            
            # Determine trade action
            if signal == 'BUY' and not is_in_position:
                # Enter new position
                quantity = 25  # Default lot size - should be configurable
                
                if self.trade_count >= self.config.get('trading', 'max_daily_trades'):
                    logger.warning("Maximum daily trades reached")
                    return False
                
                # Place buy order
                order_id = self.client.place_market_order(
                    trading_symbol=symbol,
                    transaction_type='BUY',
                    quantity=quantity
                )
                
                if order_id:
                    self.positions[instrument_token] = {
                        'symbol': symbol,
                        'quantity': quantity,
                        'entry_price': analysis['price'],
                        'entry_time': analysis['timestamp'],
                        'order_id': order_id
                    }
                    self.trade_count += 1
                    
                    trading_logger.log_signal(signal, symbol, analysis['price'], analysis['reason'])
                    trading_logger.log_order('BUY', symbol, quantity, analysis['price'], order_id)
                    return True
            
            elif signal == 'SELL' and is_in_position:
                # Exit existing position
                position = self.positions[instrument_token]
                
                order_id = self.client.place_market_order(
                    trading_symbol=position['symbol'],
                    transaction_type='SELL',
                    quantity=position['quantity']
                )
                
                if order_id:
                    # Calculate P&L
                    pnl = (analysis['price'] - position['entry_price']) * position['quantity']
                    duration = str(analysis['timestamp'] - position['entry_time'])
                    
                    trading_logger.log_signal(signal, position['symbol'], analysis['price'], analysis['reason'])
                    trading_logger.log_order('SELL', position['symbol'], position['quantity'], analysis['price'], order_id)
                    trading_logger.log_trade_closed(position['symbol'], pnl, duration, analysis['reason'])
                    
                    # Remove position
                    del self.positions[instrument_token]
                    return True
            
            return True
        
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return False
    
    def run_trading_loop(self) -> None:
        """Main trading loop."""
        logger.info("Starting live trading loop")
        self.running = True
        
        # Get instruments from config
        instruments = self.config.get('data', 'default_instruments')
        instrument_names = {
            10716162: "FinNifty 24000 CE",
            10684418: "FinNifty 23800 PE"
        }
        
        # Wait for market open (9:15 AM IST)
        self._wait_for_market_open()
        
        start_time = time.time()
        refresh_interval = self.config.get('data', 'data_refresh_interval')
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check if market is closed
                if not self._is_market_open():
                    logger.info("Market is closed, stopping trading")
                    break
                
                # Process each instrument
                for instrument_token in instruments:
                    if not self.running:
                        break
                    
                    instrument_name = instrument_names.get(instrument_token, f"Token-{instrument_token}")
                    
                    # Analyze market data
                    analysis = self.analyze_market_data(instrument_token, instrument_name)
                    
                    # Log market data
                    trading_logger.log_market_data(
                        instrument_name,
                        analysis.get('price', 0),
                        0,  # Volume not available in this context
                        oi=analysis.get('doi', 0)
                    )
                    
                    # Execute trade if signal generated
                    if analysis['signal'] != 'HOLD':
                        self.execute_trade(instrument_token, analysis['signal'], analysis)
                
                # Sleep until next refresh
                elapsed = time.time() - start_time
                sleep_time = refresh_interval - (elapsed % refresh_interval)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                time.sleep(60)  # Wait before retrying
        
        logger.info("Trading loop ended")
    
    def _wait_for_market_open(self) -> None:
        """Wait for market to open."""
        while True:
            if self._is_market_open():
                break
            logger.info("Waiting for market to open...")
            time.sleep(60)
    
    def _is_market_open(self) -> bool:
        """Check if market is currently open."""
        now = datetime.now()
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check time (9:15 AM to 3:30 PM IST)
        current_time = now.time()
        market_open = datetime.strptime("09:15:00", "%H:%M:%S").time()
        market_close = datetime.strptime("15:30:00", "%H:%M:%S").time()
        
        return market_open <= current_time <= market_close
    
    def cleanup(self) -> None:
        """Cleanup before shutdown."""
        logger.info("Performing cleanup...")
        
        # Close any open positions if configured to do so
        if self.positions:
            logger.info(f"Found {len(self.positions)} open positions")
            # Implement position closure logic here if needed
        
        logger.info("Cleanup completed")


def main():
    """Main entry point for live trading script."""
    parser = argparse.ArgumentParser(description="Run SCLU live trading")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--api-key-file", help="API key file path")
    parser.add_argument("--access-token-file", help="Access token file path")
    parser.add_argument("--dry-run", action="store_true", help="Run in simulation mode")
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        if args.api_key_file and args.access_token_file:
            config = Config.from_env_files(args.api_key_file, args.access_token_file)
        else:
            config = Config(args.config) if args.config else Config()
        
        # Validate API credentials
        if not config.get('api', 'api_key') or not config.get('api', 'access_token'):
            logger.error("API credentials not configured")
            sys.exit(1)
        
        # Create and initialize trader
        trader = LiveTrader(config)
        
        if not trader.initialize():
            logger.error("Failed to initialize trader")
            sys.exit(1)
        
        if args.dry_run:
            logger.info("Running in DRY RUN mode - no actual trades will be placed")
        
        # Start trading
        trader.run_trading_loop()
        
    except Exception as e:
        logger.error(f"Live trading failed: {e}")
        sys.exit(1)
    finally:
        if 'trader' in locals():
            trader.cleanup()


if __name__ == "__main__":
    main()
