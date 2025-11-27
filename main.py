"""
Fetch last 500 days of Open & Close prices from Yahoo Finance for all tickers in AllStocks.txt,
apply split-only adjustment, check SMA150 conditions, and calculate ATR14 for tickers that pass.
"""

import asyncio
from datetime import datetime
from data_loader import DataLoader
from stock_analyzer import StockAnalyzer
from stock_screener import StockScreener
from results_manager import ResultsManager

async def main():
    # Initialize components
    data_loader = DataLoader(max_concurrent_requests=7)
    analyzer = StockAnalyzer()
    screener = StockScreener(analyzer)
    results_manager = ResultsManager()

    # Load tickers from AllStocks.txt
    import ast
    import json
    tickers_file = "AllStocks.txt"
    with open(tickers_file, 'r') as f:
        content = f.read()
        tickers = ast.literal_eval(content)

    # Fetch stock data in parallel
    stock_data, fetch_failed_tickers = await data_loader.fetch_all_stocks_data(tickers)
    
    # Save raw chart data immediately after fetching (before any screening or manipulation)
    print(f"💾 Saving raw chart data for {len(stock_data)} stocks...")
    chart_data_raw = {}
    success_count = 0
    error_count = 0
    
    for symbol, data in stock_data.items():
        if data is None or data.empty:
            continue
        try:
            import pandas as pd
            import numpy as np
            # Remove rows with NaN or inf values
            data_clean = data.replace([np.inf, -np.inf], np.nan).dropna()
            if data_clean.empty:
                continue
            
            # Calculate SMA150 (150-day Simple Moving Average)
            sma150 = data_clean['Close'].rolling(window=150).mean()
            
            # Just extract the data as-is, no modifications
            dates = [idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx) for idx in data_clean.index]
            opens = [round(float(o), 2) for o in data_clean['Open'].values]
            highs = [round(float(h), 2) for h in data_clean['High'].values]
            lows = [round(float(l), 2) for l in data_clean['Low'].values]
            closes = [round(float(c), 2) for c in data_clean['Close'].values]
            volumes = [int(v) for v in data_clean['Volume'].values]
            sma150_values = [round(float(s), 2) if not np.isnan(s) else None for s in sma150.values]
            
            if len(dates) > 0:
                chart_data_raw[symbol] = {
                    "dates": dates,
                    "open": opens,
                    "high": highs,
                    "low": lows,
                    "close": closes,
                    "volume": volumes,
                    "sma150": sma150_values
                }
                success_count += 1
        except Exception as e:
            error_count += 1
            print(f"⚠️ Could not save chart data for {symbol}: {str(e)}")
            continue
    
    print(f"📊 Chart data extraction: {success_count} successful, {error_count} errors")
    
    # Screen stocks to identify which ones pass
    results = screener.screen_stocks(stock_data)
    results.failed_tickers.extend(fetch_failed_tickers)
    
    # Filter chart data to only include passing stocks (hot + watch list)
    passing_stocks = set(list(results.hot_stocks.keys()) + list(results.watch_list.keys()))
    print(f"🔍 Filtering chart data: {len(passing_stocks)} stocks passed screening")
    chart_data = {symbol: data for symbol, data in chart_data_raw.items() if symbol in passing_stocks}
    print(f"✅ Final chart data: {len(chart_data)} stocks (after filtering for hot + watch list)")
    
    with open('chart_data.json', 'w') as f:
        json.dump({
            "stocks": chart_data,
            "last_updated": datetime.now().isoformat()
        }, f)
    print(f"✅ Chart data saved: {len(chart_data)} stocks (hot + watch list only)")
    
    # Display results
    results_manager.print_results(results)
    
    # Save results to JSON file for web display
    results_manager.save_to_json(results, len(tickers), "results.json")

if __name__ == "__main__":
    asyncio.run(main())
