"""
Quick script to find all stocks with Golden Cross or Death Cross.
Run this after main.py has been executed to scan chart data.
"""

import os
import json

def find_crosses(charts_dir='charts'):
    golden_crosses = []
    death_crosses = []
    
    if not os.path.exists(charts_dir):
        print(f"Charts directory '{charts_dir}' not found. Run main.py first.")
        return
    
    for filename in os.listdir(charts_dir):
        if filename.endswith('.json'):
            symbol = filename[:-5]
            filepath = os.path.join(charts_dir, filename)
            
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    
                if data.get('golden_cross', False):
                    golden_crosses.append(symbol)
                if data.get('death_cross', False):
                    death_crosses.append(symbol)
            except (json.JSONDecodeError, IOError) as e:
                continue
    
    print("=" * 50)
    print(f"✨ GOLDEN CROSS ({len(golden_crosses)} stocks)")
    print("=" * 50)
    if golden_crosses:
        for symbol in sorted(golden_crosses):
            print(f"  {symbol}")
    else:
        print("  No stocks with golden cross found")
    
    print()
    print("=" * 50)
    print(f"💀 DEATH CROSS ({len(death_crosses)} stocks)")
    print("=" * 50)
    if death_crosses:
        for symbol in sorted(death_crosses):
            print(f"  {symbol}")
    else:
        print("  No stocks with death cross found")
    
    print()
    print(f"Total: {len(golden_crosses)} golden crosses, {len(death_crosses)} death crosses")
    
    return golden_crosses, death_crosses

if __name__ == '__main__':
    find_crosses()
