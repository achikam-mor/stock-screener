import pandas as pd
import json
import os
from stock_analyzer import StockAnalyzer

def test_hood_levels():
    # Load HOOD data
    filepath = os.path.join('charts', 'HOOD.json')
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return

    with open(filepath, 'r') as f:
        data = json.load(f)

    # Create DataFrame
    df = pd.DataFrame({
        'High': data['high'],
        'Low': data['low'],
        'Close': data['close']
    })
    
    print(f"Loaded {len(df)} days of data for HOOD")
    print(f"Recent Close: {df['Close'].iloc[-1]}")
    
    # Run analyzer with debug prints
    analyzer = StockAnalyzer()
    
    # We need to manually replicate the logic to see WHY it fails
    # Parameters
    window = 5
    tolerance = 0.02
    max_crossings = 20
    min_touches = 2
    
    highs = df["High"]
    lows = df["Low"]
    
    # 1. Find Candidates
    rolling_max = highs.rolling(window=window*2+1, center=True).max()
    resistances = highs[highs == rolling_max].dropna()
    
    rolling_min = lows.rolling(window=window*2+1, center=True).min()
    supports = lows[lows == rolling_min].dropna()
    
    print(f"\nFound {len(resistances)} resistance candidates")
    print(f"Found {len(supports)} support candidates")
    
    all_levels = pd.concat([resistances, supports])
    levels_sorted = sorted(all_levels.values)
    
    # 2. Cluster
    clusters = []
    if levels_sorted:
        current_cluster = [levels_sorted[0]]
        for i in range(1, len(levels_sorted)):
            if levels_sorted[i] <= current_cluster[-1] * (1 + tolerance):
                current_cluster.append(levels_sorted[i])
            else:
                clusters.append(float(sum(current_cluster)/len(current_cluster)))
                current_cluster = [levels_sorted[i]]
        clusters.append(float(sum(current_cluster)/len(current_cluster)))
    
    print(f"\nIdentified {len(clusters)} clusters (potential levels)")
    
    # 3. Filter
    print("\n--- Filtering Analysis ---")
    valid_levels = []
    
    # Check specifically for levels around 124
    target_level = 124.0
    
    for level in clusters:
        crossings = ((lows < level) & (highs > level)).sum()
        
        upper_zone = level * (1 + tolerance/2)
        lower_zone = level * (1 - tolerance/2)
        touches = ((highs >= lower_zone) & (lows <= upper_zone)).sum()
        
        is_target = abs(level - target_level) < 2.0
        
        if is_target:
            print(f"Level {level:.2f}: Crossings={crossings}, Touches={touches}")
            if crossings > max_crossings:
                print(f"  -> REJECTED: Too many crossings ({crossings} > {max_crossings})")
            if touches < min_touches:
                print(f"  -> REJECTED: Not enough touches ({touches} < {min_touches})")
        
        if crossings <= max_crossings and touches >= min_touches:
            valid_levels.append(round(level, 2))
            if is_target:
                print("  -> ACCEPTED")

    print(f"\nFinal Valid Levels: {valid_levels}")

if __name__ == "__main__":
    test_hood_levels()
