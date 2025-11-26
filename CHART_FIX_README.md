# Chart Viewer Fix Instructions

## Why Charts Aren't Showing

The chart viewer page requires `chart_data.json` to exist, but this file is only generated when `main.py` runs successfully.

## Solution

### Step 1: Commit and Push Changes
```powershell
git add .
git commit -m "Remove VIX integration and fix chart data generation"
git push origin main
```

### Step 2: Manually Run the Workflow
1. Go to: https://github.com/achikam-mor/stock-screener/actions
2. Click on your workflow (e.g., "Update Stock Data")
3. Click "Run workflow" button
4. Select the "main" branch
5. Click "Run workflow"

### Step 3: Wait for Completion
- The workflow takes about 10-15 minutes to complete
- It will generate:
  - `results.json` - Hot stocks and watch list
  - `chart_data.json` - OHLC data for ~1,700 stocks (**THIS IS WHAT CHARTS NEED**)

### Step 4: Verify Files Were Created
After the workflow completes:
1. Go to your repository: https://github.com/achikam-mor/stock-screener
2. Check that both `results.json` and `chart_data.json` exist in the root
3. Click on `chart_data.json` to verify it has data (should be a large JSON file)

### Step 5: Test Charts
1. Visit your GitHub Pages site: https://achikam-mor.github.io/stock-screener/
2. Go to the "📈 Charts" page
3. Try searching for a ticker like "AAPL" or "MSFT"
4. OR click a "📈 Launch Chart" button from hot stocks or watch list pages

## What Was Fixed

### Removed VIX Integration
- ✅ Removed VIX ticker from data fetching in `main.py`
- ✅ Removed VIX data extraction and JSON saving
- ✅ Removed VIX special handling in `data_loader.py`
- ✅ Removed VIX chart section from `market-overview.html`
- ✅ Removed VIX chart code from `market-overview.js`

### Chart Data Generation
- ✅ `chart_data.json` is still being generated with OHLC data for all stocks
- ✅ Chart viewer automatically loads data on page load
- ✅ "Launch Chart" buttons pass ticker via URL parameter
- ✅ Charts auto-load when ticker is in URL

## Troubleshooting

### If Charts Still Don't Show After Workflow Runs:

1. **Check Browser Console (F12)**:
   - Open chart-viewer.html
   - Press F12
   - Look for errors in Console tab
   - Common issues:
     - "Failed to fetch chart_data.json" = file doesn't exist yet
     - "chartData is null" = file exists but is empty
     - "No data available for SYMBOL" = stock wasn't analyzed

2. **Verify chart_data.json Exists**:
   ```
   https://achikam-mor.github.io/stock-screener/chart_data.json
   ```
   - Should return a large JSON file
   - Should have structure: `{"stocks": {...}, "last_updated": "..."}`

3. **Check File Size**:
   - chart_data.json should be 1-2 MB
   - If it's too small (< 100 KB), something went wrong during generation

4. **Run Workflow Again**:
   - Sometimes the first run after code changes has issues
   - Running it a second time often fixes problems

## Expected Behavior After Fix

✅ Workflow runs without VIX errors
✅ `chart_data.json` is generated successfully
✅ Charts page loads without errors
✅ Searching for a ticker displays the candlestick chart
✅ "Launch Chart" buttons work from hot stocks/watch list pages
✅ Charts load in < 1 second after data is cached

## Need More Help?

If charts still don't work after following these steps:
1. Check the workflow logs for errors
2. Verify chart_data.json was created and has valid JSON
3. Check browser console for JavaScript errors
4. Make sure you're testing on the deployed GitHub Pages site, not locally
