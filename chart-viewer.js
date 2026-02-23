/**
 * Chart Viewer - Interactive Candlestick Charts with TradingView Lightweight Charts
 * Uses on-demand loading - individual stock files loaded only when requested
 * Enhanced with ATR/Volume display, fullscreen mode, volume sub-chart, and date range selector
 */

let stockList = null;  // List of available stocks
let currentChart = null;
let volumeChart = null;  // Volume sub-chart
let rsiChart = null;     // RSI sub-chart
let rsChart = null;      // Relative Strength vs SPY sub-chart
let resultsData = null;
let chartCache = {};  // Cache for loaded chart data
let currentTicker = null;  // Currently displayed ticker
let currentDateRange = 260;  // Default to 1 year (260 trading days)
let currentChartData = null;  // Store current chart data for re-rendering
let sectorsData = null;  // Sectors lookup data

// Shared crosshair state for synced vertical pointer across all charts
let sharedCrosshair = { dateIndex: -1, visible: false };

/**
 * Sync crosshair plugin for sub-charts (volume, RSI, RS).
 * Draws a vertical line at the same date index as the main chart crosshair.
 * Also allows hovering on sub-charts to broadcast back to the main chart.
 */
const syncCrosshairPlugin = {
    id: 'syncCrosshair',
    afterEvent(chart, args) {
        const { event } = args;
        const { x } = event;
        const inChartArea = args.inChartArea;

        if (event.type === 'mouseout') {
            sharedCrosshair.visible = false;
            sharedCrosshair.dateIndex = -1;
            // Redraw all charts to clear crosshair
            requestAnimationFrame(() => {
                if (currentChart) currentChart.draw();
                if (volumeChart) volumeChart.draw();
                if (rsiChart) rsiChart.draw();
                if (rsChart) rsChart.draw();
            });
            args.changed = true;
            return;
        }

        if (inChartArea && chart.scales.x) {
            // Find the label index under the cursor
            const xScale = chart.scales.x;
            const labelIndex = Math.round(xScale.getValueForPixel(x));
            const labels = chart.data.labels;
            if (labelIndex >= 0 && labelIndex < labels.length) {
                sharedCrosshair.dateIndex = labelIndex;
                sharedCrosshair.visible = true;
                // Trigger redraw on all charts
                requestAnimationFrame(() => {
                    if (currentChart) currentChart.draw();
                    if (volumeChart && volumeChart !== chart) volumeChart.draw();
                    if (rsiChart && rsiChart !== chart) rsiChart.draw();
                    if (rsChart && rsChart !== chart) rsChart.draw();
                });
                args.changed = true;
            }
        }
    },
    afterDatasetsDraw(chart) {
        if (!sharedCrosshair.visible || sharedCrosshair.dateIndex < 0) return;
        const { ctx, chartArea: { top, bottom }, scales: { x } } = chart;
        if (!x) return;
        const xPos = x.getPixelForValue(sharedCrosshair.dateIndex);
        if (xPos < chart.chartArea.left || xPos > chart.chartArea.right) return;

        ctx.save();
        ctx.beginPath();
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 5]);
        ctx.strokeStyle = '#94a3b8';
        ctx.moveTo(xPos, top);
        ctx.lineTo(xPos, bottom);
        ctx.stroke();
        ctx.restore();
    }
};

// Load stock list on page load (small file, loads instantly)
document.addEventListener('DOMContentLoaded', async () => {
    console.log('[Chart Viewer] Initializing...');
    
    // Load results.json to check filtered stocks
    try {
        const resultsResponse = await fetch('results.json');
        if (resultsResponse.ok) {
            resultsData = await resultsResponse.json();
            console.log('[Chart Viewer] Results data loaded');
        }
    } catch (error) {
        console.log('[Chart Viewer] Could not load results.json:', error);
    }
    
    // Load sectors data for sector display
    try {
        const sectorsResponse = await fetch('sectors.json');
        if (sectorsResponse.ok) {
            sectorsData = await sectorsResponse.json();
            console.log('[Chart Viewer] Sectors data loaded');
        }
    } catch (error) {
        console.log('[Chart Viewer] Could not load sectors.json:', error);
    }
    
    try {
        // Load only the stock list (tiny file) - not all chart data
        const response = await fetch('stock-list.json');
        if (response.ok) {
            const data = await response.json();
            stockList = data.symbols;
            
            // Update timestamp
            if (data.last_updated) {
                const date = new Date(data.last_updated);
                const lastUpdatedEl = document.getElementById('last-updated');
                if (lastUpdatedEl) {
                    lastUpdatedEl.textContent = `Last updated: ${date.toLocaleString()}`;
                }
            } else {
                const lastUpdatedEl = document.getElementById('last-updated');
                if (lastUpdatedEl) {
                    lastUpdatedEl.textContent = 'Ready to search';
                }
            }
            
            // Check if stock list is empty
            if (!stockList || stockList.length === 0) {
                const lastUpdatedEl = document.getElementById('last-updated');
                if (lastUpdatedEl) {
                    lastUpdatedEl.textContent = 'No chart data available yet';
                }
                console.log('[Chart Viewer] Stock list is empty');
            } else {
                console.log(`[Chart Viewer] Stock list loaded: ${stockList.length} stocks available`);
            }
            
            console.log('[Chart Viewer] Stock list loaded successfully');
            
            // Check if ticker is in URL parameter and auto-load
            const urlParams = new URLSearchParams(window.location.search);
            const ticker = urlParams.get('ticker');
            if (ticker) {
                console.log('[Chart Viewer] Auto-loading chart for ticker:', ticker);
                document.getElementById('chart-ticker-search').value = ticker.toUpperCase();
                // Small delay to ensure DOM is fully ready
                setTimeout(() => {
                    loadChart();
                }, 100);
            }
        } else {
            const lastUpdatedEl = document.getElementById('last-updated');
            if (lastUpdatedEl) {
                lastUpdatedEl.textContent = 'Stock list not found';
            }
            console.error('[Chart Viewer] Stock list file not found');
        }
    } catch (error) {
        console.error('[Chart Viewer] Error loading stock list:', error);
        const lastUpdatedEl = document.getElementById('last-updated');
        if (lastUpdatedEl) {
            lastUpdatedEl.textContent = 'Error loading stock list';
        }
        showNotification('Stock list unavailable. Please run the workflow to generate data.', 'error');
    }
    
    // Handle Enter key in search box
    document.getElementById('chart-ticker-search').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            loadChart();
        }
    });
    
    // Initialize date range selector
    initDateRangeSelector();
    
    // Listen for fullscreen changes
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
});

