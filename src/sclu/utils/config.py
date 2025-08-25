"""
Configuration management for SCLU trading system.

This module handles loading and managing configuration settings
from files and environment variables.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class TradingConfig:
    """Configuration settings for trading operations."""
    
    # Strategy parameters
    sensitivity: float = 10/1000
    feeling: int = 3000000
    oi_ma_period: int = 30
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.10
    max_positions: int = 1
    
    # Risk management
    max_daily_trades: int = 30
    max_portfolio_risk: float = 0.02
    position_size_pct: float = 0.1
    
    # Timing
    trading_start_time: str = "09:15:00"
    trading_end_time: str = "15:30:00"
    data_refresh_interval: int = 180  # seconds


@dataclass
class APIConfig:
    """Configuration for API connections."""
    
    # Kite Connect settings
    api_key: str = ""
    access_token: str = ""
    request_token: str = ""
    
    # Rate limiting
    requests_per_second: int = 10
    requests_per_minute: int = 300
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class DataConfig:
    """Configuration for data handling."""
    
    # Directories
    data_directory: str = "data"
    historical_data_dir: str = "data/historical"
    live_data_dir: str = "data/live"
    
    # File formats
    datetime_format: str = "%Y-%m-%d %H:%M:%S+05:30"
    csv_delimiter: str = ","
    
    # Data processing
    default_timeframe: str = "3T"  # 3 minutes
    max_lookback_days: int = 30
    
    # Instruments
    default_instruments: list = field(default_factory=lambda: [10716162, 10684418])


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/sclu.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_output: bool = True


@dataclass
class SCLUConfig:
    """Main configuration class for SCLU system."""
    
    trading: TradingConfig = field(default_factory=TradingConfig)
    api: APIConfig = field(default_factory=APIConfig)
    data: DataConfig = field(default_factory=DataConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Environment
    environment: str = "development"  # development, staging, production
    debug: bool = True


class Config:
    """
    Configuration manager for SCLU trading system.
    
    Handles loading configuration from files, environment variables,
    and provides default values.
    """
    
    def __init__(self, config_file: Optional[str] = None) -> None:
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (JSON or YAML)
        """
        self.config_file = config_file
        self._config: Optional[SCLUConfig] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file and environment variables."""
        # Start with default configuration
        self._config = SCLUConfig()
        
        # Load from file if specified
        if self.config_file and os.path.exists(self.config_file):
            self._load_from_file(self.config_file)
        
        # Override with environment variables
        self._load_from_env()
        
        logger.info("Configuration loaded successfully")
    
    def _load_from_file(self, file_path: str) -> None:
        """Load configuration from JSON or YAML file."""
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            self._update_config_from_dict(data)
            logger.info(f"Configuration loaded from {file_path}")
        
        except Exception as e:
            logger.error(f"Error loading config from {file_path}: {e}")
            raise
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            # API configuration
            'SCLU_API_KEY': ('api', 'api_key'),
            'SCLU_ACCESS_TOKEN': ('api', 'access_token'),
            'SCLU_REQUEST_TOKEN': ('api', 'request_token'),
            
            # Trading configuration
            'SCLU_SENSITIVITY': ('trading', 'sensitivity'),
            'SCLU_FEELING': ('trading', 'feeling'),
            'SCLU_MAX_DAILY_TRADES': ('trading', 'max_daily_trades'),
            'SCLU_STOP_LOSS_PCT': ('trading', 'stop_loss_pct'),
            'SCLU_TAKE_PROFIT_PCT': ('trading', 'take_profit_pct'),
            
            # Data configuration
            'SCLU_DATA_DIRECTORY': ('data', 'data_directory'),
            'SCLU_DATETIME_FORMAT': ('data', 'datetime_format'),
            
            # General
            'SCLU_ENVIRONMENT': ('environment',),
            'SCLU_DEBUG': ('debug',),
            'SCLU_LOG_LEVEL': ('logging', 'level'),
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_config(config_path, value)
    
    def _set_nested_config(self, path: tuple, value: str) -> None:
        """Set a nested configuration value."""
        try:
            current = self._config
            
            # Navigate to the correct nested object
            for key in path[:-1]:
                current = getattr(current, key)
            
            # Set the final value with type conversion
            final_key = path[-1]
            current_value = getattr(current, final_key)
            
            # Convert string value to appropriate type
            if isinstance(current_value, bool):
                value = value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(current_value, int):
                value = int(value)
            elif isinstance(current_value, float):
                value = float(value)
            
            setattr(current, final_key, value)
            logger.debug(f"Set config {'.'.join(path)} = {value}")
        
        except Exception as e:
            logger.warning(f"Could not set config {'.'.join(path)}: {e}")
    
    def _update_config_from_dict(self, data: Dict[str, Any]) -> None:
        """Update configuration from a dictionary."""
        for section, values in data.items():
            if hasattr(self._config, section) and isinstance(values, dict):
                section_obj = getattr(self._config, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)
    
    def get(self, section: str, key: Optional[str] = None) -> Any:
        """
        Get configuration value.
        
        Args:
            section: Configuration section name
            key: Optional key within section
            
        Returns:
            Configuration value or section object
        """
        if not hasattr(self._config, section):
            raise ValueError(f"Unknown configuration section: {section}")
        
        section_obj = getattr(self._config, section)
        
        if key is None:
            return section_obj
        
        if not hasattr(section_obj, key):
            raise ValueError(f"Unknown configuration key: {section}.{key}")
        
        return getattr(section_obj, key)
    
    def save_to_file(self, file_path: str) -> None:
        """
        Save current configuration to a file.
        
        Args:
            file_path: Path to save configuration file
        """
        try:
            config_dict = {
                'trading': self._config.trading.__dict__,
                'api': self._config.api.__dict__,
                'data': self._config.data.__dict__,
                'logging': self._config.logging.__dict__,
                'environment': self._config.environment,
                'debug': self._config.debug
            }
            
            with open(file_path, 'w') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    yaml.dump(config_dict, f, default_flow_style=False)
                else:
                    json.dump(config_dict, f, indent=2)
            
            logger.info(f"Configuration saved to {file_path}")
        
        except Exception as e:
            logger.error(f"Error saving config to {file_path}: {e}")
            raise
    
    @property
    def config(self) -> SCLUConfig:
        """Get the current configuration object."""
        return self._config
    
    @classmethod
    def from_env_files(cls, api_key_file: str, access_token_file: str) -> 'Config':
        """
        Create configuration instance from API credential files.
        
        Args:
            api_key_file: Path to API key file
            access_token_file: Path to access token file
            
        Returns:
            Config: Configured instance
        """
        config = cls()
        
        try:
            # Load API key
            with open(api_key_file, 'r') as f:
                api_key = f.read().strip().split()[0]
            config._config.api.api_key = api_key
            
            # Load access token
            with open(access_token_file, 'r') as f:
                access_token = f.read().strip()
            config._config.api.access_token = access_token
            
            logger.info("API credentials loaded from files")
        
        except Exception as e:
            logger.error(f"Error loading API credentials: {e}")
            raise
        
        return config
