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
import numpy as np
import pandas as pd
from datetime import datetime
from data_loader import DataLoader
from stock_analyzer import StockAnalyzer
from stock_screener import StockScreener
from results_manager import ResultsManager
from market_data_fetcher import fetch_and_save_market_data
from candlestick_patterns import scan_patterns_last_7days, detect_cup_and_handle

def calculate_atr_for_chart(highs, lows, closes, window=14):
    """
    Calculate ATR (Average True Range) for chart data.
    Returns current ATR value and ATR as percentage of current price.
    """
    if len(highs) < window + 1 or len(lows) < window + 1 or len(closes) < window + 1:
        return None, None
    
    # True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
    # For simplicity, use High-Low range (common approximation)
    true_ranges = []
    for i in range(1, len(highs)):
        high_low = highs[i] - lows[i]
        high_prev_close = abs(highs[i] - closes[i-1])
        low_prev_close = abs(lows[i] - closes[i-1])
        tr = max(high_low, high_prev_close, low_prev_close)
        true_ranges.append(tr)
    
    # Calculate ATR as average of last 'window' true ranges
    if len(true_ranges) < window:
        return None, None
    
    atr = sum(true_ranges[-window:]) / window
    current_price = closes[-1]
    atr_percent = (atr / current_price) * 100 if current_price > 0 else 0
    
    return round(atr, 2), round(atr_percent, 2)


def calculate_rsi_for_chart(closes, window=14):
    """
    Calculate RSI (Relative Strength Index) for chart data.
    Returns list of RSI values (None for first 'window' values).
    """
    if len(closes) < window + 1:
        return [None] * len(closes)
    
    rsi_values = [None] * window  # First 'window' values are None
    
    # Calculate price changes
    changes = []
    for i in range(1, len(closes)):
        changes.append(closes[i] - closes[i-1])
    
    # Calculate initial average gain/loss
    gains = [max(0, c) for c in changes[:window]]
    losses = [abs(min(0, c)) for c in changes[:window]]
    
    avg_gain = sum(gains) / window
    avg_loss = sum(losses) / window
    
    # Calculate first RSI
    if avg_loss == 0:
        rsi_values.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi_values.append(round(100 - (100 / (1 + rs)), 2))
    
    # Calculate subsequent RSI values using smoothed averages
    for i in range(window, len(changes)):
        change = changes[i]
        gain = max(0, change)
        loss = abs(min(0, change))
        
        # Smoothed average
        avg_gain = (avg_gain * (window - 1) + gain) / window
        avg_loss = (avg_loss * (window - 1) + loss) / window
        
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(round(100 - (100 / (1 + rs)), 2))
    
    return rsi_values


def calculate_relative_strength(stock_closes, spy_closes, dates, spy_dates):
    """
    Calculate Relative Strength (RS) ratio comparing stock performance to SPY.
    RS = (Stock Price / SPY Price) normalized to 100 at start.
    Returns list of RS values aligned to stock dates.
    """
    if not stock_closes or not spy_closes:
        return None
    
    # Create a date-indexed lookup for SPY prices
    spy_price_map = {}
    for i, d in enumerate(spy_dates):
        spy_price_map[d] = spy_closes[i]
    
    rs_values = []
    base_ratio = None
    
    for i, date in enumerate(dates):
        spy_price = spy_price_map.get(date)
        stock_price = stock_closes[i]
        
        if spy_price and stock_price and spy_price > 0:
            ratio = stock_price / spy_price
            
            # Set base ratio from first valid data point
            if base_ratio is None:
                base_ratio = ratio
            
            # Normalize to 100 at start
            rs = round((ratio / base_ratio) * 100, 2) if base_ratio > 0 else None
            rs_values.append(rs)
        else:
            rs_values.append(None)
    
    return rs_values


