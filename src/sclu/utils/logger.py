"""
Logging utilities for SCLU trading system.

This module provides centralized logging configuration and utilities.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True,
    format_string: Optional[str] = None
) -> None:
    """
    Set up logging configuration for the SCLU system.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        console_output: Whether to output logs to console
        format_string: Custom format string for log messages
    """
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Default format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


class TradingLogger:
    """
    Specialized logger for trading operations.
    
    Provides methods for logging trading-specific events with
    consistent formatting and context.
    """
    
    def __init__(self, name: str = "trading") -> None:
        """
        Initialize trading logger.
        
        Args:
            name: Logger name
        """
        self.logger = get_logger(name)
        self.trade_count = 0
    
    def log_signal(self, signal_type: str, symbol: str, price: float, reason: str) -> None:
        """
        Log a trading signal.
        
        Args:
            signal_type: Type of signal (BUY, SELL, HOLD)
            symbol: Trading symbol
            price: Current price
            reason: Reason for the signal
        """
        self.logger.info(
            f"SIGNAL | {signal_type} | {symbol} | Price: {price:.2f} | Reason: {reason}"
        )
    
    def log_order(self, order_type: str, symbol: str, quantity: int, price: float, order_id: str) -> None:
        """
        Log an order placement.
        
        Args:
            order_type: Type of order (BUY, SELL)
            symbol: Trading symbol
            quantity: Order quantity
            price: Order price
            order_id: Order ID from broker
        """
        self.logger.info(
            f"ORDER | {order_type} | {symbol} | Qty: {quantity} | Price: {price:.2f} | ID: {order_id}"
        )
    
    def log_execution(self, symbol: str, quantity: int, price: float, commission: float) -> None:
        """
        Log an order execution.
        
        Args:
            symbol: Trading symbol
            quantity: Executed quantity
            price: Execution price
            commission: Commission paid
        """
        self.logger.info(
            f"EXECUTION | {symbol} | Qty: {quantity} | Price: {price:.2f} | Commission: {commission:.2f}"
        )
    
    def log_trade_closed(self, symbol: str, pnl: float, duration: str, reason: str) -> None:
        """
        Log a completed trade.
        
        Args:
            symbol: Trading symbol
            pnl: Profit/Loss amount
            duration: Trade duration
            reason: Reason for closing
        """
        self.trade_count += 1
        status = "PROFIT" if pnl > 0 else "LOSS"
        
        self.logger.info(
            f"TRADE CLOSED | {symbol} | {status}: {pnl:.2f} | Duration: {duration} | "
            f"Reason: {reason} | Trade #{self.trade_count}"
        )
    
    def log_portfolio_status(self, total_value: float, cash: float, positions: int) -> None:
        """
        Log portfolio status.
        
        Args:
            total_value: Total portfolio value
            cash: Available cash
            positions: Number of open positions
        """
        self.logger.info(
            f"PORTFOLIO | Total: {total_value:.2f} | Cash: {cash:.2f} | Positions: {positions}"
        )
    
    def log_error(self, error_type: str, message: str, symbol: str = None) -> None:
        """
        Log a trading error.
        
        Args:
            error_type: Type of error
            message: Error message
            symbol: Related trading symbol (optional)
        """
        symbol_part = f" | {symbol}" if symbol else ""
        self.logger.error(f"ERROR | {error_type} | {message}{symbol_part}")
    
    def log_market_data(self, symbol: str, price: float, volume: int, oi: int = None) -> None:
        """
        Log market data update.
        
        Args:
            symbol: Trading symbol
            price: Current price
            volume: Volume
            oi: Open Interest (optional)
        """
        oi_part = f" | OI: {oi}" if oi is not None else ""
        self.logger.debug(
            f"MARKET DATA | {symbol} | Price: {price:.2f} | Volume: {volume}{oi_part}"
        )


# Initialize default logging if not already configured
if not logging.getLogger().handlers:
    setup_logging(
        level=os.getenv("SCLU_LOG_LEVEL", "INFO"),
        log_file=os.getenv("SCLU_LOG_FILE"),
        console_output=True
    )
