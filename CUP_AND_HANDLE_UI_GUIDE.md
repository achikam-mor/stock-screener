# Cup and Handle Pattern - UI Guide

## Overview
The cup and handle pattern detection is now fully integrated into the UI, allowing you to easily find and filter stocks with confirmed or forming cup and handle patterns.

## Where to Find Cup and Handle Patterns

### 1. Visual Indicators on Stock Cards
Stocks with cup and handle patterns will show special icons next to their symbol:

- **☕✅** = Confirmed cup and handle (breakout already occurred)
- **🏺** = Forming cup and handle (handle is forming, waiting for breakout)

### 2. Filter Options
On the **Hot Stocks** and **Watch List** pages, you'll find a new "Cup & Handle" filter dropdown:

**Filter Options:**
- **All** - Show all stocks (default)
- **☕ Confirmed** - Only show stocks with confirmed cup and handle patterns
- **🏺 Forming** - Only show stocks with forming cup and handle patterns  
- **☕ Any C&H** - Show any stock with a cup and handle pattern (confirmed or forming)

## How to Use the Filters

### Example 1: Find Confirmed Cup and Handle Patterns
1. Go to **Hot Stocks** page
2. Set "Cup & Handle" filter to "☕ Confirmed"
3. You'll see only stocks that have had confirmed breakouts

### Example 2: Find Opportunities (Forming Patterns)
1. Go to **Watch List** page
2. Set "Cup & Handle" filter to "🏺 Forming"
3. These stocks are still forming the handle and haven't broken out yet - potential entry points!

### Example 3: Combine Multiple Filters
You can combine cup and handle filters with other criteria:
1. Set "Cup & Handle" to "☕ Confirmed"
2. Set "Cross" to "✨ Golden Cross"
3. Set "Volume" to "High (>1.5x)"
4. This shows confirmed cup and handle patterns with golden crosses and high volume

## Understanding the Icon Tooltips

Hover over any cup and handle icon (☕✅ or 🏺) to see detailed information:
- **Status**: Confirmed or Forming
- **Rim Price**: The breakout level (cup and handle price line)
- **Target Price**: Projected profit target based on cup depth
- **Potential Gain**: Expected percentage gain
- **Confidence**: Pattern confidence level (77-87%)
- **Date**: When breakout occurred (or "Forming" if not yet confirmed)

## Currently Detected Patterns

As of your last scan:
- **28 total cup and handle patterns found**
- **6 confirmed** (recent breakouts)
- **22 forming** (handles forming, awaiting breakouts)

### Top Confirmed Patterns:
1. **JEF** (Jefferies Financial) - Confirmed TODAY! Target: $81.12 (+25.5%)
2. **DBRG** (DigitalBridge) - Target: $17.46 (+32.3%)
3. **RKT** (Rocket Companies) - Target: $22.30 (+18.5%)
4. **AFRM** (Affirm Holdings) - Target: $97.61 (+23.6%)
5. **BURL** (Burlington Stores) - Target: $334.09 (+16.3%)
6. **RF** (Regions Financial) - Target: $31.52 (+16.8%)

## Pattern Quality
All patterns detected use strict William O'Neil criteria:
- Cup depth: 12-35%
- Cup duration: 30-300 days
- Proper rim symmetry
- Handle in upper half of cup
- Volume requirements met
- Confidence: 77-87%

## Next Steps

### To Update Data with Cup and Handle Patterns:
1. Run: `python main.py`  (scans all stocks and updates JSON files)
2. The UI will automatically display cup and handle patterns when you refresh

### To Generate a Report:
1. Run: `python scan_cup_handle_all_stocks.py`
2. Creates a CSV file with all patterns and their details
3. Useful for offline analysis and record-keeping

## Tips for Trading

1. **Confirmed Patterns** (☕✅):
   - Breakout already occurred
   - Consider these for momentum plays
   - Check volume on breakout day
   - Use rim price as your stop loss

2. **Forming Patterns** (🏺):
   - Handle is still forming
   - Set price alerts at the rim price
   - Wait for volume confirmation on breakout
   - These are pre-breakout opportunities

3. **Risk Management**:
   - Use handle low as your stop loss
   - Target price shows potential profit
   - Risk/reward ratio is calculated for you
   - Never risk more than 2% of your account on one trade

## Troubleshooting

**Q: I don't see any cup and handle icons?**
A: Run `python main.py` first to detect patterns and update the JSON files.

**Q: The filter shows "0 stocks"?**
A: Either no patterns were detected, or you need to run the main script to update data.

**Q: How often should I rescan?**
A: Run the scanner weekly or when you want to find new patterns with updated market data.

## Additional Resources
- Full CSV report: `cup_handle_report_YYYYMMDD_HHMMSS.csv`
- Pattern details: Hover over icons for tooltips
- Implementation docs: `CUP_AND_HANDLE_IMPLEMENTATION.md`