/**
 * Initialize date range selector buttons
 */
function initDateRangeSelector() {
    const rangeButtons = document.querySelectorAll('.range-btn');
    rangeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const range = parseInt(btn.dataset.range);
            console.log(`[Chart Viewer] Date range changed to: ${range === 0 ? 'ALL' : range + ' days'}`);
            
            // Update active state
            rangeButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update current range and re-render chart
            currentDateRange = range;
            if (currentChartData && currentTicker) {
                displayCandlestickChart(currentTicker, currentChartData);
            }
        });
    });
}

/**
 * Load and display chart for the searched ticker (on-demand)
 */
async function loadChart() {
    const ticker = document.getElementById('chart-ticker-search').value.trim().toUpperCase();
    
    if (!ticker) {
        showNotification('Please enter a ticker symbol', 'error');
        return;
    }
    
    if (!stockList) {
        showNotification('Stock list not loaded yet. Please wait...', 'error');
        return;
    }
    
    // Check if stock exists in our list
    if (!stockList.includes(ticker)) {
        // Check if stock was filtered by screening criteria
        if (resultsData && resultsData.filtered_by_sma && resultsData.filtered_by_sma.includes(ticker)) {
            showNotification(`${ticker} was filtered out by our SMA/investing strategy and does not meet the screening criteria.`, 'info');
        } else if (resultsData && resultsData.failed_tickers && resultsData.failed_tickers.includes(ticker)) {
            showNotification(`${ticker} data fetch failed. Please try again later.`, 'error');
        } else {
            showNotification(`No chart data available for ${ticker}. Stock may not have been analyzed or does not meet screening criteria.`, 'error');
        }
        document.getElementById('chart-section').style.display = 'none';
        return;
    }
    
    // Show loading message
    showNotification(`Loading chart for ${ticker}...`, 'success');
    
    // Check cache first
    if (chartCache[ticker]) {
        currentTicker = ticker;
        currentChartData = chartCache[ticker];
        displayCandlestickChart(ticker, chartCache[ticker]);
        return;
    }
    
    // Fetch individual stock data on-demand
    try {
        const response = await fetch(`charts/${ticker}.json`);
        if (response.ok) {
            const chartData = await response.json();
            chartCache[ticker] = chartData;  // Cache for future use
            currentTicker = ticker;
            currentChartData = chartData;
            console.log(`[Chart Viewer] Chart data loaded for ${ticker}:`, {
                dataPoints: chartData.dates?.length || 0,
                hasATR: chartData.atr !== undefined,
                hasVolume: chartData.last_volume !== undefined
            });
            displayCandlestickChart(ticker, chartData);
        } else {
            showNotification(`Could not load chart data for ${ticker}`, 'error');
            document.getElementById('chart-section').style.display = 'none';
        }
    } catch (error) {
        console.error(`[Chart Viewer] Error loading chart for ${ticker}:`, error);
        showNotification(`Error loading chart for ${ticker}. Please try again.`, 'error');
        document.getElementById('chart-section').style.display = 'none';
    }
}

/**
 * Display candlestick chart using Chart.js with Financial plugin
 */
