#!/usr/bin/env python3
"""
Basic SCLU Backtesting Example

This example demonstrates how to run a simple backtest using the SCLU strategy
with sample data. It shows the basic workflow and how to interpret results.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import backtrader as bt
import pandas as pd
from datetime import datetime, timedelta

from sclu.strategies import SCLUStrategy
from sclu.data import DataLoader, DataProcessor
from sclu.utils import Config, get_logger

# Set up logging
logger = get_logger(__name__)


def create_sample_data():
    """Create sample OHLCV+OI data for demonstration."""
    logger.info("Creating sample data for demonstration...")
    
    # Generate 30 days of 3-minute data
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    # Create 3-minute intervals
    dates = pd.date_range(start=start_date, end=end_date, freq='3T')
    
    # Filter for market hours (9:15 AM to 3:30 PM IST)
    dates = dates[
        (dates.hour >= 9) & 
        ((dates.hour < 15) | ((dates.hour == 15) & (dates.minute <= 30)))
    ]
    
    # Simulate realistic options data
    base_price = 50.0
    base_oi = 1000000
    
    data = []
    for i, date in enumerate(dates):
        # Simulate price movement with some trend and noise
        price_trend = 0.1 * (i / len(dates))  # Slight upward trend
        noise = (hash(str(date)) % 1000 - 500) / 10000  # Pseudo-random noise
        
        price = base_price + price_trend + noise
        
        # Create OHLC around the price
        spread = 0.5
        open_price = price + (hash(str(date) + "open") % 100 - 50) / 100
        high_price = max(open_price, price) + spread * abs(hash(str(date) + "high") % 100) / 100
        low_price = min(open_price, price) - spread * abs(hash(str(date) + "low") % 100) / 100
        close_price = price
        
        # Simulate volume and OI
        volume = 1000 + abs(hash(str(date) + "vol") % 5000)
        
        # Simulate OI with some patterns
        oi_trend = 50000 * (i / len(dates))  # Growing OI
        oi_noise = (hash(str(date) + "oi") % 20000 - 10000)
        oi = max(100000, base_oi + oi_trend + oi_noise)
        
        data.append({
            'datetime': date,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': int(volume),
            'oi': int(oi)
        })
    
    df = pd.DataFrame(data)
    df.set_index('datetime', inplace=True)
    
    logger.info(f"Created {len(df)} data points from {df.index.min()} to {df.index.max()}")
    return df


def run_basic_backtest():
    """Run a basic backtest with sample data."""
    logger.info("Starting basic SCLU backtest example...")
    
    # Create sample data
    data = create_sample_data()
    
    # Process the data
    processor = DataProcessor()
    data = processor.clean_data(data)
    data = processor.add_oi_analysis(data)
    
    # Create Backtrader data feed
    data_feed = bt.feeds.PandasData(
        dataname=data,
        datetime=None,  # Use index
        open='open',
        high='high', 
        low='low',
        close='close',
        volume='volume',
        openinterest='oi'
    )
    
    # Create cerebro instance
    cerebro = bt.Cerebro()
    
    # Add data with 3-minute compression (NSE OI refresh cycle)
    cerebro.resampledata(data_feed, timeframe=bt.TimeFrame.Minutes, compression=3)
    
    # Add strategy with custom parameters
    cerebro.addstrategy(
        SCLUStrategy,
        sensitivity=0.01,
        feeling=3000000,
        oi_ma_period=30,
        stop_loss_pct=0.05,
        take_profit_pct=0.10
    )
    
    # Set broker parameters
    initial_cash = 100000.0
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
    
    # Add analyzers for performance metrics
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.VWR, _name='vwr')  # Variability-Weighted Return
    
    # Print starting conditions
    starting_value = cerebro.broker.getvalue()
    logger.info(f'Starting Portfolio Value: ${starting_value:,.2f}')
    
    # Run the backtest
    results = cerebro.run()
    
    # Get final value
    final_value = cerebro.broker.getvalue()
    total_return = (final_value - starting_value) / starting_value
    
    # Extract strategy results
    strategy = results[0]
    
    # Print basic results
    print("\n" + "="*60)
    print("BASIC SCLU BACKTEST RESULTS")
    print("="*60)
    print(f"Starting Value:    ${starting_value:,.2f}")
    print(f"Final Value:       ${final_value:,.2f}")
    print(f"Total Return:      ${final_value - starting_value:,.2f}")
    print(f"Total Return %:    {total_return * 100:.2f}%")
    
    # Extract analyzer results
    try:
        sharpe_ratio = strategy.analyzers.sharpe.get_analysis().get('sharperatio', 0)
        drawdown_info = strategy.analyzers.drawdown.get_analysis()
        trade_info = strategy.analyzers.trades.get_analysis()
        
        print(f"Sharpe Ratio:      {sharpe_ratio:.3f}" if sharpe_ratio else "Sharpe Ratio:      N/A")
        print(f"Max Drawdown:      {drawdown_info.get('max', {}).get('drawdown', 0):.2f}%")
        
        total_trades = trade_info.get('total', {}).get('total', 0)
        won_trades = trade_info.get('won', {}).get('total', 0)
        lost_trades = trade_info.get('lost', {}).get('total', 0)
        
        print(f"Total Trades:      {total_trades}")
        print(f"Winning Trades:    {won_trades}")
        print(f"Losing Trades:     {lost_trades}")
        
        if total_trades > 0:
            win_rate = (won_trades / total_trades) * 100
            print(f"Win Rate:          {win_rate:.1f}%")
            
            if 'won' in trade_info and 'pnl' in trade_info['won']:
                avg_win = trade_info['won']['pnl']['average']
                print(f"Average Win:       ${avg_win:.2f}")
            
            if 'lost' in trade_info and 'pnl' in trade_info['lost']:
                avg_loss = trade_info['lost']['pnl']['average']
                print(f"Average Loss:      ${avg_loss:.2f}")
                
                if avg_loss != 0:
                    profit_factor = abs(avg_win / avg_loss) if 'avg_win' in locals() else 0
                    print(f"Profit Factor:     {profit_factor:.2f}")
    
    except Exception as e:
        logger.warning(f"Error extracting analyzer results: {e}")
    
    print("="*60)
    
    # Additional insights
    print("\nSTRATEGY INSIGHTS:")
    print("-" * 30)
    print("• This example uses simulated data for demonstration")
    print("• Real performance will vary with actual market data")
    print("• Always test with historical data before live trading")
    print("• Consider market conditions when interpreting results")
    print("• Use paper trading to validate strategy before going live")
    
    # Plot results (optional)
    try:
        print("\nGenerating plot...")
        cerebro.plot(style='candlestick', volume=False)
        print("Plot saved successfully!")
    except Exception as e:
        logger.warning(f"Could not generate plot: {e}")
        print("Note: Install matplotlib for plotting functionality")
    
    return {
        'starting_value': starting_value,
        'final_value': final_value,
        'total_return': total_return,
        'strategy_results': strategy
    }


def run_parameter_comparison():
    """Compare different parameter sets."""
    logger.info("Running parameter comparison...")
    
    # Different parameter sets to test
    parameter_sets = [
        {'sensitivity': 0.005, 'feeling': 2000000, 'name': 'Conservative'},
        {'sensitivity': 0.01, 'feeling': 3000000, 'name': 'Balanced'},
        {'sensitivity': 0.015, 'feeling': 4000000, 'name': 'Aggressive'},
    ]
    
    results = []
    data = create_sample_data()
    
    for params in parameter_sets:
        logger.info(f"Testing {params['name']} parameters...")
        
        # Create fresh cerebro for each test
        cerebro = bt.Cerebro()
        
        # Create data feed
        data_feed = bt.feeds.PandasData(
            dataname=data,
            datetime=None,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest='oi'
        )
        
        cerebro.resampledata(data_feed, timeframe=bt.TimeFrame.Minutes, compression=3)
        
        # Add strategy with specific parameters
        cerebro.addstrategy(
            SCLUStrategy,
            sensitivity=params['sensitivity'],
            feeling=params['feeling']
        )
        
        cerebro.broker.setcash(100000.0)
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        
        # Run backtest
        starting_value = cerebro.broker.getvalue()
        result = cerebro.run()
        final_value = cerebro.broker.getvalue()
        
        total_return = (final_value - starting_value) / starting_value
        
        results.append({
            'name': params['name'],
            'sensitivity': params['sensitivity'],
            'feeling': params['feeling'],
            'return': total_return,
            'final_value': final_value
        })
    
    # Print comparison
    print("\n" + "="*70)
    print("PARAMETER COMPARISON RESULTS")
    print("="*70)
    print(f"{'Strategy':<12} {'Sensitivity':<12} {'Feeling':<10} {'Return %':<10} {'Final Value':<12}")
    print("-" * 70)
    
    for result in results:
        print(f"{result['name']:<12} {result['sensitivity']:<12.3f} "
              f"{result['feeling']:<10,} {result['return']*100:<10.2f} "
              f"${result['final_value']:<12,.0f}")
    
    print("="*70)


if __name__ == "__main__":
    print("SCLU Basic Backtesting Example")
    print("==============================")
    print("This example demonstrates basic backtesting functionality.")
    print("It uses simulated data for demonstration purposes.\n")
    
    try:
        # Run basic backtest
        results = run_basic_backtest()
        
        # Run parameter comparison
        print("\n" + "="*60)
        print("RUNNING PARAMETER COMPARISON")
        print("="*60)
        run_parameter_comparison()
        
        print("\n" + "="*60)
        print("EXAMPLE COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("Next steps:")
        print("1. Replace sample data with real historical data")
        print("2. Optimize parameters using historical data")
        print("3. Test with paper trading before going live")
        print("4. Implement proper risk management")
        
    except Exception as e:
        logger.error(f"Error running backtest example: {e}")
        print(f"Error: {e}")
        print("Please check the logs for more details.")
