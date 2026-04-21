"""
One-time script to populate cup_and_handle_patterns in all existing chart files.
This script reads all chart JSON files and adds cup and handle pattern detection.
Run this ONCE to populate all existing chart files with cup and handle patterns.
"""

import json
import os
from typing import List, Dict
from candlestick_patterns import detect_cup_and_handle

def populate_cup_handle_patterns():
    """Populate cup and handle patterns for all existing chart files."""
    charts_dir = 'charts'
    
    if not os.path.exists(charts_dir):
        print(f"❌ Charts directory not found: {charts_dir}")
        return
    
    # Get all chart files
    chart_files = [f for f in os.listdir(charts_dir) if f.endswith('.json')]
    total_files = len(chart_files)
    
    print(f"📊 Found {total_files} chart files")
    print(f"☕ Starting cup and handle pattern detection...\n")
    
    updated_count = 0
    patterns_found = 0
    error_count = 0
    skipped_count = 0
    
    for i, filename in enumerate(chart_files, 1):
        symbol = filename.replace('.json', '')
        filepath = os.path.join(charts_dir, filename)
        
        try:
            # Read chart data
            with open(filepath, 'r') as f:
                chart_data = json.load(f)
            
            # Skip if already has cup_and_handle_patterns
            if 'cup_and_handle_patterns' in chart_data:
                skipped_count += 1
                if i % 100 == 0:
                    print(f"Progress: {i}/{total_files} ({(i/total_files*100):.1f}%) - {symbol} (skipped, already has patterns)")
                continue
            
            # Get OHLC data
            opens = chart_data.get('open', [])
            highs = chart_data.get('high', [])
            lows = chart_data.get('low', [])
            closes = chart_data.get('close', [])
            volumes = chart_data.get('volume', [])
            dates = chart_data.get('dates', [])
            
            # Check if we have enough data
            if len(closes) < 50:
                chart_data['cup_and_handle_patterns'] = []
                skipped_count += 1
                continue
            
            # Detect cup and handle pattern
            cup_handle_pattern = detect_cup_and_handle(opens, highs, lows, closes, volumes, dates)
            
            # Store pattern in chart data
            if cup_handle_pattern:
                chart_data['cup_and_handle_patterns'] = [cup_handle_pattern]
                patterns_found += 1
                print(f"✅ {symbol}: Found {cup_handle_pattern['status']} cup and handle pattern")
            else:
                chart_data['cup_and_handle_patterns'] = []
            
            # Save updated chart data
            with open(filepath, 'w') as f:
                json.dump(chart_data, f)
            
            updated_count += 1
            
            # Progress update every 100 files
            if i % 100 == 0:
                print(f"Progress: {i}/{total_files} ({(i/total_files*100):.1f}%) - {patterns_found} patterns found so far")
        
        except Exception as e:
            error_count += 1
            print(f"⚠️ Error processing {symbol}: {str(e)}")
            # Still write an empty array to avoid processing again
            try:
                chart_data['cup_and_handle_patterns'] = []
                with open(filepath, 'w') as f:
                    json.dump(chart_data, f)
            except:
                pass
    
    print(f"\n" + "="*60)
    print(f"✅ Cup and handle pattern population complete!")
    print(f"="*60)
    print(f"📊 Total files processed: {total_files}")
    print(f"✅ Files updated: {updated_count}")
    print(f"☕ Patterns found: {patterns_found}")
    print(f"⏭️  Files skipped (already had patterns): {skipped_count}")
    print(f"⚠️  Errors: {error_count}")
    print(f"="*60)

if __name__ == "__main__":
    print("="*60)
    print("  CUP AND HANDLE PATTERN POPULATION SCRIPT")
    print("  One-time script to populate all chart files")
    print("="*60)
    print("\n⚠️  WARNING: This will modify all chart JSON files!")
    print("⚠️  Make sure you have committed your changes to git first.\n")
    
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    
    if response == 'yes':
        populate_cup_handle_patterns()
    else:
        print("❌ Aborted.")