function displayCandlestickChart(ticker, data) {
    const chartSection = document.getElementById('chart-section');
    chartSection.style.display = 'block';
    
    // Update chart title with favorite star
    const chartTitleEl = document.getElementById('chart-title');
    const isFav = isFavorite(ticker);
    chartTitleEl.innerHTML = `
        <span class="favorite-star chart-favorite-star ${isFav ? 'is-favorite' : ''}" 
              data-ticker="${ticker}" 
              onclick="toggleFavorite('${ticker}', event)"
              title="${isFav ? 'Remove from favorites' : 'Add to favorites'}">
            ${isFav ? '★' : '☆'}
        </span>
        ${ticker} - Candlestick Chart
    `;
    
    // Determine data range based on currentDateRange setting
    const maxDays = currentDateRange === 0 ? data.dates.length : currentDateRange;
    const startIndex = Math.max(0, data.dates.length - maxDays);
    const dates = data.dates.slice(startIndex);
    const opens = data.open.slice(startIndex);
    const highs = data.high.slice(startIndex);
    const lows = data.low.slice(startIndex);
    const closes = data.close.slice(startIndex);
    const volumes = data.volume.slice(startIndex);
    const sma50Values = data.sma50 ? data.sma50.slice(startIndex) : [];
    const sma150Values = data.sma150 ? data.sma150.slice(startIndex) : [];
    const sma200Values = data.sma200 ? data.sma200.slice(startIndex) : [];
    
    // Update period label
    const periodLabels = { 21: '1 Month', 63: '3 Months', 126: '6 Months', 260: '1 Year', 0: 'All Time' };
    document.getElementById('chart-period').textContent = periodLabels[currentDateRange] || 'Custom';
    document.getElementById('chart-data-points').textContent = `${dates.length} trading days`;
    
    // Calculate statistics for displayed period
    const currentPrice = closes[closes.length - 1];
    const periodHigh = Math.max(...highs);
    const periodLow = Math.min(...lows);
    const avgVolume = Math.round(volumes.reduce((a, b) => a + b, 0) / volumes.length);
    
    // Update basic statistics
    document.getElementById('current-price').textContent = `$${currentPrice.toFixed(2)}`;
    document.getElementById('period-high').textContent = `$${periodHigh.toFixed(2)}`;
    document.getElementById('period-low').textContent = `$${periodLow.toFixed(2)}`;
    
    // Calculate and display SMA150 and distance
    const currentSMA150 = sma150Values.length > 0 ? sma150Values[sma150Values.length - 1] : null;
    if (currentSMA150 !== null) {
        document.getElementById('current-sma150').textContent = `$${currentSMA150.toFixed(2)}`;
        const distance = ((currentPrice - currentSMA150) / currentSMA150) * 100;
        const distanceEl = document.getElementById('sma150-distance');
        distanceEl.textContent = `${distance >= 0 ? '+' : ''}${distance.toFixed(2)}%`;
        // Color based on whether it meets the ±4% criteria
        if (Math.abs(distance) <= 4) {
            distanceEl.style.color = '#10b981'; // Green - within criteria
        } else {
            distanceEl.style.color = '#f59e0b'; // Amber - outside criteria
        }
    } else {
        document.getElementById('current-sma150').textContent = 'N/A';
        document.getElementById('sma150-distance').textContent = 'N/A';
    }
    
    // Display ATR metrics (from chart JSON or calculate fallback)
    const atrValue = data.atr ?? calculateATRFallback(highs, lows, closes);
    const atrPercent = data.atr_percent ?? (atrValue ? (atrValue / currentPrice * 100) : null);
    
    if (atrValue !== null) {
        document.getElementById('current-atr').textContent = `$${atrValue.toFixed(2)}`;
        document.getElementById('atr-percent').textContent = `${atrPercent.toFixed(2)}%`;
        // Color ATR based on volatility level
        const atrPercentEl = document.getElementById('atr-percent');
        if (atrPercent < 2) {
            atrPercentEl.style.color = '#10b981'; // Green - low volatility
        } else if (atrPercent < 4) {
            atrPercentEl.style.color = '#f59e0b'; // Amber - moderate volatility
        } else {
            atrPercentEl.style.color = '#ef4444'; // Red - high volatility
        }
    } else {
        document.getElementById('current-atr').textContent = 'N/A';
        document.getElementById('atr-percent').textContent = 'N/A';
    }
    
    // Display volume metrics
    const lastVolume = data.last_volume ?? volumes[volumes.length - 1];
    const avgVolume14d = data.avg_volume_14d ?? avgVolume;
    const volumeRatio = avgVolume14d > 0 ? (lastVolume / avgVolume14d) : 0;
    
    document.getElementById('today-volume').textContent = formatVolume(lastVolume);
    document.getElementById('avg-volume').textContent = formatVolume(avgVolume14d);
    
    const volumeRatioEl = document.getElementById('volume-ratio');
    volumeRatioEl.textContent = `${volumeRatio.toFixed(2)}x`;
    // Color volume ratio
    if (volumeRatio > 1.5) {
        volumeRatioEl.style.color = '#10b981'; // Green - high volume
    } else if (volumeRatio < 0.5) {
        volumeRatioEl.style.color = '#ef4444'; // Red - low volume
    } else {
        volumeRatioEl.style.color = '#94a3b8'; // Gray - normal
    }
    
    // Color current price based on change
    const priceChange = data.close[data.close.length - 1] - data.close[0];
    document.getElementById('current-price').style.color = priceChange >= 0 ? '#10b981' : '#ef4444';
    
    // Display sector
    const sectorEl = document.getElementById('stock-sector');
    if (sectorEl) {
        const sector = (sectorsData && sectorsData.stocks && sectorsData.stocks[ticker]) || 'Unknown';
        sectorEl.textContent = sector;
    }
    
    // Update TradingView link
    const tvContainer = document.getElementById('tradingview-link-container');
    const tvLink = document.getElementById('tradingview-link');
    if (tvContainer && tvLink) {
        tvLink.href = `https://www.tradingview.com/chart/?symbol=${encodeURIComponent(ticker)}`;
        tvLink.textContent = `📊 View ${ticker} on TradingView`;
        tvContainer.style.display = 'block';
    }
    
    // Destroy existing chart if any
    if (currentChart) {
        currentChart.destroy();
        currentChart = null;
    }
    
    // Get canvas and context
    const canvas = document.getElementById('candlestickChart');
    const ctx = canvas.getContext('2d');
    
    // Define custom free-moving crosshair plugin
    const freeCrosshairPlugin = {
        id: 'freeCrosshair',
        afterInit(chart) {
            chart.crosshair = { x: 0, y: 0, visible: false };
        },
        afterEvent(chart, args) {
            const { inChartArea } = args;
            const { x, y } = args.event;
            
            if (args.event.type === 'mouseout') {
                chart.crosshair = { x: 0, y: 0, visible: false };
                sharedCrosshair.visible = false;
                sharedCrosshair.dateIndex = -1;
                requestAnimationFrame(() => {
                    if (volumeChart) volumeChart.draw();
                    if (rsiChart) rsiChart.draw();
                    if (rsChart) rsChart.draw();
                });
                args.changed = true;
                return;
            }
            
            chart.crosshair = { x, y, visible: inChartArea };
            
            // Sync with sub-charts: find the date index under cursor
            if (inChartArea && chart.scales.x) {
                const timestamp = chart.scales.x.getValueForPixel(x);
                // Find the closest date index in the sliced dates array
                let closestIdx = 0;
                let minDiff = Infinity;
                for (let i = 0; i < dates.length; i++) {
                    const diff = Math.abs(new Date(dates[i]).getTime() - timestamp);
                    if (diff < minDiff) {
                        minDiff = diff;
                        closestIdx = i;
                    }
                }
                sharedCrosshair.dateIndex = closestIdx;
                sharedCrosshair.visible = true;
                // Trigger redraw on sub-charts
                requestAnimationFrame(() => {
                    if (volumeChart) volumeChart.draw();
                    if (rsiChart) rsiChart.draw();
                    if (rsChart) rsChart.draw();
                });
            }
            
            args.changed = true; // Force redraw
        },
        afterDatasetsDraw(chart, args, options) {
            const { ctx, chartArea: { left, right, top, bottom }, scales: { x, y } } = chart;
            
            // If sub-chart triggered the crosshair, draw vertical line from shared state
            if (!chart.crosshair.visible && sharedCrosshair.visible && sharedCrosshair.dateIndex >= 0) {
                const dateStr = dates[sharedCrosshair.dateIndex];
                if (dateStr) {
                    const ts = new Date(dateStr).getTime();
                    const xPos = x.getPixelForValue(ts);
                    if (xPos >= left && xPos <= right) {
                        ctx.save();
                        ctx.beginPath();
                        ctx.lineWidth = 1;
                        ctx.setLineDash([5, 5]);
                        ctx.strokeStyle = '#94a3b8';
                        ctx.moveTo(xPos, top);
                        ctx.lineTo(xPos, bottom);
                        ctx.stroke();
                        ctx.restore();
                    }
                }
                return;
            }
            
            if (!chart.crosshair.visible) return;
            
            const xPos = chart.crosshair.x;
            const yPos = chart.crosshair.y;
            
            ctx.save();
            ctx.beginPath();
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 5]);
            ctx.strokeStyle = '#94a3b8';
            
            // Draw vertical line
            ctx.moveTo(xPos, top);
            ctx.lineTo(xPos, bottom);
            
            // Draw horizontal line
            ctx.moveTo(left, yPos);
            ctx.lineTo(right, yPos);
            ctx.stroke();
            
            // Draw Y-axis label (Price)
            const price = y.getValueForPixel(yPos);
            const priceLabel = price.toFixed(2);
            
            ctx.fillStyle = '#1e293b';
            ctx.fillRect(right, yPos - 10, 50, 20);
            ctx.fillStyle = '#ffffff';
            ctx.font = '11px sans-serif';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            ctx.fillText(priceLabel, right + 5, yPos);
            
            // Draw X-axis label (Date)
            const timestamp = x.getValueForPixel(xPos);
            const date = new Date(timestamp);
            const dateLabel = date.toLocaleDateString();
            
            const textWidth = ctx.measureText(dateLabel).width;
            ctx.fillStyle = '#1e293b';
            ctx.fillRect(xPos - textWidth / 2 - 5, bottom, textWidth + 10, 20);
            ctx.fillStyle = '#ffffff';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.fillText(dateLabel, xPos, bottom + 5);
            
            ctx.restore();
        }
    };

    // Custom plugin to draw dynamic support and resistance levels with history-based coloring
    const keyLevelsPlugin = {
        id: 'keyLevels',
        beforeDatasetsDraw(chart, args, options) {
            // Check if enabled
            const checkbox = document.getElementById('sr-checkbox');
            if (checkbox && !checkbox.checked) return;

            const { ctx, chartArea: { left, right, top, bottom }, scales: { x, y } } = chart;
            
            // Get candlestick dataset
            const datasets = chart.data.datasets;
            if (!datasets || datasets.length === 0) return;
            
            // Find candlestick dataset
            const candleDataset = datasets.find(d => d.type === 'candlestick');
            if (!candleDataset || !candleDataset.data || candleDataset.data.length === 0) return;
            
            const candles = candleDataset.data;
            
            if (data.key_levels && data.key_levels.length > 0) {
                ctx.save();
                ctx.lineWidth = 1;
                ctx.setLineDash([5, 5]); // Dashed line
                
                // Optimization: Find visible candles range once
                const minTime = x.getValueForPixel(left);
                
                // Find start index (include one before left edge for continuity)
                let startIndex = candles.findIndex(c => c.x >= minTime);
                if (startIndex === -1) startIndex = 0;
                if (startIndex > 0) startIndex--;
                
                data.key_levels.forEach(level => {
                    const yPos = y.getPixelForValue(level);
                    
                    // Only draw if visible in Y axis
                    if (yPos < top || yPos > bottom) return;
                    
                    let currentPathColor = null;
                    
                    // Helper to start a new segment
                    const startSegment = (color, xStart) => {
                        if (currentPathColor) {
                            ctx.stroke();
                        }
                        ctx.beginPath();
                        ctx.strokeStyle = color;
                        ctx.moveTo(xStart, yPos);
                        currentPathColor = color;
                    };
                    
                    // Determine initial color based on the first visible candle
                    const firstCandle = candles[startIndex];
                    // If price > level, it's Support (Green). If price < level, it's Resistance (Red).
                    const initialIsSupport = firstCandle.c > level;
                    const initialColor = initialIsSupport ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)';
                    
                    // Start drawing from the left edge
                    startSegment(initialColor, left);
                    
                    // Iterate through visible candles to check for crossovers
                    for (let i = startIndex; i < candles.length; i++) {
                        const candle = candles[i];
                        const candleX = x.getPixelForValue(candle.x);
                        
                        // Stop if we are past the right edge
                        if (candleX > right) break;
                        
                        const isSupport = candle.c > level;
                        const color = isSupport ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)';
                        
                        // If state changes, end current segment and start new one
                        if (color !== currentPathColor) {
                            ctx.lineTo(candleX, yPos);
                            startSegment(color, candleX);
                        }
                    }
                    
                    // Finish line to the right edge
                    ctx.lineTo(right, yPos);
                    ctx.stroke();
                });
                ctx.restore();
            }
        }
    };
    
    // Prepare candlestick data - using sliced arrays
    const candlestickData = dates.map((date, i) => ({
        x: new Date(date).getTime(), // Convert to timestamp
        o: opens[i],
        h: highs[i],
        l: lows[i],
        c: closes[i]
    }));
    
    // Prepare SMA data
    const sma50Data = dates
        .map((date, i) => ({
            x: new Date(date).getTime(),
            y: sma50Values && sma50Values[i] !== null ? sma50Values[i] : null
        }))
        .filter(point => point.y !== null);

    const sma150Data = dates
        .map((date, i) => ({
            x: new Date(date).getTime(),
            y: sma150Values && sma150Values[i] !== null ? sma150Values[i] : null
        }))
        .filter(point => point.y !== null);

    const sma200Data = dates
        .map((date, i) => ({
            x: new Date(date).getTime(),
            y: sma200Values && sma200Values[i] !== null ? sma200Values[i] : null
        }))
        .filter(point => point.y !== null);
    
    // Calculate Y-axis range with padding
    const priceMin = periodLow * 0.98; // 2% padding below
    const priceMax = periodHigh * 1.02; // 2% padding above
    
    // Create candlestick chart
    try {
        currentChart = new Chart(ctx, {
            type: 'candlestick',
            data: {
                datasets: [
                    {
                        label: ticker,
                        type: 'candlestick',
                        data: candlestickData,
                        color: {
                            up: '#10b981',
                            down: '#ef4444',
                            unchanged: '#6b7280'
                        },
                        borderColor: {
                            up: '#10b981',
                            down: '#ef4444',
                            unchanged: '#6b7280'
                        },
                        order: 4
                    },
                    {
                        label: 'SMA50',
                        type: 'line',
                        data: sma50Data,
                        borderColor: '#3b82f6',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        tension: 0.1,
                        hidden: !document.getElementById('sma50-checkbox').checked,
                        order: 3
                    },
                    {
                        label: 'SMA150',
                        type: 'line',
                        data: sma150Data,
                        borderColor: '#eab308',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        tension: 0.1,
                        hidden: !document.getElementById('sma150-checkbox').checked,
                        order: 2
                    },
                    {
                        label: 'SMA200',
                        type: 'line',
                        data: sma200Data,
                        borderColor: '#a855f7',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        tension: 0.1,
                        hidden: !document.getElementById('sma200-checkbox').checked,
                        order: 1
                    }
                ]
            },
            plugins: [freeCrosshairPlugin, keyLevelsPlugin],
            options: {
                responsive: true,
                maintainAspectRatio: false,
                parsing: false, // Data is already in correct format
                interaction: {
                    mode: 'nearest',
                    intersect: true,
                    axis: 'x'
                },
                plugins: {
                    crosshair: false,
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'nearest',
                        intersect: true,
                        backgroundColor: 'rgba(30, 41, 59, 0.95)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#f1f5f9',
                        borderColor: '#334155',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            title: function(context) {
                                const date = new Date(context[0].parsed.x);
                                return date.toLocaleDateString();
                            },
                            label: function(context) {
                                const data = context.raw;
                                if (data.o !== undefined) {
                                    // Candlestick data
                                    const change = data.c - data.o;
                                    const changePct = (change / data.o * 100).toFixed(2);
                                    return [
                                        `Open: $${data.o.toFixed(2)}`,
                                        `High: $${data.h.toFixed(2)}`,
                                        `Low: $${data.l.toFixed(2)}`,
                                        `Close: $${data.c.toFixed(2)}`,
                                        `Change: $${change.toFixed(2)} (${changePct}%)`
                                    ];
                                } else if (context.dataset.label.startsWith('SMA')) {
                                    // SMA line data
                                    return `${context.dataset.label}: $${data.y.toFixed(2)}`;
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'MMM dd'
                            }
                        },
                        grid: {
                            color: '#334155',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            maxRotation: 45,
                            minRotation: 45
                        }
                    },
                    y: {
                        position: 'right',
                        min: priceMin,
                        max: priceMax,
                        grid: {
                            color: '#334155',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                }
            }
        });
        
        console.log(`Chart created successfully for ${ticker} with ${candlestickData.length} candles`);
        
        // Add candlestick pattern markers if available
        if (data.candlestick_patterns && data.candlestick_patterns.length > 0) {
            addPatternMarkers(data.candlestick_patterns, dates, highs, lows);
        }
        
    } catch (error) {
        console.error('Error creating chart:', error);
        console.error('Error details:', error.message);
        showNotification('Error displaying chart. Please check console for details.', 'error');
        return;
    }
    
    // Scroll to chart
    chartSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}/**
 * Format volume number
 */
