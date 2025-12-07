"""
Fetch last 410 days of Open & Close prices from Yahoo Finance for tickers,
apply split-only adjustment, check SMA150 conditions, and calculate ATR14 for tickers that pass.
Supports priority-based scanning to reduce API calls.
"""

import asyncio
import argparse
import ast
import json
import os
from datetime import datetime
from data_loader import DataLoader
from stock_analyzer import StockAnalyzer
from stock_screener import StockScreener
from results_manager import ResultsManager
from market_data_fetcher import fetch_and_save_market_data


def load_tickers_from_file(filepath):
    """Load tickers from a file formatted as a Python list."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        content = f.read().strip()
        if not content:
            return []
        return ast.literal_eval(content)


def save_tickers_to_file(filepath, tickers):
    """Save tickers to a file in Python list format."""
    # Format like AllStocks.txt: multiple tickers per line with proper formatting
    formatted = "["
    for i, ticker in enumerate(sorted(set(tickers))):
        if i > 0:
            formatted += ", "
        if i > 0 and i % 15 == 0:  # New line every 15 tickers
            formatted += "\n"
        formatted += f"'{ticker}'"
    formatted += "]"
    
    with open(filepath, 'w') as f:
        f.write(formatted + "\n")


def classify_stocks_by_sma_distance(chart_data_raw):
    """
    Classify stocks into priority groups based on SMA150 distance.
    Priority1: -10% to +10% from SMA150
    Priority2: 10% to 15% (absolute) from SMA150
    Priority3: > 15% (absolute) from SMA150
    """
    priority1 = []
    priority2 = []
    priority3 = []
    
    for symbol, data in chart_data_raw.items():
        if not data.get('close') or not data.get('sma150'):
            priority3.append(symbol)  # Can't calculate, put in lowest priority
            continue
        
        # Get last close and SMA150
        last_close = data['close'][-1] if data['close'] else None
        last_sma150 = None
        
        # Find the last non-null SMA150 value
        for sma_val in reversed(data['sma150']):
            if sma_val is not None:
                last_sma150 = sma_val
                break
        
        if last_close is None or last_sma150 is None or last_sma150 == 0:
            priority3.append(symbol)
            continue
        
        # Calculate distance percentage
        distance_pct = ((last_close - last_sma150) / last_sma150) * 100
        abs_distance = abs(distance_pct)
        
        if abs_distance <= 10:
            priority1.append(symbol)
        elif abs_distance <= 15:
            priority2.append(symbol)
        else:
            priority3.append(symbol)
    
    return priority1, priority2, priority3


def merge_existing_chart_data(new_data, charts_dir='charts'):
    """Merge new chart data with existing data by reading individual stock files."""
    merged = dict(new_data)  # Start with new data
    
    if not os.path.exists(charts_dir):
        return merged
    
    # Read existing individual stock files for stocks not in new_data
    for filename in os.listdir(charts_dir):
        if filename.endswith('.json'):
            symbol = filename[:-5]  # Remove .json extension
            if symbol not in merged:
                try:
                    with open(os.path.join(charts_dir, filename), 'r') as f:
                        stock_data = json.load(f)
                        merged[symbol] = stock_data
                except (json.JSONDecodeError, IOError):
                    continue
    
    return merged


def save_individual_chart_files(chart_data, charts_dir='charts'):
    """Save each stock's chart data to individual JSON files."""
    os.makedirs(charts_dir, exist_ok=True)
    
    saved_count = 0
    for symbol, data in chart_data.items():
        filepath = os.path.join(charts_dir, f'{symbol}.json')
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f)
            saved_count += 1
        except Exception as e:
            print(f"⚠️ Could not save chart file for {symbol}: {str(e)}")
    
    return saved_count


def save_stock_list(chart_data, filepath='stock-list.json'):
    """Save a list of all available stock symbols for the search dropdown."""
    symbols = sorted(chart_data.keys())
    with open(filepath, 'w') as f:
        json.dump({
            "symbols": symbols,
            "count": len(symbols),
            "last_updated": datetime.now().isoformat()
        }, f)
    return len(symbols)


