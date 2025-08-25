#!/usr/bin/env python3
"""
SCLU Data Analysis Example

This example demonstrates how to analyze market data for SCLU strategy
development, including Open Interest analysis and visualization.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from sclu.data import DataLoader, DataProcessor
from sclu.utils import get_logger

# Set up logging
logger = get_logger(__name__)

# Optional: Set matplotlib style
try:
    plt.style.use('seaborn-v0_8')
except:
    plt.style.use('default')


def create_comprehensive_sample_data():
    """Create more comprehensive sample data with various market patterns."""
    logger.info("Creating comprehensive sample data...")
    
    # Generate 60 days of 1-minute data
    start_date = datetime.now() - timedelta(days=60)
    end_date = datetime.now()
    
    dates = pd.date_range(start=start_date, end=end_date, freq='1T')
    
    # Filter for market hours (9:15 AM to 3:30 PM IST)
    dates = dates[
        (dates.hour >= 9) & 
        ((dates.hour < 15) | ((dates.hour == 15) & (dates.minute <= 30)))
    ]
    
    # Create different market regimes
    n_points = len(dates)
    
    # Trending period (first 1/3)
    trend_period = n_points // 3
    
    # Sideways period (middle 1/3)
    sideways_period = n_points // 3
    
    # Volatile period (last 1/3)
    volatile_period = n_points - trend_period - sideways_period
    
    data = []
    base_price = 50.0
    base_oi = 1500000
    
    for i, date in enumerate(dates):
        if i < trend_period:
            # Trending market
            price_trend = 10 * (i / trend_period)  # Strong upward trend
            volatility = 0.5
            oi_pattern = 100000 * (i / trend_period)  # Growing OI
            
        elif i < trend_period + sideways_period:
            # Sideways market
            j = i - trend_period
            price_trend = 10 + 2 * np.sin(j / 10)  # Oscillating around level
            volatility = 0.3
            oi_pattern = 100000 + 20000 * np.sin(j / 15)  # Fluctuating OI
            
        else:
            # Volatile market
            j = i - trend_period - sideways_period
            price_trend = 12 + 5 * np.random.normal(0, 1)  # High volatility
            volatility = 1.5
            oi_pattern = 120000 + 50000 * np.random.normal(0, 0.5)  # Erratic OI
        
        # Add noise
        noise = np.random.normal(0, volatility)
        price = base_price + price_trend + noise
        
        # Create realistic OHLC
        spread = volatility * 0.5
        open_price = price + np.random.normal(0, spread/4)
        high_price = max(open_price, price) + abs(np.random.normal(0, spread/2))
        low_price = min(open_price, price) - abs(np.random.normal(0, spread/2))
        close_price = price
        
        # Volume with some correlation to price movement
        price_change = abs(close_price - open_price)
        volume = max(500, 1000 + 5000 * price_change + np.random.normal(0, 1000))
        
        # Open Interest with realistic patterns
        oi_noise = np.random.normal(0, 10000)
        oi = max(100000, base_oi + oi_pattern + oi_noise)
        
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
    
    logger.info(f"Created {len(df)} data points with multiple market regimes")
    return df


def analyze_open_interest_patterns(data):
    """Analyze Open Interest patterns and derivatives."""
    logger.info("Analyzing Open Interest patterns...")
    
    processor = DataProcessor()
    data = processor.add_oi_analysis(data)
    
    # Calculate additional metrics
    data['price_change'] = data['close'].pct_change()
    data['volume_ma'] = data['volume'].rolling(window=20).mean()
    data['oi_zscore'] = (data['oi'] - data['oi'].rolling(20).mean()) / data['oi'].rolling(20).std()
    
    # Analyze OI-Price relationships
    price_oi_corr = data['price_change'].corr(data['oi_pct_change'])
    volume_oi_corr = data['volume'].corr(data['oi'])
    
    print("\nOPEN INTEREST ANALYSIS")
    print("=" * 50)
    print(f"OI Range: {data['oi'].min():,.0f} - {data['oi'].max():,.0f}")
    print(f"Average OI: {data['oi'].mean():,.0f}")
    print(f"OI Volatility: {data['oi'].std():,.0f}")
    print(f"Price-OI Change Correlation: {price_oi_corr:.3f}")
    print(f"Volume-OI Correlation: {volume_oi_corr:.3f}")
    
    # Identify significant OI changes
    large_oi_changes = data[abs(data['oi_pct_change']) > 0.05]  # >5% changes
    print(f"Large OI Changes (>5%): {len(large_oi_changes)} occurrences")
    
    return data


def analyze_strategy_signals(data):
    """Analyze potential SCLU strategy signals."""
    logger.info("Analyzing strategy signals...")
    
    # SCLU signal parameters
    sensitivity = 0.01
    feeling = 3000000
    
    # Calculate signals
    data['buy_signal'] = (
        (data['oi_derivative'] < 0) & 
        (data['oi_second_derivative'] < -0.1 * sensitivity * feeling)
    )
    
    data['sell_signal'] = (
        (data['oi_derivative'] > -1 * sensitivity * feeling) |
        (data['oi_second_derivative'] > -0.1 * sensitivity * feeling)
    )
    
    # Analyze signal frequency
    buy_signals = data[data['buy_signal']].copy()
    total_buy_signals = len(buy_signals)
    
    print("\nSTRATEGY SIGNAL ANALYSIS")
    print("=" * 50)
    print(f"Total Buy Signals: {total_buy_signals}")
    print(f"Signal Frequency: {total_buy_signals / len(data) * 100:.2f}% of periods")
    
    if total_buy_signals > 0:
        # Analyze signal timing
        signal_intervals = buy_signals.index.to_series().diff().dt.total_seconds() / 60
        print(f"Average Signal Interval: {signal_intervals.mean():.1f} minutes")
        print(f"Min Signal Interval: {signal_intervals.min():.1f} minutes")
        print(f"Max Signal Interval: {signal_intervals.max():.1f} minutes")
        
        # Analyze signal quality (next period returns)
        buy_signals['next_return'] = data['close'].shift(-1) / data['close'] - 1
        buy_signals = buy_signals.dropna()
        
        if len(buy_signals) > 0:
            avg_next_return = buy_signals['next_return'].mean()
            win_rate = (buy_signals['next_return'] > 0).mean()
            
            print(f"Average Next-Period Return: {avg_next_return * 100:.3f}%")
            print(f"Signal Win Rate: {win_rate * 100:.1f}%")
    
    return data


def create_visualizations(data):
    """Create comprehensive visualizations."""
    logger.info("Creating visualizations...")
    
    fig, axes = plt.subplots(4, 1, figsize=(15, 12))
    fig.suptitle('SCLU Strategy Data Analysis', fontsize=16, fontweight='bold')
    
    # Price and volume
    ax1 = axes[0]
    ax1.plot(data.index, data['close'], label='Close Price', color='blue', linewidth=1)
    ax1.set_ylabel('Price', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True, alpha=0.3)
    
    # Volume on secondary y-axis
    ax1_vol = ax1.twinx()
    ax1_vol.bar(data.index, data['volume'], alpha=0.3, color='gray', width=0.8)
    ax1_vol.set_ylabel('Volume', color='gray')
    ax1_vol.tick_params(axis='y', labelcolor='gray')
    
    ax1.set_title('Price and Volume')
    ax1.legend(loc='upper left')
    
    # Open Interest
    ax2 = axes[1]
    ax2.plot(data.index, data['oi'], label='Open Interest', color='green', linewidth=1)
    ax2.fill_between(data.index, data['oi'], alpha=0.3, color='green')
    ax2.set_ylabel('Open Interest')
    ax2.set_title('Open Interest Over Time')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # OI Derivatives
    ax3 = axes[2]
    ax3.plot(data.index, data['oi_derivative'], label='OI Derivative', color='orange', linewidth=1)
    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax3.set_ylabel('OI Derivative')
    ax3.set_title('Open Interest First Derivative (Rate of Change)')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # OI Second Derivative with signals
    ax4 = axes[3]
    ax4.plot(data.index, data['oi_second_derivative'], label='OI Second Derivative', 
             color='red', linewidth=1)
    ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # Mark buy signals
    if 'buy_signal' in data.columns:
        buy_points = data[data['buy_signal']]
        ax4.scatter(buy_points.index, buy_points['oi_second_derivative'], 
                   color='green', marker='^', s=50, label='Buy Signals', zorder=5)
    
    ax4.set_ylabel('OI Second Derivative')
    ax4.set_title('Open Interest Second Derivative with Trading Signals')
    ax4.set_xlabel('Date')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    
    plt.tight_layout()
    plt.show()
    
    # Additional correlation analysis plot
    fig2, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
    fig2.suptitle('Correlation Analysis', fontsize=16, fontweight='bold')
    
    # Price vs OI
    ax1.scatter(data['oi'], data['close'], alpha=0.5, s=1)
    ax1.set_xlabel('Open Interest')
    ax1.set_ylabel('Close Price')
    ax1.set_title('Price vs Open Interest')
    ax1.grid(True, alpha=0.3)
    
    # Price change vs OI change
    ax2.scatter(data['oi_pct_change'], data['price_change'], alpha=0.5, s=1)
    ax2.set_xlabel('OI % Change')
    ax2.set_ylabel('Price % Change')
    ax2.set_title('Price Change vs OI Change')
    ax2.grid(True, alpha=0.3)
    
    # Volume vs Price
    ax3.scatter(data['volume'], data['close'], alpha=0.5, s=1)
    ax3.set_xlabel('Volume')
    ax3.set_ylabel('Close Price')
    ax3.set_title('Price vs Volume')
    ax3.grid(True, alpha=0.3)
    
    # OI Derivative distribution
    ax4.hist(data['oi_derivative'].dropna(), bins=50, alpha=0.7, color='orange')
    ax4.axvline(x=0, color='red', linestyle='--')
    ax4.set_xlabel('OI Derivative')
    ax4.set_ylabel('Frequency')
    ax4.set_title('OI Derivative Distribution')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def analyze_market_regimes(data):
    """Analyze different market regimes and strategy performance."""
    logger.info("Analyzing market regimes...")
    
    # Define market regimes based on volatility and trend
    data['returns'] = data['close'].pct_change()
    data['volatility'] = data['returns'].rolling(20).std()
    data['trend'] = data['close'].rolling(20).apply(lambda x: (x[-1] - x[0]) / x[0])
    
    # Classify regimes
    vol_threshold = data['volatility'].quantile(0.7)
    trend_threshold = 0.02
    
    conditions = [
        (data['volatility'] < vol_threshold) & (data['trend'] > trend_threshold),
        (data['volatility'] < vol_threshold) & (data['trend'] < -trend_threshold),
        (data['volatility'] < vol_threshold) & (abs(data['trend']) <= trend_threshold),
        data['volatility'] >= vol_threshold
    ]
    
    choices = ['Trending Up', 'Trending Down', 'Sideways', 'High Volatility']
    data['regime'] = np.select(conditions, choices, default='Unknown')
    
    # Analyze regime distribution
    regime_counts = data['regime'].value_counts()
    
    print("\nMARKET REGIME ANALYSIS")
    print("=" * 50)
    for regime, count in regime_counts.items():
        percentage = (count / len(data)) * 100
        print(f"{regime}: {count} periods ({percentage:.1f}%)")
    
    # Analyze OI behavior in different regimes
    print("\nOI BEHAVIOR BY REGIME")
    print("-" * 30)
    for regime in choices:
        regime_data = data[data['regime'] == regime]
        if len(regime_data) > 0:
            avg_oi_change = regime_data['oi_pct_change'].mean()
            avg_oi_vol = regime_data['oi_pct_change'].std()
            print(f"{regime}:")
            print(f"  Avg OI Change: {avg_oi_change:.4f}")
            print(f"  OI Volatility: {avg_oi_vol:.4f}")


def main():
    """Main analysis function."""
    print("SCLU Data Analysis Example")
    print("=" * 50)
    print("This example demonstrates comprehensive market data analysis")
    print("for SCLU strategy development and optimization.\n")
    
    try:
        # Create comprehensive sample data
        data = create_comprehensive_sample_data()
        
        # Run analyses
        data = analyze_open_interest_patterns(data)
        data = analyze_strategy_signals(data)
        analyze_market_regimes(data)
        
        # Create visualizations
        print("\nGenerating visualizations...")
        create_visualizations(data)
        
        # Save processed data for further analysis
        output_file = Path(__file__).parent / "sample_analysis_data.csv"
        data.to_csv(output_file)
        print(f"\nProcessed data saved to: {output_file}")
        
        print("\n" + "=" * 50)
        print("ANALYSIS COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("Key insights:")
        print("1. Open Interest patterns vary significantly across market regimes")
        print("2. OI derivatives can provide early signals of market changes")
        print("3. Strategy signal frequency depends heavily on parameter tuning")
        print("4. Correlation analysis helps understand market microstructure")
        print("\nNext steps:")
        print("1. Test with real historical data")
        print("2. Optimize parameters for different market conditions")
        print("3. Implement regime-aware parameter adjustment")
        print("4. Validate findings with out-of-sample data")
        
    except Exception as e:
        logger.error(f"Error in data analysis: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