function formatVolume(volume) {
    if (volume >= 1000000000) {
        return (volume / 1000000000).toFixed(2) + 'B';
    } else if (volume >= 1000000) {
        return (volume / 1000000).toFixed(2) + 'M';
    } else if (volume >= 1000) {
        return (volume / 1000).toFixed(2) + 'K';
    }
    return volume.toString();
}

/**
 * Add candlestick pattern markers to the chart
 */
function addPatternMarkers(patterns, dates, highs, lows) {
    if (!currentChart || !patterns || patterns.length === 0) return;
    
    const canvas = document.getElementById('candlestickChart');
    const existingOverlay = document.getElementById('pattern-markers-overlay');
    if (existingOverlay) {
        existingOverlay.remove();
    }
    
    // Create overlay container for pattern markers
    const overlay = document.createElement('div');
    overlay.id = 'pattern-markers-overlay';
    overlay.style.position = 'absolute';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.pointerEvents = 'none';
    overlay.style.zIndex = '10';
    
    canvas.parentElement.style.position = 'relative';
    canvas.parentElement.appendChild(overlay);
    
    // Map pattern dates to chart positions
    patterns.forEach(pattern => {
        const dateIndex = dates.findIndex(d => d === pattern.date);
        if (dateIndex === -1) return;
        
        // Get chart coordinates for this date
        const chartArea = currentChart.chartArea;
        const xScale = currentChart.scales.x;
        const yScale = currentChart.scales.y;
        
        if (!xScale || !yScale) return;
        
        const dateObj = new Date(pattern.date);
        const xPos = xScale.getPixelForValue(dateObj.getTime());
        
        // Position marker near the bottom of the chart (above X-axis)
        // Use a fixed position relative to the chart area bottom
        const yPos = chartArea.bottom - 10;
        
        // Create marker element
        const marker = document.createElement('div');
        marker.className = 'pattern-marker';
        marker.style.position = 'absolute';
        marker.style.left = `${xPos}px`;
        marker.style.top = `${yPos}px`;
        marker.style.transform = 'translate(-50%, -50%)';
        marker.style.pointerEvents = 'auto';
        marker.style.cursor = 'help';
        marker.style.width = '10px';
        marker.style.height = '10px';
        marker.style.borderRadius = '50%';
        marker.style.border = '1px solid white';
        marker.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.5)';
        marker.style.zIndex = '20';
        
        // Color based on signal and status
        if (pattern.signal === 'bullish' && pattern.status === 'confirmed') {
            marker.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
        } else if (pattern.signal === 'bullish' && pattern.status === 'pending') {
            marker.style.background = 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)';
        } else if (pattern.signal === 'bearish' && pattern.status === 'pending') {
            marker.style.background = 'linear-gradient(135deg, #fb923c 0%, #f97316 100%)';
        } else if (pattern.signal === 'bearish' && pattern.status === 'confirmed') {
            marker.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
        }
        
        // Format pattern name for display
        const displayName = pattern.pattern.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const statusIcon = pattern.status === 'confirmed' ? '✅' : '⏳';
        
        // Tooltip with date
        const tooltip = `${displayName}\nDate: ${pattern.date}\n${pattern.signal.charAt(0).toUpperCase() + pattern.signal.slice(1)} ${statusIcon}\n${pattern.status.charAt(0).toUpperCase() + pattern.status.slice(1)}\nConfidence: ${pattern.confidence}%`;
        marker.title = tooltip;
        
        overlay.appendChild(marker);
    });
    
    console.log(`Added ${patterns.length} pattern markers to chart`);
}