def merge_results(new_results, existing_filepath='results.json'):
    """Merge new results with existing results for stocks not scanned this run."""
    if not os.path.exists(existing_filepath):
        return None
    
    try:
        with open(existing_filepath, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Stock Screener with Priority-based Scanning')
    parser.add_argument('--mode', type=str, default='all',
                       choices=['all', 'priority1', 'priority1_2', 'manual'],
                       help='Scanning mode: all (all stocks), priority1 (P1 only), priority1_2 (P1+P2), manual (all stocks from AllStocks.txt)')
    parser.add_argument('--run-number', type=int, default=0,
                       help='Run number for scheduled executions (1-6)')
    args = parser.parse_args()
    
    print(f"🚀 Running stock screener in mode: {args.mode}")
    
    # Initialize components
    data_loader = DataLoader(max_concurrent_requests=7)
    analyzer = StockAnalyzer()
    screener = StockScreener(analyzer)
    results_manager = ResultsManager()

    # Determine which tickers to scan based on mode
    all_tickers = load_tickers_from_file("AllStocks.txt")
    
    if args.mode == 'manual' or args.mode == 'all':
        # Manual trigger or full scan: scan ALL stocks from AllStocks.txt
        tickers = all_tickers
        print(f"📋 Scanning ALL {len(tickers)} stocks from AllStocks.txt")
        is_full_scan = True
    elif args.mode == 'priority1':
        # Priority 1 only (runs 1, 2, 3, 5)
        priority1 = load_tickers_from_file("Priority1.txt")
        if not priority1:
            # If Priority1.txt doesn't exist, fall back to all stocks
            print("⚠️ Priority1.txt not found, falling back to all stocks")
            tickers = all_tickers
            is_full_scan = True
        else:
            tickers = priority1
            print(f"📋 Scanning {len(tickers)} Priority 1 stocks")
            is_full_scan = False
    elif args.mode == 'priority1_2':
        # Priority 1 and 2 (runs 4)
        priority1 = load_tickers_from_file("Priority1.txt")
        priority2 = load_tickers_from_file("Priority2.txt")
        if not priority1 and not priority2:
            print("⚠️ Priority files not found, falling back to all stocks")
            tickers = all_tickers
            is_full_scan = True
        else:
            tickers = list(set(priority1 + priority2))
            print(f"📋 Scanning {len(tickers)} Priority 1+2 stocks ({len(priority1)} P1, {len(priority2)} P2)")
            is_full_scan = False
    else:
        tickers = all_tickers
        is_full_scan = True

    # Fetch stock data in parallel
    stock_data, fetch_failed_tickers = await data_loader.fetch_all_stocks_data(tickers)
    
    # Save raw chart data immediately after fetching (before any screening or manipulation)
    print(f"💾 Saving raw chart data for {len(stock_data)} stocks...")
    import pandas as pd
    import numpy as np
    
    chart_data_raw = {}
    success_count = 0
    error_count = 0
    
    for symbol, data in stock_data.items():
        if data is None or data.empty:
            continue
        try:
            # Remove rows with NaN or inf values
            data_clean = data.replace([np.inf, -np.inf], np.nan).dropna()
            if data_clean.empty:
                continue
            
            # Calculate SMAs
            sma50 = data_clean['Close'].rolling(window=50).mean()
            sma150 = data_clean['Close'].rolling(window=150).mean()
            sma200 = data_clean['Close'].rolling(window=200).mean()
            
            # Just extract the data as-is, no modifications
            dates = [idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx) for idx in data_clean.index]
            opens = [round(float(o), 2) for o in data_clean['Open'].values]
            highs = [round(float(h), 2) for h in data_clean['High'].values]
            lows = [round(float(l), 2) for l in data_clean['Low'].values]
            closes = [round(float(c), 2) for c in data_clean['Close'].values]
            volumes = [int(v) for v in data_clean['Volume'].values]
            sma50_values = [round(float(s), 2) if not np.isnan(s) else None for s in sma50.values]
            sma150_values = [round(float(s), 2) if not np.isnan(s) else None for s in sma150.values]
            sma200_values = [round(float(s), 2) if not np.isnan(s) else None for s in sma200.values]
            
            if len(dates) > 0:
                chart_data_raw[symbol] = {
                    "dates": dates,
                    "open": opens,
                    "high": highs,
                    "low": lows,
                    "close": closes,
                    "volume": volumes,
                    "sma50": sma50_values,
                    "sma150": sma150_values,
                    "sma200": sma200_values
                }
                success_count += 1
        except Exception as e:
            error_count += 1
            print(f"⚠️ Could not save chart data for {symbol}: {str(e)}")
            continue
    
    print(f"📊 Chart data extraction: {success_count} successful, {error_count} errors")
    
    # Merge with existing chart data if not a full scan
    if is_full_scan:
        final_chart_data = chart_data_raw
    else:
        final_chart_data = merge_existing_chart_data(chart_data_raw)
    
    # Save individual chart files for each stock (for on-demand loading)
    print(f"💾 Saving individual chart files...")
    saved_files = save_individual_chart_files(final_chart_data)
    print(f"✅ Saved {saved_files} individual chart files to charts/ folder")
    
    # Save stock list for search dropdown
    stock_count = save_stock_list(final_chart_data)
    print(f"✅ Stock list saved: {stock_count} symbols")
    
    # Also save combined chart_data.json for backward compatibility (legacy)
    with open('chart_data.json', 'w') as f:
        json.dump({
            "stocks": final_chart_data,
            "last_updated": datetime.now().isoformat()
        }, f)
    print(f"✅ Combined chart data saved: {len(final_chart_data)} stocks total")
    
    # Classify stocks into priority groups based on current SMA distance
    # Use ALL available chart data for classification (to reclassify all stocks)
    if is_full_scan:
        print("🔄 Classifying all stocks into priority groups...")
        priority1, priority2, priority3 = classify_stocks_by_sma_distance(final_chart_data)
        
        # Save priority files
        save_tickers_to_file("Priority1.txt", priority1)
        save_tickers_to_file("Priority2.txt", priority2)
        save_tickers_to_file("Priority3.txt", priority3)
        
        print(f"📊 Priority classification:")
        print(f"   Priority 1 (±10% SMA): {len(priority1)} stocks")
        print(f"   Priority 2 (10-15% SMA): {len(priority2)} stocks")
        print(f"   Priority 3 (>15% SMA): {len(priority3)} stocks")
    else:
        # For partial scans, reclassify only the scanned stocks
        print("🔄 Reclassifying scanned stocks...")
        p1_new, p2_new, p3_new = classify_stocks_by_sma_distance(chart_data_raw)
        
        # Load existing priority files
        existing_p1 = set(load_tickers_from_file("Priority1.txt"))
        existing_p2 = set(load_tickers_from_file("Priority2.txt"))
        existing_p3 = set(load_tickers_from_file("Priority3.txt"))
        
        # Remove scanned tickers from all priority files
        scanned_tickers = set(chart_data_raw.keys())
        existing_p1 -= scanned_tickers
        existing_p2 -= scanned_tickers
        existing_p3 -= scanned_tickers
        
        # Add scanned tickers to their new priority
        updated_p1 = list(existing_p1 | set(p1_new))
        updated_p2 = list(existing_p2 | set(p2_new))
        updated_p3 = list(existing_p3 | set(p3_new))
        
        # Save updated priority files
        save_tickers_to_file("Priority1.txt", updated_p1)
        save_tickers_to_file("Priority2.txt", updated_p2)
        save_tickers_to_file("Priority3.txt", updated_p3)
        
        print(f"📊 Updated priority classification:")
        print(f"   Priority 1: {len(updated_p1)} stocks")
        print(f"   Priority 2: {len(updated_p2)} stocks")
        print(f"   Priority 3: {len(updated_p3)} stocks")
    
    # Screen stocks to identify which ones pass
    results = screener.screen_stocks(stock_data)
    results.failed_tickers.extend(fetch_failed_tickers)
    
    # Display results
    results_manager.print_results(results)
    
    # Save results to JSON file for web display
    results_manager.save_to_json(results, len(all_tickers), "results.json")
    
    # Fetch and save market sentiment data (Fear & Greed indices)
    print("\n📈 Fetching market sentiment data...")
    fetch_and_save_market_data()

if __name__ == "__main__":
    asyncio.run(main())
