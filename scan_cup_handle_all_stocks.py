"""
Cup and Handle Pattern Scanner
Analyzes all stocks in the charts directory and generates a comprehensive report
"""

import json
import os
from typing import Dict, List
from datetime import datetime
import csv
from candlestick_patterns import detect_cup_and_handle

def load_stock_data(stock_file: str) -> Dict:
    """Load stock data from JSON file"""
    try:
        with open(stock_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {stock_file}: {e}")
        return {}

def analyze_stock(symbol: str, data: Dict) -> Dict:
    """Analyze a single stock for cup and handle pattern"""
    try:
        # Extract OHLC data
        if 'dates' not in data or 'open' not in data:
            return None
        
        dates = data['dates']
        opens = data['open']
        highs = data['high']
        lows = data['low']
        closes = data['close']
        volumes = data['volume']
        
        # Detect cup and handle pattern
        pattern = detect_cup_and_handle(opens, highs, lows, closes, volumes, dates)
        
        return pattern
        
    except Exception as e:
        print(f"⚠️ Error analyzing {symbol}: {str(e)}")
        return None

def generate_comprehensive_report():
    """Scan all stocks and generate a comprehensive cup and handle report"""
    charts_dir = 'charts'
    
    if not os.path.exists(charts_dir):
        print(f"Error: {charts_dir} directory not found!")
        return
    
    # Get all JSON files
    json_files = [f for f in os.listdir(charts_dir) if f.endswith('.json') and f != '.gitkeep']
    
    print(f"\n{'='*80}")
    print(f"CUP AND HANDLE PATTERN SCANNER")
    print(f"{'='*80}")
    print(f"Scanning {len(json_files)} stocks for Cup and Handle patterns...")
    print(f"{'='*80}\n")
    
    all_patterns = []
    processed = 0
    
    for json_file in json_files:
        symbol = json_file.replace('.json', '')
        file_path = os.path.join(charts_dir, json_file)
        
        data = load_stock_data(file_path)
        if not data:
            continue
        
        pattern = analyze_stock(symbol, data)
        
        if pattern:
            pattern_info = {
                'stock_name': symbol,
                'cup_handle_price_line': pattern.get('rim_price', 'N/A'),
                'start_of_cup_date': pattern.get('cup_start_date', 'N/A'),
                'end_of_cup_date': pattern.get('cup_end_date', 'N/A'),
                'handle_start_date': pattern.get('handle_start_date', 'N/A'),
                'confirmation_date': pattern.get('breakout_date') if pattern.get('breakout_date') else 'Not confirmed yet',
                'handle_shape': pattern.get('handle_shape', 'N/A'),
                'cup_bottom_price': pattern.get('cup_bottom_price', 'N/A'),
                'handle_low': pattern.get('handle_low', 'N/A'),
                'depth_percent': pattern.get('depth_percent', 'N/A'),
                'profit_target': pattern.get('profit_target', 'N/A'),
                'risk_reward_ratio': pattern.get('risk_reward_ratio', 'N/A'),
                'status': pattern.get('status', 'N/A'),
                'confidence': pattern.get('confidence', 'N/A'),
                'days_ago': pattern.get('days_ago', 'N/A')
            }
            all_patterns.append(pattern_info)
            print(f"✅ {symbol}: Found {pattern['status']} pattern (confidence: {pattern.get('confidence', 'N/A')}%)")
        
        processed += 1
        if processed % 100 == 0:
            print(f"   Processed {processed}/{len(json_files)} stocks...")
    
    print(f"\n{'='*80}")
    print(f"SCAN COMPLETE")
    print(f"{'='*80}")
    print(f"Total patterns found: {len(all_patterns)}")
    print(f"Stocks scanned: {processed}")
    print(f"{'='*80}\n")
    
    # Generate CSV report
    if all_patterns:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f'cup_handle_report_{timestamp}.csv'
        
        # Write to CSV
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'stock_name',
                'cup_handle_price_line',
                'start_of_cup_date',
                'end_of_cup_date',
                'handle_start_date',
                'confirmation_date',
                'handle_shape',
                'cup_bottom_price',
                'handle_low',
                'depth_percent',
                'profit_target',
                'risk_reward_ratio',
                'status',
                'confidence',
                'days_ago'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_patterns)
        
        print(f"📄 CSV Report saved: {csv_filename}\n")
        
        # Print detailed table
        print("="*150)
        print("DETAILED CUP AND HANDLE PATTERN REPORT")
        print("="*150)
        print(f"{'Stock':<8} {'Price Line':<12} {'Cup Start':<12} {'Cup End':<12} {'Handle Date':<12} "
              f"{'Confirmation':<15} {'Status':<12} {'Confidence':<11} {'Days Ago':<10}")
        print("-"*150)
        
        for pattern in all_patterns:
            conf_date = pattern['confirmation_date'] if pattern['confirmation_date'] != 'Not confirmed yet' else 'Pending'
            print(f"{pattern['stock_name']:<8} {str(pattern['cup_handle_price_line']):<12} "
                  f"{pattern['start_of_cup_date']:<12} {pattern['end_of_cup_date']:<12} "
                  f"{pattern['handle_start_date']:<12} {conf_date:<15} {pattern['status']:<12} "
                  f"{str(pattern['confidence']):<11} {str(pattern['days_ago']):<10}")
        
        print("="*150)
        
        # Group by status
        confirmed = [p for p in all_patterns if p['status'] == 'confirmed']
        forming = [p for p in all_patterns if p['status'] == 'forming']
        
        print(f"\n📊 SUMMARY BY STATUS:")
        print(f"   ✅ Confirmed (breakout occurred): {len(confirmed)}")
        print(f"   🔄 Forming (handle forming): {len(forming)}")
        
    else:
        print("\n⚠️ No Cup and Handle patterns found in any stock files.")
        print("This could mean:")
        print("1. No patterns match the strict William O'Neil criteria")
        print("2. The market conditions don't currently favor cup and handle formations")
        print("3. The lookback period doesn't contain suitable patterns")

if __name__ == '__main__':
    generate_comprehensive_report()