/**
 * Show notification message
 */
function showNotification(message, type) {
    const notification = document.getElementById('chart-notification');
    notification.textContent = message;
    notification.className = `search-notification ${type}`;
    notification.style.display = 'flex';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 5000);
}

/**
 * Toggle SMA visibility
 */
function toggleSMA(smaType) {
    if (!currentChart) return;
    
    const checkbox = document.getElementById(`${smaType}-checkbox`);
    const isChecked = checkbox.checked;
    
    // Find dataset index based on label
    const datasetIndex = currentChart.data.datasets.findIndex(d => d.label.toLowerCase() === smaType.toLowerCase());
    
    if (datasetIndex !== -1) {
        currentChart.setDatasetVisibility(datasetIndex, isChecked);
        currentChart.update();
    }
}

/**
 * Toggle Key Levels visibility
 */
function toggleKeyLevels() {
    if (currentChart) {
        currentChart.update();
    }
}

/**
 * Calculate ATR fallback from OHLC data (client-side calculation)
 */
function calculateATRFallback(highs, lows, closes, window = 14) {
    if (highs.length < window + 1) return null;
    
    const trueRanges = [];
    for (let i = 1; i < highs.length; i++) {
        const highLow = highs[i] - lows[i];
        const highPrevClose = Math.abs(highs[i] - closes[i - 1]);
        const lowPrevClose = Math.abs(lows[i] - closes[i - 1]);
        trueRanges.push(Math.max(highLow, highPrevClose, lowPrevClose));
    }
    
    if (trueRanges.length < window) return null;
    
    const recentTRs = trueRanges.slice(-window);
    return recentTRs.reduce((a, b) => a + b, 0) / window;
}

