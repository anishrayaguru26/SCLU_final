# SCLU - Short Cover Long Unwind

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**SCLU** is a specialized algorithmic trading system for **naked option buying during short covering and long unwinding rallies** in the Indian stock market (NSE). The strategy capitalizes on forced exits of option sellers when their stop losses are hit, creating explosive price movements in options.

## Features

### Core Trading Strategy
- **Short Covering Detection**: Identifies forced seller exits during stop loss cascades
- **Open Interest Derivatives**: Uses precise mathematical formulas to detect OI acceleration patterns
- **Strategic Market Timing**: Optimized for 1-2 DTE options in low VIX environments
- **Strike Selection Logic**: Automated selection of ATM and OTM strikes for maximum delta exposure

### Backtesting & Analysis
- **Historical Backtesting**: Comprehensive backtesting framework using Backtrader
- **Performance Metrics**: Detailed analytics including Sharpe ratio, drawdown, win rate
- **Data Processing**: Advanced data cleaning and technical indicator calculation
- **Strategy Optimization**: Parameter optimization and sensitivity analysis

### Live Trading
- **Zerodha Kite Integration**: Direct integration with Zerodha Kite Connect API
- **Real-time Data**: Live market data processing and analysis
- **Automated Execution**: Hands-free trading with configurable safety limits
- **Monitoring & Logging**: Comprehensive logging and performance tracking

## Quick Start

### Prerequisites

- Python 3.8 or higher
- A Zerodha trading account with Kite Connect API access
- Historical market data (CSV format)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/SCLU.git
   cd SCLU
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration:**
   ```bash
   # Copy environment template
   cp config/env.example .env
   
   # Edit .env with your API credentials
   nano .env
   ```

4. **Configure your settings:**
   ```bash
   # Copy default configuration
   cp config/default.yaml config/local.yaml
   
   # Customize your trading parameters
   nano config/local.yaml
   ```

### Running a Backtest

```bash
# Run backtest with sample data
python scripts/run_backtest.py data/historical/sample_data.csv

# Run with custom parameters
python scripts/run_backtest.py data/historical/sample_data.csv \
    --cash 50000 \
    --sensitivity 0.008 \
    --feeling 3500000 \
    --plot
```

### Live Trading
```bash
# Run in dry-run mode (recommended)
python scripts/live_trading.py --dry-run --config config/local.yaml

# Live trading (use with caution)
python scripts/live_trading.py --config config/production.yaml
```

## Strategy Overview

The SCLU strategy targets **short covering and long unwinding rallies** where option sellers are forced to exit:

### Core Premise
*"Option sellers always win... until their stop losses are hit."*

When short covering or long unwinding occurs, sellers' stop losses create cascading exits, leading to explosive option price movements. Delta can exceed 1.0 during these events, especially near expiry.

### Signal Generation (Exact Formulas)

**Entry Signal (Buy)**:
```
1. First Derivative < 0 (OI decreasing)
AND
2. Second Derivative < -0.5% of 50-period OI Moving Average
```

**Exit Signal (Sell)**:
```
1. First Derivative > -0.1% of 50-period OI Moving Average
OR
2. Second Derivative > -0.5% of 50-period OI Moving Average
```

### Optimal Conditions
- **Market Environment**: Low VIX periods
- **Time to Expiry**: 1-2 DTE (not 0 DTE)
- **Strike Selection**: ATM and OTM options (ATM +1/+2/+3)
- **Side Selection**: Calls for short covering, Puts for long unwinding

### Risk Management

- **Position Sizing**: Configurable position size as percentage of portfolio
- **Stop Loss**: Automatic stop loss based on percentage or absolute amount
- **Take Profit**: Automatic take profit targets
- **Daily Limits**: Maximum number of trades per day
- **Emergency Stop**: Circuit breaker for large losses

## Architecture

```
SCLU/
├── src/sclu/                    # Main source code
│   ├── strategies/              # Trading strategies
│   ├── indicators/              # Custom indicators
│   ├── api/                     # API integrations
│   ├── data/                    # Data handling
│   └── utils/                   # Utilities
├── scripts/                     # Execution scripts
├── tests/                       # Test suites
├── config/                      # Configuration files
├── data/                        # Data storage
├── docs/                        # Documentation
└── examples/                    # Usage examples
```

### Key Components

- **Strategy Engine**: Core trading logic and signal generation
- **Data Pipeline**: Market data ingestion, cleaning, and processing
- **Execution Engine**: Order management and trade execution
- **Risk Manager**: Position sizing and risk controls
- **Configuration System**: Flexible configuration management
- **Monitoring System**: Logging, metrics, and alerting

## Performance & Backtesting

### Sample Performance Metrics

The strategy has been tested on historical NSE options data:

- **Time Period**: January 2024 - December 2024
- **Instruments**: FinNifty CE/PE options
- **Win Rate**: ~65-75% (varies by market conditions)
- **Sharpe Ratio**: 1.2-1.8 (depends on parameters)
- **Maximum Drawdown**: <15% (with proper risk management)

### Running Your Own Analysis

```bash
# Comprehensive backtest with multiple instruments
python scripts/run_backtest.py data/historical/ \
    --config config/backtest.yaml \
    --plot \
    --output results/backtest_results.json

# Parameter optimization
python scripts/optimize_strategy.py \
    --data-dir data/historical/ \
    --optimize sensitivity,feeling \
    --output results/optimization.csv
```

## Configuration

### Trading Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `sensitivity` | Signal sensitivity multiplier | 0.01 | 0.005-0.02 |
| `feeling` | Signal strength parameter | 3000000 | 1M-5M |
| `oi_ma_period` | OI moving average period | 30 | 20-50 |
| `stop_loss_pct` | Stop loss percentage | 0.05 | 0.02-0.10 |
| `max_daily_trades` | Maximum trades per day | 30 | 10-50 |

### Environment Variables

```bash
# Required
SCLU_API_KEY=your_kite_api_key
SCLU_ACCESS_TOKEN=your_access_token

# Optional
SCLU_ENVIRONMENT=development
SCLU_LOG_LEVEL=INFO
SCLU_DRY_RUN_MODE=true
```

## Testing

```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/

# Run all tests with coverage
python -m pytest tests/ --cov=src/sclu --cov-report=html
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linting
black src/ tests/
flake8 src/ tests/
mypy src/
```

## Support & Community

- **Documentation**: [Full Documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/SCLU/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/SCLU/discussions)

## Acknowledgments

- Built with [Backtrader](https://www.backtrader.com/) for backtesting
- Uses [Zerodha Kite Connect](https://kite.trade/) for live trading
- Inspired by quantitative trading research and options market analysis

---

**Made for the trading community**

*Remember: Past performance does not guarantee future results. Always do your own research and trade responsibly.*
