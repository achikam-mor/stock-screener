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
    data_loader = DataLoader(max_concurrent_requests=5)
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
    
    # Save all OHLC data for chart viewer
    chart_data = {}
    for symbol, data in stock_data.items():
        if data is not None and not data.empty:
            try:
                # Reset index to ensure it's datetime, not strings
                data = data.reset_index(drop=False)
                if 'Date' in data.columns:
                    data = data.set_index('Date')
                
                # Validate data row-by-row to keep arrays aligned
                dates = []
                opens = []
                highs = []
                lows = []
                closes = []
                volumes = []
                
                for idx, row in data.iterrows():
                    # Skip if index is the ticker symbol itself
                    if str(idx) == symbol:
                        continue
                    
                    # Validate all required fields
                    try:
                        date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)
                        o = float(row['Open'])
                        h = float(row['High'])
                        l = float(row['Low'])
                        c = float(row['Close'])
                        v = int(row['Volume'])
                        
                        # Only add row if all values are valid
                        if o > 0 and h > 0 and l > 0 and c > 0 and v >= 0:
                            dates.append(date_str)
                            opens.append(round(o, 2))
                            highs.append(round(h, 2))
                            lows.append(round(l, 2))
                            closes.append(round(c, 2))
                            volumes.append(v)
                    except (ValueError, TypeError, KeyError):
                        continue
                
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
    print(f"✅ Chart data saved: {len(chart_data)} stocks")
    
    # Screen stocks and combine failed tickers from both fetching and screening
    results = screener.screen_stocks(stock_data)
    results.failed_tickers.extend(fetch_failed_tickers)  # Add fetch failures to results

    # Display results
    results_manager.print_results(results)
    
    # Save results to JSON file for web display
    results_manager.save_to_json(results, len(tickers), "results.json")

if __name__ == "__main__":
    asyncio.run(main())