/**
 * Toggle volume sub-chart visibility
 */
function toggleVolumeChart() {
    const checkbox = document.getElementById('volume-checkbox');
    const volumeContainer = document.getElementById('volume-chart-container');
    
    if (checkbox.checked) {
        volumeContainer.style.display = 'block';
        if (currentChartData && currentTicker) {
            renderVolumeChart(currentChartData);
        }
    } else {
        volumeContainer.style.display = 'none';
        if (volumeChart) {
            volumeChart.destroy();
            volumeChart = null;
        }
    }
}

/**
 * Render volume sub-chart
 */
function renderVolumeChart(data) {
    const maxDays = currentDateRange === 0 ? data.dates.length : currentDateRange;
    const startIndex = Math.max(0, data.dates.length - maxDays);
    const dates = data.dates.slice(startIndex);
    const opens = data.open.slice(startIndex);
    const closes = data.close.slice(startIndex);
    const volumes = data.volume.slice(startIndex);
    
    // Destroy existing volume chart
    if (volumeChart) {
        volumeChart.destroy();
    }
    
    const ctx = document.getElementById('volumeChart').getContext('2d');
    
    // Color bars based on price direction
    const barColors = closes.map((close, i) => {
        return close >= opens[i] ? 'rgba(16, 185, 129, 0.7)' : 'rgba(239, 68, 68, 0.7)';
    });
    
    volumeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: 'Volume',
                data: volumes,
                backgroundColor: barColors,
                borderColor: barColors.map(c => c.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        plugins: [syncCrosshairPlugin],
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Volume: ' + formatVolume(context.raw);
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#94a3b8',
                        callback: function(value) {
                            return formatVolume(value);
                        }
                    }
                }
            }
        }
    });
    
    console.log('[Chart Viewer] Volume chart rendered');
}

/**
 * Check if native fullscreen is supported
 */
function isFullscreenSupported() {
    return document.fullscreenEnabled || 
           document.webkitFullscreenEnabled || 
           document.mozFullScreenEnabled ||
           document.msFullscreenEnabled;
}

