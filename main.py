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
    
    # Add VIX ticker for market overview page
    tickers_with_vix = tickers + ["^VIX"]

    # Fetch stock data in parallel
    stock_data, fetch_failed_tickers = await data_loader.fetch_all_stocks_data(tickers_with_vix)

    # Extract VIX data before screening
    vix_data = stock_data.pop("^VIX", None)
    if vix_data is not None and not vix_data.empty:
        try:
            # Reset index to ensure it's datetime, not strings
            vix_data = vix_data.reset_index(drop=False)
            if 'Date' in vix_data.columns:
                vix_data = vix_data.set_index('Date')
            
            # Save VIX data to JSON for market overview page
            vix_json = {
                "dates": [date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date) for date in vix_data.index],
                "values": [round(float(close), 2) for close in vix_data['Close'] if str(close).replace('.','',1).replace('-','',1).isdigit()],
                "last_updated": datetime.now().isoformat()
            }
            with open('vix_data.json', 'w') as f:
                json.dump(vix_json, f, indent=2)
            print(f"✅ VIX data saved: {len(vix_json['dates'])} days")
        except Exception as e:
            print(f"⚠️ Could not save VIX data: {str(e)}")
    
    # Save all OHLC data for chart viewer
    chart_data = {}
    for symbol, data in stock_data.items():
        if data is not None and not data.empty:
            try:
                chart_data[symbol] = {
                    "dates": [date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date) for date in data.index],
                    "open": [round(float(o), 2) for o in data['Open']],
                    "high": [round(float(h), 2) for h in data['High']],
                    "low": [round(float(l), 2) for l in data['Low']],
                    "close": [round(float(c), 2) for c in data['Close']],
                    "volume": [int(v) for v in data['Volume']]
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
