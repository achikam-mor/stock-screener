import json
from candlestick_patterns import detect_cup_formation

# Load RKT data
with open('charts/RKT.json', 'r') as f:
    data = json.load(f)

dates = data['dates']
opens = data['open']
highs = data['high']
lows = data['low']
closes = data['close']
volumes = data['volume']

# Test the specific cup we know exists
cup_start_idx = 358  # Oct 1, 2025
cup_end_idx = 401     # Dec 2, 2025

print(f"Testing cup from {dates[cup_start_idx]} to {dates[cup_end_idx]}")
print(f"Duration: {cup_end_idx - cup_start_idx} days")
print(f"Left rim high: {highs[cup_start_idx]:.2f}")
print(f"Right rim high: {highs[cup_end_idx]:.2f}")
print(f"Diff: {abs(highs[cup_start_idx] - highs[cup_end_idx]):.2f} ({abs(highs[cup_start_idx] - highs[cup_end_idx])/highs[cup_start_idx]*100:.2f}%)\n")

cup = detect_cup_formation(highs, lows, closes, cup_start_idx, cup_end_idx)

if cup:
    print("SUCCESS! Cup formation detected!")
    print(f"  Left rim: {dates[cup['left_rim_idx']]} at ${cup['left_rim_price']:.2f}")
    print(f"  Bottom: {dates[cup['cup_bottom_idx']]} at ${cup['cup_bottom_price']:.2f}")
    print(f"  Right rim: {dates[cup['right_rim_idx']]} at ${cup['right_rim_price']:.2f}")
    print(f"  Depth: {cup['depth_percent']:.2f}%")
    print(f"  Valid: {cup['is_valid']}")
else:
    print("FAILED! Cup formation NOT detected!")
    print("\nDebugging...")
    
    # Check each validation step manually
    duration = cup_end_idx - cup_start_idx
    print(f"1. Duration: {duration} (need >= 30) - {'PASS' if duration >= 30 else 'FAIL'}")
    
    # Left rim search
    search_end = cup_start_idx + duration // 3
    left_rim_price = max(highs[cup_start_idx:search_end+1])
    left_rim_idx = cup_start_idx + list(highs[cup_start_idx:search_end+1]).index(left_rim_price)
    print(f"2. Left rim: {dates[left_rim_idx]} at ${left_rim_price:.2f}")
    
    # Rim violations
    violations = [i for i in range(left_rim_idx + 1, cup_end_idx + 1) if highs[i] > left_rim_price * 1.02]
    print(f"3. Rim violations: {len(violations)} {'PASS' if len(violations) == 0 else 'FAIL'}")
    if violations:
        for v in violations[:3]:
            print(f"   - {dates[v]}: {highs[v]:.2f} > {left_rim_price * 1.02:.2f}")
    
    # Cup bottom
    cup_bottom_price = min(lows[left_rim_idx:cup_end_idx+1])
    cup_bottom_idx = left_rim_idx + list(lows[left_rim_idx:cup_end_idx+1]).index(cup_bottom_price)
    print(f"4. Cup bottom: {dates[cup_bottom_idx]} at ${cup_bottom_price:.2f}")
    
    # Right rim search
    candidates = []
    for i in range(cup_bottom_idx + 1, cup_end_idx + 1):
        diff_pct = abs(highs[i] - left_rim_price) / left_rim_price
        if diff_pct <= 0.03:
            candidates.append((i, highs[i], diff_pct))
    
    print(f"5. Right rim candidates (within 3%): {len(candidates)}")
    for idx, high, diff in sorted(candidates, key=lambda x: x[2])[:3]:
        print(f"   - {dates[idx]}: {high:.2f} (diff {diff*100:.2f}%)")
    
    if candidates:
        best_idx, best_high, best_diff = min(candidates, key=lambda x: x[2])
        print(f"6. Best right rim: {dates[best_idx]} at ${best_high:.2f}")
        
        # Check depth
        depth_percent = ((left_rim_price - cup_bottom_price) / left_rim_price) * 100
        print(f"7. Depth: {depth_percent:.2f}% (need 12-35%) - {'PASS' if 12 <= depth_percent <= 35 else 'FAIL'}")
    else:
        print(f"6. NO right rim candidates found!")