def detect_golden_death_cross(sma50_values, sma200_values, lookback_days=5):
    """
    Detect Golden Cross (50 SMA crosses above 200 SMA) and Death Cross (50 SMA crosses below 200 SMA).
    
    Args:
        sma50_values: List of SMA50 values
        sma200_values: List of SMA200 values
        lookback_days: Number of days to look back for a recent cross (default 5)
    
    Returns:
        Tuple of (golden_cross: bool, death_cross: bool)
        - golden_cross: True if 50 SMA crossed above 200 SMA within lookback period
        - death_cross: True if 50 SMA crossed below 200 SMA within lookback period
    """
    golden_cross = False
    death_cross = False
    
    if not sma50_values or not sma200_values:
        return golden_cross, death_cross
    
    # Need at least 2 data points to detect a cross
    if len(sma50_values) < 2 or len(sma200_values) < 2:
        return golden_cross, death_cross
    
    # Look at the last 'lookback_days' days for a cross
    end_idx = len(sma50_values)
    start_idx = max(0, end_idx - lookback_days - 1)  # +1 because we need previous day to compare
    
    for i in range(start_idx + 1, end_idx):
        curr_sma50 = sma50_values[i]
        prev_sma50 = sma50_values[i - 1]
        curr_sma200 = sma200_values[i]
        prev_sma200 = sma200_values[i - 1]
        
        # Skip if any value is None
        if None in (curr_sma50, prev_sma50, curr_sma200, prev_sma200):
            continue
        
        # Golden Cross: 50 SMA was below 200 SMA, now above
        if prev_sma50 <= prev_sma200 and curr_sma50 > curr_sma200:
            golden_cross = True
            death_cross = False  # Can't have both at same time
            
        # Death Cross: 50 SMA was above 200 SMA, now below
        elif prev_sma50 >= prev_sma200 and curr_sma50 < curr_sma200:
            death_cross = True
            golden_cross = False  # Can't have both at same time
    
    return golden_cross, death_cross


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
    
    # Fetch SPY data for Relative Strength calculation
    print(f"📈 Fetching SPY data for Relative Strength calculation...")
    spy_data = None
    spy_dates = []
    spy_closes = []
    try:
        spy_response, _ = await data_loader.fetch_all_stocks_data(["SPY"])
        if "SPY" in spy_response and spy_response["SPY"] is not None:
            spy_df = spy_response["SPY"].replace([np.inf, -np.inf], np.nan).dropna()
            if not spy_df.empty:
                spy_dates = [idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx) for idx in spy_df.index]
                spy_closes = [round(float(c), 2) for c in spy_df['Close'].values]
                print(f"✅ SPY data loaded: {len(spy_closes)} data points")
    except Exception as e:
        print(f"⚠️ Could not fetch SPY data for RS calculation: {e}")
    
    # Save raw chart data immediately after fetching (before any screening or manipulation)
    print(f"💾 Saving raw chart data for {len(stock_data)} stocks...")
    # Note: pandas and numpy are already imported at module level
    
    chart_data_raw = {}
    success_count = 0
    error_count = 0
    
    for symbol, data in stock_data.items():
        if data is None:
            continue
        if data.empty:
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
                # Calculate ATR for chart display
                atr_value, atr_pct = calculate_atr_for_chart(highs, lows, closes)
                
                # Calculate RSI for chart display
                rsi_values = calculate_rsi_for_chart(closes)
                
                # Calculate Relative Strength vs SPY
                rs_values = None
                if spy_closes and spy_dates:
                    rs_values = calculate_relative_strength(closes, spy_closes, dates, spy_dates)
                
                # Calculate Golden Cross / Death Cross
                golden_cross, death_cross = detect_golden_death_cross(sma50_values, sma200_values)
                
                # Calculate volume metrics
                last_volume = volumes[-1] if volumes else 0
                avg_volume_14d = round(sum(volumes[-15:-1]) / 14) if len(volumes) >= 15 else round(sum(volumes) / len(volumes)) if volumes else 0
                
                # Calculate Key Levels (Support/Resistance)
                key_levels = analyzer.find_key_levels(data_clean)
                
                chart_data_raw[symbol] = {
                    "dates": dates,
                    "open": opens,
                    "high": highs,
                    "low": lows,
                    "close": closes,
                    "volume": volumes,
                    "sma50": sma50_values,
                    "sma150": sma150_values,
                    "sma200": sma200_values,
                    # New fields for enhanced chart display
                    "atr": atr_value,
                    "atr_percent": atr_pct,
                    "last_volume": last_volume,
                    "avg_volume_14d": avg_volume_14d,
                    # RSI indicator
                    "rsi": rsi_values,
                    # Relative Strength vs SPY
                    "rs_spy": rs_values,
                    # Key Levels
                    "key_levels": key_levels,
                    # Golden Cross / Death Cross indicators
                    "golden_cross": golden_cross,
                    "death_cross": death_cross
                }
                success_count += 1
        except Exception as e:
            error_count += 1
            print(f"⚠️ Could not save chart data for {symbol}: {str(e)}")
            continue
    
    print(f"📊 Chart data extraction: {success_count} successful, {error_count} errors")
    
    # Log stocks with Golden Cross or Death Cross
    golden_cross_stocks = [sym for sym, data in chart_data_raw.items() if data.get('golden_cross', False)]
    death_cross_stocks = [sym for sym, data in chart_data_raw.items() if data.get('death_cross', False)]
    
    if golden_cross_stocks:
        print(f"✨ Golden Cross detected ({len(golden_cross_stocks)}): {', '.join(sorted(golden_cross_stocks))}")
    if death_cross_stocks:
        print(f"💀 Death Cross detected ({len(death_cross_stocks)}): {', '.join(sorted(death_cross_stocks))}")
    if not golden_cross_stocks and not death_cross_stocks:
        print(f"📈 No crosses detected in this batch")
    
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
        
        # Update priority1 variable for pattern detection
        priority1 = updated_p1
    
    # Detect candlestick patterns for Priority1 stocks (within ±10% of SMA150)
    print(f"\n🕯️ Detecting candlestick patterns for {len(priority1)} Priority 1 stocks...")
    priority1_set = set(priority1)  # Convert to set for O(1) lookup
    pattern_count = 0
    stocks_with_patterns = 0
    
    for symbol in chart_data_raw.keys():
        if symbol in priority1_set:
            chart_data = chart_data_raw[symbol]
            
            try:
                # Get OHLC data for pattern detection
                opens = chart_data.get('open', [])
                highs = chart_data.get('high', [])
                lows = chart_data.get('low', [])
                closes = chart_data.get('close', [])
                volumes = chart_data.get('volume', [])
                dates = chart_data.get('dates', [])
                atr = chart_data.get('atr')
                
                # Detect patterns in last 7 days
                patterns = scan_patterns_last_7days(opens, highs, lows, closes, volumes, atr, dates)
                
                # Store patterns in chart data
                chart_data_raw[symbol]['candlestick_patterns'] = patterns
                
                if patterns:
                    pattern_count += len(patterns)
                    stocks_with_patterns += 1
            
            except Exception as e:
                print(f"⚠️ Could not detect patterns for {symbol}: {str(e)}")
                chart_data_raw[symbol]['candlestick_patterns'] = []
    
    print(f"✅ Pattern detection complete: {pattern_count} patterns detected across {stocks_with_patterns} stocks")
    
    # Detect Cup and Handle patterns for ALL stocks (not just Priority1)
    print(f"\n☕ Detecting Cup and Handle patterns for all stocks...")
    cup_handle_count = 0
    stocks_with_cup_handle = 0
    
    # Load all stock symbols
    all_stocks_symbols = set()
    if os.path.exists("AllStocks.txt"):
        with open("AllStocks.txt", "r") as f:
            all_stocks_symbols = set(line.strip() for line in f if line.strip())
    
    for symbol in chart_data_raw.keys():
        if symbol in all_stocks_symbols:
            chart_data = chart_data_raw[symbol]
            
            try:
                # Get OHLC data for cup and handle detection
                opens = chart_data.get('open', [])
                highs = chart_data.get('high', [])
                lows = chart_data.get('low', [])
                closes = chart_data.get('close', [])
                volumes = chart_data.get('volume', [])
                dates = chart_data.get('dates', [])
                
                # Detect cup and handle pattern
                cup_handle_pattern = detect_cup_and_handle(opens, highs, lows, closes, volumes, dates)
                
                # Store pattern in chart data (separate key from candlestick patterns)
                if cup_handle_pattern:
                    chart_data_raw[symbol]['cup_and_handle_patterns'] = [cup_handle_pattern]
                    cup_handle_count += 1
                    stocks_with_cup_handle += 1
                else:
                    chart_data_raw[symbol]['cup_and_handle_patterns'] = []
            
            except Exception as e:
                print(f"⚠️ Could not detect cup and handle for {symbol}: {str(e)}")
                chart_data_raw[symbol]['cup_and_handle_patterns'] = []
    
    print(f"✅ Cup and Handle detection complete: {cup_handle_count} patterns detected across {stocks_with_cup_handle} stocks")
    
    # Re-save chart files with pattern data for Priority1 stocks
    if pattern_count > 0 or cup_handle_count > 0:
        print(f"💾 Updating chart files with pattern data...")
        # Update all stocks that have patterns (either candlestick or cup and handle)
        symbols_to_update = set()
        if pattern_count > 0:
            symbols_to_update.update(priority1_set)
        if cup_handle_count > 0:
            symbols_to_update.update(all_stocks_symbols)
        
        for symbol in symbols_to_update:
            if symbol in chart_data_raw:
                final_chart_data[symbol] = chart_data_raw[symbol]
        
        # Save updated individual chart files
        updated_files = save_individual_chart_files(final_chart_data)
        print(f"✅ Updated {updated_files} chart files with pattern data")
    
    # Screen stocks to identify which ones pass
    results = screener.screen_stocks(stock_data)
    results.failed_tickers.extend(fetch_failed_tickers)
    
    # Display results
    results_manager.print_results(results)
    
    # Save results to JSON file for web display
    results_manager.save_to_json(results, len(all_tickers), "results.json", args.mode)
    
    # Fetch and save market sentiment data (Fear & Greed indices)
    print("\n📈 Fetching market sentiment data...")
    fetch_and_save_market_data()

if __name__ == "__main__":
    asyncio.run(main())
