#!/usr/bin/env python3
"""
SCLU Backtesting Script

Run backtests for the SCLU trading strategy using historical data.
"""

import argparse
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import backtrader as bt
from sclu.strategies import SCLUStrategy
from sclu.data import DataLoader
from sclu.utils import Config, get_logger

logger = get_logger(__name__)


def run_backtest(
    data_file: str,
    initial_cash: float = 100000.0,
    strategy_params: dict = None,
    plot: bool = False
) -> dict:
    """
    Run a backtest with the specified parameters.
    
    Args:
        data_file: Path to historical data file
        initial_cash: Starting cash amount
        strategy_params: Strategy parameters override
        plot: Whether to plot results
        
    Returns:
        dict: Backtest results
    """
    logger.info(f"Starting backtest with data file: {data_file}")
    
    # Create cerebro instance
    cerebro = bt.Cerebro()
    
    # Load data
    loader = DataLoader()
    data_feed = loader.create_backtrader_feed(data_file)
    
    # Resample to 3-minute bars (NSE OI refresh cycle)
    cerebro.resampledata(data_feed, timeframe=bt.TimeFrame.Minutes, compression=3)
    
    # Add strategy
    if strategy_params:
        cerebro.addstrategy(SCLUStrategy, **strategy_params)
    else:
        cerebro.addstrategy(SCLUStrategy)
    
    # Set broker parameters
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    # Record starting value
    starting_value = cerebro.broker.getvalue()
    logger.info(f'Starting Portfolio Value: {starting_value:.2f}')
    
    # Run backtest
    results = cerebro.run()
    
    # Get final value
    final_value = cerebro.broker.getvalue()
    logger.info(f'Final Portfolio Value: {final_value:.2f}')
    
    # Extract results
    strategy_result = results[0]
    
    # Calculate performance metrics
    total_return = (final_value - starting_value) / starting_value
    
    backtest_results = {
        'starting_value': starting_value,
        'final_value': final_value,
        'total_return': total_return,
        'total_return_pct': total_return * 100,
    }
    
    # Add analyzer results
    try:
        sharpe_ratio = strategy_result.analyzers.sharpe.get_analysis().get('sharperatio', 0)
        drawdown = strategy_result.analyzers.drawdown.get_analysis()
        trades = strategy_result.analyzers.trades.get_analysis()
        
        backtest_results.update({
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': drawdown.get('max', {}).get('drawdown', 0),
            'total_trades': trades.get('total', {}).get('total', 0),
            'winning_trades': trades.get('won', {}).get('total', 0),
            'losing_trades': trades.get('lost', {}).get('total', 0),
        })
        
        # Calculate win rate
        total_trades = backtest_results['total_trades']
        if total_trades > 0:
            backtest_results['win_rate'] = (backtest_results['winning_trades'] / total_trades) * 100
        else:
            backtest_results['win_rate'] = 0
        
    except Exception as e:
        logger.warning(f"Error extracting analyzer results: {e}")
    
    # Plot results if requested
    if plot:
        try:
            cerebro.plot(style='candlestick')
        except Exception as e:
            logger.warning(f"Error plotting results: {e}")
    
    return backtest_results


def print_results(results: dict) -> None:
    """Print backtest results in a formatted way."""
    print("\n" + "="*50)
    print("BACKTEST RESULTS")
    print("="*50)
    print(f"Starting Value:     ${results['starting_value']:,.2f}")
    print(f"Final Value:        ${results['final_value']:,.2f}")
    print(f"Total Return:       ${results['final_value'] - results['starting_value']:,.2f}")
    print(f"Total Return %:     {results['total_return_pct']:.2f}%")
    print(f"Sharpe Ratio:       {results.get('sharpe_ratio', 'N/A')}")
    print(f"Max Drawdown:       {results.get('max_drawdown', 'N/A'):.2f}%")
    print(f"Total Trades:       {results.get('total_trades', 'N/A')}")
    print(f"Winning Trades:     {results.get('winning_trades', 'N/A')}")
    print(f"Losing Trades:      {results.get('losing_trades', 'N/A')}")
    print(f"Win Rate:           {results.get('win_rate', 'N/A'):.1f}%")
    print("="*50)


def main():
    """Main entry point for backtest script."""
    parser = argparse.ArgumentParser(description="Run SCLU strategy backtest")
    parser.add_argument("data_file", help="Path to historical data CSV file")
    parser.add_argument("--cash", type=float, default=100000.0, help="Initial cash amount")
    parser.add_argument("--plot", action="store_true", help="Plot backtest results")
    parser.add_argument("--sensitivity", type=float, help="Strategy sensitivity parameter")
    parser.add_argument("--feeling", type=int, help="Strategy feeling parameter")
    parser.add_argument("--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config(args.config) if args.config else Config()
    
    # Prepare strategy parameters
    strategy_params = {}
    if args.sensitivity:
        strategy_params['sensitivity'] = args.sensitivity
    if args.feeling:
        strategy_params['feeling'] = args.feeling
    
    try:
        # Run backtest
        results = run_backtest(
            data_file=args.data_file,
            initial_cash=args.cash,
            strategy_params=strategy_params,
            plot=args.plot
        )
        
        # Print results
        print_results(results)
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
