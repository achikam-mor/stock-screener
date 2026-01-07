import json
from candlestick_patterns import detect_cup_and_handle

with open('charts/RKT.json', 'r') as f:
    data = json.load(f)

pattern = detect_cup_and_handle(
    data['open'],
    data['high'],
    data['low'],
    data['close'],
    data['volume'],
    data['dates']
)

if pattern:
    print("RKT Pattern DETECTED!")
    print(f"  Cup: {pattern['cup_start_date']} to {pattern['cup_end_date']}")
    print(f"  Handle: {pattern['handle_start_date']} to {pattern.get('breakout_date', 'forming')}")
    print(f"  Status: {pattern['status']}")
    print(f"  Confidence: {pattern['confidence']}%")
else:
    print("RKT Pattern NOT detected")
