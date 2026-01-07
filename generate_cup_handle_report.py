"""
Cup and Handle Pattern Report Generator
Scans all stock JSON files and generates a report with pattern details
"""

import json
import os
from typing import List, Dict
import csv
from datetime import datetime

def load_stock_data(stock_file: str) -> Dict:
    """Load stock data from JSON file"""
    try:
        with open(stock_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {stock_file}: {e}")
        return {}

def extract_cup_handle_data(symbol: str, data: Dict) -> List[Dict]:
    """Extract cup and handle pattern data from stock data"""
    patterns = []
    
    # Check if cup_and_handle_patterns exists in the data
    if 'cup_and_handle_patterns' in data and data['cup_and_handle_patterns']:
        for pattern in data['cup_and_handle_patterns']:
            pattern_info = {
                'stock_name': symbol,
                'cup_handle_price_line': pattern.get('rim_price', 'N/A'),
                'start_of_cup_date': pattern.get('cup_start_date', 'N/A'),
                'end_of_cup_date': pattern.get('cup_end_date', 'N/A'),
                'handle_date': pattern.get('handle_start_date', 'N/A'),
                'confirmation_date': pattern.get('breakout_date', 'Not confirmed yet'),
                'handle_shape': pattern.get('handle_shape', 'N/A'),
                'cup_bottom_price': pattern.get('cup_bottom_price', 'N/A'),
                'handle_low': pattern.get('handle_low', 'N/A'),
                'depth_percent': pattern.get('depth_percent', 'N/A'),
                'profit_target': pattern.get('profit_target', 'N/A'),
                'risk_reward_ratio': pattern.get('risk_reward_ratio', 'N/A'),
                'status': pattern.get('status', 'N/A'),
                'confidence': pattern.get('confidence', 'N/A')
            }
            patterns.append(pattern_info)
    
    return patterns

def generate_report():
    """Generate cup and handle pattern report for all stocks"""
    charts_dir = 'charts'
    
    if not os.path.exists(charts_dir):
        print(f"Error: {charts_dir} directory not found!")
        return
    
    # Get all JSON files
    json_files = [f for f in os.listdir(charts_dir) if f.endswith('.json') and f != '.gitkeep']
    
    print(f"Scanning {len(json_files)} stock files for Cup and Handle patterns...")
    
    all_patterns = []
    stocks_with_patterns = 0
    
    for json_file in json_files:
        symbol = json_file.replace('.json', '')
        file_path = os.path.join(charts_dir, json_file)
        
        data = load_stock_data(file_path)
        patterns = extract_cup_handle_data(symbol, data)
        
        if patterns:
            all_patterns.extend(patterns)
            stocks_with_patterns += 1
    
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
                'handle_date',
                'confirmation_date',
                'handle_shape',
                'cup_bottom_price',
                'handle_low',
                'depth_percent',
                'profit_target',
                'risk_reward_ratio',
                'status',
                'confidence'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_patterns)
        
        print(f"\n✅ Report generated: {csv_filename}")
        print(f"📊 Total patterns found: {len(all_patterns)}")
        print(f"📈 Stocks with Cup and Handle patterns: {stocks_with_patterns}")
        
        # Print summary to console
        print("\n" + "="*120)
        print("CUP AND HANDLE PATTERN REPORT")
        print("="*120)
        print(f"{'Stock':<8} {'Price Line':<12} {'Cup Start':<12} {'Cup End':<12} {'Handle Date':<12} {'Confirmation':<15} {'Status':<12}")
        print("-"*120)
        
        for pattern in all_patterns:
            conf_date = pattern['confirmation_date'] if pattern['confirmation_date'] != 'Not confirmed yet' else 'Pending'
            print(f"{pattern['stock_name']:<8} {str(pattern['cup_handle_price_line']):<12} "
                  f"{pattern['start_of_cup_date']:<12} {pattern['end_of_cup_date']:<12} "
                  f"{pattern['handle_date']:<12} {conf_date:<15} {pattern['status']:<12}")
        
        print("="*120)
        
    else:
        print("\n⚠️ No Cup and Handle patterns found in any stock files.")
        print("This could mean:")
        print("1. The pattern detection hasn't been run yet")
        print("2. No patterns match the strict criteria")
        print("3. The JSON files don't contain 'cup_and_handle_patterns' data")
        print("\nTo detect patterns, run: python main.py")

if __name__ == '__main__':
    generate_report()