/**
 * Check if currently in fullscreen mode (native or CSS)
 */
function isInFullscreen() {
    const container = document.getElementById('chart-fullscreen-container');
    return document.fullscreenElement || 
           document.webkitFullscreenElement || 
           document.mozFullScreenElement ||
           document.msFullscreenElement ||
           container.classList.contains('mobile-fullscreen');
}

/**
 * Toggle fullscreen mode - supports both native and CSS-based fullscreen for mobile
 */
function toggleFullscreen() {
    const container = document.getElementById('chart-fullscreen-container');
    
    if (!isInFullscreen()) {
        // Enter fullscreen
        // Try native fullscreen first
        if (isFullscreenSupported()) {
            if (container.requestFullscreen) {
                container.requestFullscreen().catch(() => {
                    // Fallback to CSS fullscreen if native fails
                    enableCSSFullscreen(container);
                });
            } else if (container.webkitRequestFullscreen) {
                container.webkitRequestFullscreen();
            } else if (container.msRequestFullscreen) {
                container.msRequestFullscreen();
            }
        } else {
            // Use CSS-based fullscreen for mobile devices
            enableCSSFullscreen(container);
        }
        console.log('[Chart Viewer] Entering fullscreen mode');
    } else {
        // Exit fullscreen
        if (document.fullscreenElement || document.webkitFullscreenElement) {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
        } else {
            // Exit CSS-based fullscreen
            disableCSSFullscreen(container);
        }
        console.log('[Chart Viewer] Exiting fullscreen mode');
    }
}

/**
 * Enable CSS-based fullscreen (for mobile devices)
 */
function enableCSSFullscreen(container) {
    container.classList.add('mobile-fullscreen');
    document.body.classList.add('fullscreen-active');
    handleFullscreenChange();
}

/**
 * Disable CSS-based fullscreen
 */
function disableCSSFullscreen(container) {
    container.classList.remove('mobile-fullscreen');
    document.body.classList.remove('fullscreen-active');
    handleFullscreenChange();
}

/**
 * Handle fullscreen change event
 */
function handleFullscreenChange() {
    const icon = document.getElementById('fullscreen-icon');
    const container = document.getElementById('chart-fullscreen-container');
    const inFullscreen = isInFullscreen();
    
    if (inFullscreen) {
        icon.textContent = '✕'; // Exit fullscreen icon (X)
        // Resize chart for fullscreen
        if (currentChart) {
            setTimeout(() => currentChart.resize(), 100);
        }
        if (volumeChart) {
            setTimeout(() => volumeChart.resize(), 100);
        }
        if (rsiChart) {
            setTimeout(() => rsiChart.resize(), 100);
        }
    } else {
        icon.textContent = '⛶'; // Enter fullscreen icon
        // Resize chart back to normal
        if (currentChart) {
            setTimeout(() => currentChart.resize(), 100);
        }
        if (volumeChart) {
            setTimeout(() => volumeChart.resize(), 100);
        }
        if (rsiChart) {
            setTimeout(() => rsiChart.resize(), 100);
        }
    }
}

/**
 * Toggle RSI sub-chart visibility
 */
function toggleRSIChart() {
    const checkbox = document.getElementById('rsi-checkbox');
    const rsiContainer = document.getElementById('rsi-chart-container');
    
    if (checkbox.checked) {
        rsiContainer.style.display = 'block';
        if (currentChartData && currentTicker) {
            renderRSIChart(currentChartData);
        }
    } else {
        rsiContainer.style.display = 'none';
        if (rsiChart) {
            rsiChart.destroy();
            rsiChart = null;
        }
    }
}

/**
 * Render RSI sub-chart
 */
function renderRSIChart(data) {
    const maxDays = currentDateRange === 0 ? data.dates.length : currentDateRange;
    const startIndex = Math.max(0, data.dates.length - maxDays);
    const dates = data.dates.slice(startIndex);
    const rsiValues = data.rsi ? data.rsi.slice(startIndex) : [];
    
    // If no RSI data, calculate it client-side
    let rsiData = rsiValues;
    if (!rsiValues.length || rsiValues.every(v => v === null)) {
        const closes = data.close.slice(startIndex);
        rsiData = calculateRSIFallback(closes);
    }
    
    // Destroy existing RSI chart
    if (rsiChart) {
        rsiChart.destroy();
    }
    
    const ctx = document.getElementById('rsiChart').getContext('2d');
    
    rsiChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'RSI (14)',
                data: rsiData,
                borderColor: '#ec4899',
                backgroundColor: 'rgba(236, 72, 153, 0.1)',
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                tension: 0.1
            }]
        },
        plugins: [syncCrosshairPlugin],
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            let status = '';
                            if (value >= 70) status = ' (Overbought)';
                            else if (value <= 30) status = ' (Oversold)';
                            return `RSI: ${value?.toFixed(2) || 'N/A'}${status}`;
                        }
                    }
                },
                // Draw overbought/oversold zones
                annotation: {
                    annotations: {
                        overbought: {
                            type: 'line',
                            yMin: 70,
                            yMax: 70,
                            borderColor: 'rgba(239, 68, 68, 0.5)',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        },
                        oversold: {
                            type: 'line',
                            yMin: 30,
                            yMax: 30,
                            borderColor: 'rgba(16, 185, 129, 0.5)',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    min: 0,
                    max: 100,
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#94a3b8',
                        stepSize: 20
                    }
                }
            }
        }
    });
    
    // Draw reference lines manually since annotation plugin may not be loaded
    const yScale = rsiChart.scales.y;
    const ctx2 = rsiChart.ctx;
    
    // Save original after draw
    const originalDraw = rsiChart.draw;
    rsiChart.draw = function() {
        originalDraw.apply(this, arguments);
        
        const chartArea = this.chartArea;
        ctx2.save();
        ctx2.setLineDash([5, 5]);
        
        // Overbought line (70)
        const y70 = yScale.getPixelForValue(70);
        ctx2.strokeStyle = 'rgba(239, 68, 68, 0.5)';
        ctx2.beginPath();
        ctx2.moveTo(chartArea.left, y70);
        ctx2.lineTo(chartArea.right, y70);
        ctx2.stroke();
        
        // Oversold line (30)
        const y30 = yScale.getPixelForValue(30);
        ctx2.strokeStyle = 'rgba(16, 185, 129, 0.5)';
        ctx2.beginPath();
        ctx2.moveTo(chartArea.left, y30);
        ctx2.lineTo(chartArea.right, y30);
        ctx2.stroke();
        
        ctx2.restore();
    };
    
    rsiChart.update();
    
    console.log('[Chart Viewer] RSI chart rendered');
}

