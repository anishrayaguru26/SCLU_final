#!/usr/bin/env python3
"""
SCLU Strategy Example - Short Covering Rally Detection

This example demonstrates the SCLU strategy specifically designed for
naked option buying during short covering and long unwinding rallies.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from sclu.strategies import SCLUStrategy
from sclu.data import DataLoader, DataProcessor
from sclu.utils import Config, get_logger

# Set up logging
logger = get_logger(__name__)


def create_short_covering_scenario():
    """
    Create realistic data simulating a short covering event.
    Based on the Nifty 25000 CE September 12th example from the strategy document.
    """
    logger.info("Creating short covering scenario data...")
    
    # Generate data for expiry day (1 DTE scenario)
    start_time = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)
    end_time = start_time.replace(hour=15, minute=30)
    
    # Create 3-minute intervals (NSE OI refresh cycle)
    dates = pd.date_range(start=start_time, end=end_time, freq='3T')
    
    # Simulate option data for short covering scenario
    base_price = 15.0  # Starting option price
    base_oi = 2500000  # Starting OI (25 lakh)
    
    data = []
    
    for i, date in enumerate(dates):
        # Create different phases of the trading day
        total_points = len(dates)
        
        if i < total_points * 0.7:  # First 70% - normal trading
            # Gradual price decline with stable OI
            price_trend = -2 * (i / (total_points * 0.7))
            oi_trend = -50000 * (i / (total_points * 0.7))  # Gradual OI decline
            volatility = 0.5
            
        else:  # Last 30% - short covering event
            # Explosive price movement with sharp OI decline
            rally_progress = (i - total_points * 0.7) / (total_points * 0.3)
            
            # Exponential price increase
            price_trend = -1.4 + 25 * (rally_progress ** 2)
            
            # Sharp OI decline (forced seller exits)
            oi_decline = -300000 * rally_progress  # Sharp decline
            oi_trend = -50000 + oi_decline
            
            volatility = 2.0  # Higher volatility during rally
        
        # Add realistic noise
        price_noise = np.random.normal(0, volatility)
        price = max(0.5, base_price + price_trend + price_noise)
        
        # Create OHLC around the price
        spread = volatility * 0.3
        open_price = max(0.5, price + np.random.normal(0, spread/4))
        high_price = max(open_price, price) + abs(np.random.normal(0, spread/2))
        low_price = max(0.5, min(open_price, price) - abs(np.random.normal(0, spread/2)))
        close_price = price
        
        # Volume increases during short covering
        volume_multiplier = 1.0 if i < total_points * 0.7 else (1 + 3 * rally_progress)
        volume = int(15000 * volume_multiplier * (1 + np.random.normal(0, 0.3)))
        
        # Open Interest with noise
        oi_noise = np.random.normal(0, 20000)
        oi = max(100000, base_oi + oi_trend + oi_noise)
        
        data.append({
            'datetime': date,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume,
            'oi': int(oi)
        })
    
    df = pd.DataFrame(data)
    df.set_index('datetime', inplace=True)
    
    logger.info(f"Created short covering scenario with {len(df)} data points")
    logger.info(f"Price range: {df['close'].min():.2f} to {df['close'].max():.2f}")
    logger.info(f"OI range: {df['oi'].min():,} to {df['oi'].max():,}")
    
    return df


def run_sclu_strategy_example():
    """Run the SCLU strategy on a short covering scenario."""
    logger.info("Running SCLU Strategy Example...")
    
    # Create scenario data
    data = create_short_covering_scenario()
    
    # Process the data
    processor = DataProcessor()
    data = processor.clean_data(data)
    data = processor.add_oi_analysis(data)
    
    # Create Backtrader data feed
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
    
    # Create cerebro instance
    cerebro = bt.Cerebro()
    
    # Add data (no resampling since we already have 3-minute data)
    cerebro.adddata(data_feed)
    
    # Add SCLU strategy with documented parameters
    cerebro.addstrategy(
        SCLUStrategy,
        oi_ma_period=50,
        entry_threshold_pct=0.005,     # 0.5% of OI MA
        exit_doi_threshold_pct=0.001,  # 0.1% of OI MA  
        exit_d2oi_threshold_pct=0.005, # 0.5% of OI MA
        stop_loss_pct=0.15,            # 15% stop loss
        take_profit_pct=0.30           # 30% take profit
    )
    
    # Set broker parameters for options trading
    initial_cash = 50000.0  # Smaller amount for option buying
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=0.002)  # 0.2% commission for options
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    # Print starting conditions
    starting_value = cerebro.broker.getvalue()
    print("\n" + "="*70)
    print("SCLU STRATEGY EXAMPLE - SHORT COVERING RALLY")
    print("="*70)
    print(f"Strategy: Naked Option Buying during Short Covering")
    print(f"Scenario: Simulated Nifty 25000 CE expiry day rally")
    print(f"Starting Portfolio Value: ₹{starting_value:,.2f}")
    print(f"Data Points: {len(data)} (3-minute intervals)")
    print("="*70)
    
    # Run the backtest
    results = cerebro.run()
    
    # Get final value
    final_value = cerebro.broker.getvalue()
    total_return = (final_value - starting_value) / starting_value
    
    # Extract results
    strategy = results[0]
    
    print("\nSTRATEGY EXECUTION RESULTS")
    print("-" * 40)
    print(f"Final Portfolio Value: ₹{final_value:,.2f}")
    print(f"Total Return: ₹{final_value - starting_value:,.2f}")
    print(f"Total Return %: {total_return * 100:.2f}%")
    
    # Analyze trades
    try:
        trade_analysis = strategy.analyzers.trades.get_analysis()
        
        total_trades = trade_analysis.get('total', {}).get('total', 0)
        won_trades = trade_analysis.get('won', {}).get('total', 0)
        lost_trades = trade_analysis.get('lost', {}).get('total', 0)
        
        print(f"\nTRADE ANALYSIS")
        print(f"Total Trades: {total_trades}")
        print(f"Winning Trades: {won_trades}")
        print(f"Losing Trades: {lost_trades}")
        
        if total_trades > 0:
            win_rate = (won_trades / total_trades) * 100
            print(f"Win Rate: {win_rate:.1f}%")
            
            if 'won' in trade_analysis and won_trades > 0:
                avg_win = trade_analysis['won']['pnl']['average']
                max_win = trade_analysis['won']['pnl']['max']
                print(f"Average Win: ₹{avg_win:.2f}")
                print(f"Maximum Win: ₹{max_win:.2f}")
            
            if 'lost' in trade_analysis and lost_trades > 0:
                avg_loss = trade_analysis['lost']['pnl']['average']
                max_loss = trade_analysis['lost']['pnl']['max']
                print(f"Average Loss: ₹{avg_loss:.2f}")
                print(f"Maximum Loss: ₹{max_loss:.2f}")
        
        # Drawdown analysis
        drawdown_analysis = strategy.analyzers.drawdown.get_analysis()
        max_drawdown = drawdown_analysis.get('max', {}).get('drawdown', 0)
        print(f"Maximum Drawdown: {max_drawdown:.2f}%")
        
    except Exception as e:
        logger.warning(f"Error extracting trade analysis: {e}")
    
    print("\n" + "="*70)
    print("STRATEGY INSIGHTS")
    print("="*70)
    print("📊 This example demonstrates the SCLU strategy's ability to detect")
    print("   and capitalize on short covering rallies in options.")
    print()
    print("🎯 Key Strategy Features:")
    print("   • Detects forced seller exits using OI derivatives")
    print("   • Optimized for 1-2 DTE options (not 0 DTE)")
    print("   • Works best in low VIX environments")
    print("   • Focuses on ATM and OTM strikes")
    print()
    print("📈 Signal Generation:")
    print("   • Entry: DOI < 0 AND D2OI < -0.5% of 50-period OI MA")
    print("   • Exit: DOI > -0.1% of OI MA OR D2OI > -0.5% of OI MA")
    print()
    print("⚠️  Real Trading Considerations:")
    print("   • Use real historical data for validation")
    print("   • Test in paper trading mode first")
    print("   • Monitor VIX levels before trading")
    print("   • Consider transaction costs and slippage")
    print("="*70)
    
    return {
        'starting_value': starting_value,
        'final_value': final_value,
        'total_return': total_return,
        'strategy_results': strategy,
        'data': data
    }


def analyze_oi_derivatives(data):
    """Analyze the Open Interest derivatives in detail."""
    print("\n" + "="*70)
    print("OPEN INTEREST DERIVATIVE ANALYSIS")
    print("="*70)
    
    # Calculate derivatives
    processor = DataProcessor()
    data = processor.add_oi_analysis(data)
    
    # Calculate 50-period OI MA for thresholds
    data['oi_ma_50'] = data['oi'].rolling(window=50).mean()
    
    # Calculate SCLU thresholds
    data['entry_threshold'] = -0.005 * data['oi_ma_50']  # -0.5%
    data['exit_doi_threshold'] = -0.001 * data['oi_ma_50']  # -0.1%
    data['exit_d2oi_threshold'] = -0.005 * data['oi_ma_50']  # -0.5%
    
    # Identify signals
    data['buy_signal'] = (
        (data['oi_derivative'] < 0) & 
        (data['oi_second_derivative'] < data['entry_threshold'])
    )
    
    data['sell_signal'] = (
        (data['oi_derivative'] > data['exit_doi_threshold']) |
        (data['oi_second_derivative'] > data['exit_d2oi_threshold'])
    )
    
    # Print analysis
    print(f"OI Range: {data['oi'].min():,} to {data['oi'].max():,}")
    print(f"OI Decline: {((data['oi'].iloc[0] - data['oi'].iloc[-1]) / data['oi'].iloc[0]) * 100:.1f}%")
    
    buy_signals = data[data['buy_signal']]
    sell_signals = data[data['sell_signal']]
    
    print(f"\nSignal Analysis:")
    print(f"Buy Signals: {len(buy_signals)}")
    print(f"Sell Signals: {len(sell_signals)}")
    
    if len(buy_signals) > 0:
        print(f"First Buy Signal at: {buy_signals.index[0].strftime('%H:%M:%S')}")
        print(f"Price at First Signal: ₹{buy_signals['close'].iloc[0]:.2f}")
        
        if len(sell_signals) > 0:
            first_sell_after_buy = sell_signals[sell_signals.index > buy_signals.index[0]]
            if len(first_sell_after_buy) > 0:
                exit_price = first_sell_after_buy['close'].iloc[0]
                entry_price = buy_signals['close'].iloc[0]
                trade_return = ((exit_price - entry_price) / entry_price) * 100
                print(f"First Exit Signal at: {first_sell_after_buy.index[0].strftime('%H:%M:%S')}")
                print(f"Price at Exit: ₹{exit_price:.2f}")
                print(f"Trade Return: {trade_return:.1f}%")
    
    print("="*70)
    
    return data


if __name__ == "__main__":
    print("SCLU Strategy Example - Short Covering Rally Detection")
    print("=" * 70)
    print("This example simulates the strategy described in the SCLU document:")
    print("Naked option buying during short covering rallies using OI derivatives.")
    print()
    
    try:
        # Run the strategy example
        results = run_sclu_strategy_example()
        
        # Analyze OI derivatives
        analyzed_data = analyze_oi_derivatives(results['data'])
        
        print("\n" + "="*70)
        print("EXAMPLE COMPLETED!")
        print("="*70)
        print("This demonstrates how the SCLU strategy detects and trades")
        print("short covering events using Open Interest derivative analysis.")
        print()
        print("Next Steps:")
        print("1. Test with real historical options data")
        print("2. Validate on multiple short covering events")
        print("3. Optimize parameters for different underlyings")
        print("4. Implement VIX filtering for market conditions")
        print("5. Add strike selection logic for live trading")
        
    except Exception as e:
        logger.error(f"Error running SCLU strategy example: {e}")
        print(f"Error: {e}")
        print("Please check the logs for more details.")
