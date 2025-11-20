"""
Fetch last 500 days of Open & Close prices from Yahoo Finance for all tickers in AllStocks.txt,
apply split-only adjustment, check SMA150 conditions, and calculate ATR14 for tickers that pass.
"""

import asyncio
from data_loader import DataLoader
from stock_analyzer import StockAnalyzer
from stock_screener import StockScreener
from results_manager import ResultsManager

async def main():
    # Initialize components
    data_loader = DataLoader(max_concurrent_requests=5)
    analyzer = StockAnalyzer()
    screener = StockScreener(analyzer)
    results_manager = ResultsManager()

    # Load tickers from AllStocks.txt
    import ast
    tickers_file = "AllStocks.txt"
    with open(tickers_file, 'r') as f:
        content = f.read()
        tickers = ast.literal_eval(content)

    # Fetch stock data in parallel
    stock_data, fetch_failed_tickers = await data_loader.fetch_all_stocks_data(tickers)

    # Screen stocks and combine failed tickers from both fetching and screening
    results = screener.screen_stocks(stock_data)
    results.failed_tickers.extend(fetch_failed_tickers)  # Add fetch failures to results

    # Display results
    results_manager.print_results(results)
    
    # Save results to JSON file for web display
    results_manager.save_to_json(results, len(tickers), "results.json")

if __name__ == "__main__":
    asyncio.run(main())