/**
 * Calculate RSI fallback from closes (client-side calculation)
 */
function calculateRSIFallback(closes, window = 14) {
    if (closes.length < window + 1) return Array(closes.length).fill(null);
    
    const rsiValues = Array(window).fill(null);
    
    // Calculate price changes
    const changes = [];
    for (let i = 1; i < closes.length; i++) {
        changes.push(closes[i] - closes[i - 1]);
    }
    
    // Calculate initial average gain/loss
    let avgGain = 0, avgLoss = 0;
    for (let i = 0; i < window; i++) {
        if (changes[i] > 0) avgGain += changes[i];
        else avgLoss += Math.abs(changes[i]);
    }
    avgGain /= window;
    avgLoss /= window;
    
    // First RSI
    if (avgLoss === 0) {
        rsiValues.push(100);
    } else {
        const rs = avgGain / avgLoss;
        rsiValues.push(100 - (100 / (1 + rs)));
    }
    
    // Subsequent RSI values
    for (let i = window; i < changes.length; i++) {
        const change = changes[i];
        const gain = Math.max(0, change);
        const loss = Math.abs(Math.min(0, change));
        
        avgGain = (avgGain * (window - 1) + gain) / window;
        avgLoss = (avgLoss * (window - 1) + loss) / window;
        
        if (avgLoss === 0) {
            rsiValues.push(100);
        } else {
            const rs = avgGain / avgLoss;
            rsiValues.push(100 - (100 / (1 + rs)));
        }
    }
    
    return rsiValues;
}

/**
 * Toggle Relative Strength sub-chart visibility
 */
function toggleRSChart() {
    const checkbox = document.getElementById('rs-checkbox');
    const rsContainer = document.getElementById('rs-chart-container');
    
    if (checkbox.checked) {
        rsContainer.style.display = 'block';
        if (currentChartData && currentTicker) {
            renderRSChart(currentChartData);
        }
    } else {
        rsContainer.style.display = 'none';
        if (rsChart) {
            rsChart.destroy();
            rsChart = null;
        }
    }
}

/**
 * Render Relative Strength vs SPY sub-chart
 */
function renderRSChart(data) {
    const maxDays = currentDateRange === 0 ? data.dates.length : currentDateRange;
    const startIndex = Math.max(0, data.dates.length - maxDays);
    const dates = data.dates.slice(startIndex);
    const rsValues = data.rs_spy ? data.rs_spy.slice(startIndex) : [];
    
    // If no RS data available, show placeholder
    if (!rsValues.length || rsValues.every(v => v === null)) {
        console.log('[Chart Viewer] No RS vs SPY data available');
        const container = document.getElementById('rs-chart-container');
        container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#94a3b8;">RS vs SPY data not available - requires backend update</div>';
        return;
    }
    
    // Restore canvas if it was replaced with message
    let canvas = document.getElementById('rsChart');
    if (!canvas) {
        const container = document.getElementById('rs-chart-container');
        container.innerHTML = '<canvas id="rsChart"></canvas>';
        canvas = document.getElementById('rsChart');
    }
    
    // Destroy existing RS chart
    if (rsChart) {
        rsChart.destroy();
    }
    
    const ctx = canvas.getContext('2d');
    
    // Determine colors based on trend
    const lastRS = rsValues.filter(v => v !== null).slice(-1)[0] || 100;
    const isOutperforming = lastRS > 100;
    const lineColor = isOutperforming ? '#10b981' : '#ef4444'; // Green if outperforming, red if underperforming
    const bgColor = isOutperforming ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';
    
    rsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'RS vs SPY',
                data: rsValues,
                borderColor: '#14b8a6',
                backgroundColor: bgColor,
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                tension: 0.1
            }]
        },
        plugins: [syncCrosshairPlugin],
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            let status = '';
                            if (value > 100) status = ' (Outperforming SPY)';
                            else if (value < 100) status = ' (Underperforming SPY)';
                            else status = ' (Equal to SPY)';
                            return `RS: ${value?.toFixed(2) || 'N/A'}${status}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#94a3b8',
                        callback: function(value) {
                            return value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
    
    // Draw 100 line (baseline - equal to SPY)
    const yScale = rsChart.scales.y;
    const ctx2 = rsChart.ctx;
    
    const originalDraw = rsChart.draw;
    rsChart.draw = function() {
        originalDraw.apply(this, arguments);
        
        const chartArea = this.chartArea;
        const y100 = yScale.getPixelForValue(100);
        
        if (y100 >= chartArea.top && y100 <= chartArea.bottom) {
            ctx2.save();
            ctx2.setLineDash([5, 5]);
            ctx2.strokeStyle = 'rgba(148, 163, 184, 0.5)';
            ctx2.beginPath();
            ctx2.moveTo(chartArea.left, y100);
            ctx2.lineTo(chartArea.right, y100);
            ctx2.stroke();
            ctx2.restore();
        }
    };
    
    rsChart.update();
    
    console.log('[Chart Viewer] RS vs SPY chart rendered');
}

