"""
Test script to verify volume-based screening logic
"""
import asyncio
from data_loader import DataLoader
from stock_analyzer import StockAnalyzer
from stock_screener import StockScreener
from results_manager import ResultsManager

async def main():
    # Test tickers
    tickers = ["AMZN", "MSFT", "META", "BLK", "AAPL", "JPM", "VRNS"]
    
    print("=" * 80)
    print("Testing Volume-Based Stock Screening")
    print("=" * 80)
    print(f"\nTest Tickers: {', '.join(tickers)}")
    print(f"Total: {len(tickers)} stocks\n")
    
    # Initialize components
    data_loader = DataLoader(max_concurrent_requests=5)
    analyzer = StockAnalyzer()
    screener = StockScreener(analyzer)
    results_manager = ResultsManager()

    # Fetch stock data
    print("Fetching stock data...")
    stock_data, fetch_failed_tickers = await data_loader.fetch_all_stocks_data(tickers)
    print(f"Successfully fetched: {len(stock_data)} stocks")
    if fetch_failed_tickers:
        print(f"Failed to fetch: {', '.join(fetch_failed_tickers)}")
    
    # Screen stocks
    print("\nScreening stocks with new logic...")
    print("Filters:")
    print("  - ATR% must be >= 0.5%")
    print("  - Hot Stocks: Above SMA150 AND volume > 14-day average")
    print("  - Watch List: (Above SMA with low volume) OR (Below SMA)")
    print()
    
    results = screener.screen_stocks(stock_data)
    results.failed_tickers.extend(fetch_failed_tickers)

    # Display results
    results_manager.print_results(results)
    
    # Save to JSON for web viewing
    results_manager.save_to_json(results, "results.json")
    
    print("\n" + "=" * 80)
    print("Summary:")
    print(f"  Hot Stocks: {len(results.hot_stocks)}")
    print(f"  Watch List: {len(results.watch_list)}")
    print(f"  Failed: {len(results.failed_tickers)}")
    print(f"  Total Analyzed: {len(results.hot_stocks) + len(results.watch_list)}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
