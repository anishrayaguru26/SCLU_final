# Legacy Files

This directory contains the original SCLU codebase before refactoring. These files are preserved for reference and historical purposes.

## Original Structure

The original codebase had the following structure:
- `SCLUv1.py` - Original strategy implementation
- `SCLU_backtest.py` - Original backtesting script  
- `SCLUlivev1.py` - Original live trading implementation
- `mayankdls/` - API connection utilities
- `datadumps/` and `datadumps2/` - Historical market data
- `crapfiles/` - Test and experimental files

## Migration Notes

The original code has been refactored into the new production-ready structure:

### Key Changes Made:

1. **Strategy Code**: `SCLUv1.py` → `src/sclu/strategies/sclu_strategy.py`
   - Added proper type hints and docstrings
   - Implemented better error handling
   - Added configurable parameters
   - Improved logging

2. **Indicators**: Custom indicators extracted to `src/sclu/indicators/open_interest.py`
   - `OI` class → `OpenInterestIndicator`
   - `dOI` class → `OpenInterestDerivative` 
   - `d2OI` class → `OpenInterestSecondDerivative`

3. **API Integration**: `mayankdls/` → `src/sclu/api/kite_client.py`
   - Improved error handling and retry logic
   - Better credential management
   - More comprehensive API coverage

4. **Data Handling**: New data processing pipeline in `src/sclu/data/`
   - `DataLoader` for flexible data loading
   - `DataProcessor` for data cleaning and analysis

5. **Configuration**: Hardcoded values moved to YAML configuration files
   - `config/default.yaml` for development
   - `config/production.yaml` for production
   - Environment variable support

6. **Testing**: Comprehensive test suite added
   - Unit tests for all components
   - Integration tests for workflows
   - Automated CI/CD pipeline

## Historical Data

The `datadumps/` and `datadumps2/` directories contain historical options data:
- NSE options data (Nifty, Bank Nifty, FinNifty, Sensex)
- OHLCV+OI format
- Various expiry dates and strike prices
- Time period: 2024

This data has been moved to `data/historical/` in the new structure.

## API Credentials

⚠️ **Security Note**: The original files contained API credentials in plain text files:
- `api_key.txt`
- `access_token.txt` 
- `request_token.txt`

These are now managed through:
- Environment variables (recommended)
- Secure configuration files (not checked into git)
- `.env` files (gitignored)

## Usage with Legacy Code

If you need to use the original code:

```bash
cd legacy/
python SCLUv1.py  # For backtesting
python SCLUlivev1.py  # For live trading (update credentials first)
```

**Note**: The legacy code may have hardcoded paths and require manual configuration.

## Recommended Migration Path

Instead of using legacy code, use the new production-ready version:

```bash
# Backtesting
python scripts/run_backtest.py data/historical/your_data.csv

# Live trading (paper mode)
python scripts/live_trading.py --dry-run

# Configuration
cp config/default.yaml config/local.yaml
# Edit local.yaml with your settings
```

## Support

For questions about the migration or legacy code, please:
1. Check the main README.md
2. Review the CONTRIBUTING.md guidelines
3. Open an issue on GitHub

---

*This legacy code is preserved for reference only. All new development should use the refactored codebase.*
