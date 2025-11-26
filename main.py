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
    
    # Screen stocks first to identify which ones pass
    results = screener.screen_stocks(stock_data)
    results.failed_tickers.extend(fetch_failed_tickers)
    
    # Only save chart data for stocks that passed screening (hot + watch list)
    passing_stocks = set(list(results.hot_stocks.keys()) + list(results.watch_list.keys()))
    chart_data = {}
    for symbol in passing_stocks:
        data = stock_data.get(symbol)
        if data is None or data.empty:
            continue
        
        try:
                # Make a copy to avoid modifying original
                import pandas as pd
                data = data.copy()
                
                # Convert all OHLC columns to numeric first, coerce errors to NaN
                # This will convert any ticker symbols or invalid strings to NaN
                data['Open'] = pd.to_numeric(data['Open'], errors='coerce')
                data['High'] = pd.to_numeric(data['High'], errors='coerce')
                data['Low'] = pd.to_numeric(data['Low'], errors='coerce')
                data['Close'] = pd.to_numeric(data['Close'], errors='coerce')
                data['Volume'] = pd.to_numeric(data['Volume'], errors='coerce')
                
                # Filter out rows with invalid OHLC values (must be positive and not NaN)
                valid_mask = (data['Open'] > 0) & (data['High'] > 0) & (data['Low'] > 0) & (data['Close'] > 0) & (data['Volume'] >= 0)
                data = data[valid_mask]
                
                # Convert to lists
                dates = [idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx) for idx in data.index]
                opens = [round(float(o), 2) for o in data['Open']]
                highs = [round(float(h), 2) for h in data['High']]
                lows = [round(float(l), 2) for l in data['Low']]
                closes = [round(float(c), 2) for c in data['Close']]
                volumes = [int(v) for v in data['Volume']]
                
                # Only save if we have valid data
                if len(dates) > 0:
                    chart_data[symbol] = {
                        "dates": dates,
                        "open": opens,
                        "high": highs,
                        "low": lows,
                        "close": closes,
                        "volume": volumes
                    }
                    
        except Exception as e:
            print(f"⚠️ Could not save chart data for {symbol}: {str(e)}")
            continue
    
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
