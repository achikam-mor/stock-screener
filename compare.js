/**
 * Stock Comparison Tool - Compare up to 3 stocks side-by-side
 */

let resultsData = null;
let chartData = null;
let selectedStocks = [];
let charts = [];

// Load data on page load
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Load results.json
        const resultsResponse = await fetch('results.json');
        if (resultsResponse.ok) {
            resultsData = await resultsResponse.json();
            
            // Update timestamp
            if (resultsData.last_updated) {
                const date = new Date(resultsData.last_updated);
                document.getElementById('last-updated').textContent = 
                    `Last updated: ${date.toLocaleString()}`;
            }
        }
        
        // Load chart_data.json
        const chartResponse = await fetch('chart_data.json');
        if (chartResponse.ok) {
            const data = await chartResponse.json();
            chartData = data.stocks;
        }
        
        // Check for URL parameters (tickers passed from other pages)
        const urlParams = new URLSearchParams(window.location.search);
        const tickers = urlParams.get('tickers');
        if (tickers) {
            const tickerList = tickers.split(',').slice(0, 3); // Max 3 stocks
            tickerList.forEach(ticker => {
                addTickerToCompare(ticker.toUpperCase());
            });
            if (selectedStocks.length > 0) {
                compareStocks();
            }
        }
    } catch (error) {
        console.error('Error loading data:', error);
        showNotification('Error loading data. Please try again later.', 'error');
    }
    
    // Handle Enter key in search box
    document.getElementById('compare-ticker-search').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addTickerToCompare();
        }
    });
});

/**
 * Add a ticker to the comparison selection
 */
function addTickerToCompare(ticker = null) {
    const input = document.getElementById('compare-ticker-search');
    const symbol = (ticker || input.value.trim().toUpperCase());
    
    if (!symbol) {
        showNotification('Please enter a ticker symbol', 'error');
        return;
    }
    
    // Check if already selected
    if (selectedStocks.includes(symbol)) {
        showNotification(`${symbol} is already selected`, 'error');
        input.value = '';
        return;
    }
    
    // Check max 3 stocks
    if (selectedStocks.length >= 3) {
        showNotification('Maximum 3 stocks can be compared at once', 'error');
        return;
    }
    
    // Check if stock exists in chart data
    if (!chartData || !chartData[symbol]) {
        showNotification(`${symbol} not found or data unavailable`, 'error');
        input.value = '';
        return;
    }
    
    // Add to selected stocks
    selectedStocks.push(symbol);
    input.value = '';
    updateSelectedStocksDisplay();
    updateCompareButton();
    showNotification(`${symbol} added to comparison`, 'success');
}

/**
 * Remove a ticker from selection
 */
function removeTickerFromCompare(symbol) {
    selectedStocks = selectedStocks.filter(s => s !== symbol);
    updateSelectedStocksDisplay();
    updateCompareButton();
    showNotification(`${symbol} removed from comparison`, 'info');
}

/**
 * Update the display of selected stocks
 */
function updateSelectedStocksDisplay() {
    const container = document.getElementById('selected-stocks');
    
    if (selectedStocks.length === 0) {
        container.innerHTML = '<p class="no-selection">No stocks selected yet</p>';
        return;
    }
    
    container.innerHTML = selectedStocks.map(symbol => `
        <div class="stock-chip">
            <span class="stock-chip-symbol">${symbol}</span>
            <button class="stock-chip-remove" onclick="removeTickerFromCompare('${symbol}')" title="Remove">
                ✕
            </button>
        </div>
    `).join('');
}

/**
 * Enable/disable compare button based on selection
 */
function updateCompareButton() {
    const button = document.getElementById('compare-button');
    button.disabled = selectedStocks.length < 2;
}

/**
 * Perform the comparison
 */
function compareStocks() {
    if (selectedStocks.length < 2) {
        showNotification('Please select at least 2 stocks to compare', 'error');
        return;
    }
    
    // Destroy existing charts
    charts.forEach(chart => chart.destroy());
    charts = [];
    
    // Show comparison section
    document.getElementById('comparison-section').style.display = 'block';
    
    // Update headers
    selectedStocks.forEach((symbol, index) => {
        const headerEl = document.getElementById(`ticker-header-${index + 1}`);
        if (headerEl) {
            headerEl.textContent = symbol;
            headerEl.style.display = '';
        }
    });
    
    // Hide unused columns
    for (let i = selectedStocks.length; i < 3; i++) {
        const headerEl = document.getElementById(`ticker-header-${i + 1}`);
        if (headerEl) {
            headerEl.style.display = 'none';
        }
    }
    
    // Build metrics table
    buildMetricsTable();
    
    // Build charts
    buildChartsComparison();
    
    // Scroll to results
    document.getElementById('comparison-section').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Build the metrics comparison table
 */
function buildMetricsTable() {
    const tbody = document.getElementById('comparison-metrics-body');
    
    // Get stock data - calculate from chart data for all stocks
    const stocksData = selectedStocks.map(symbol => {
        const stockFromResults = resultsData ? (resultsData.hot_stocks?.[symbol] || resultsData.watch_list?.[symbol]) : null;
        const chart = chartData ? chartData[symbol] : null;
        
        // Calculate metrics from chart data if not in results
        let calculatedData = null;
        if (chart && chart.close && chart.close.length > 0) {
            const lastIndex = chart.close.length - 1;
            const currentPrice = chart.close[lastIndex];
            const currentSMA150 = chart.sma150 && chart.sma150[lastIndex] !== null ? chart.sma150[lastIndex] : null;
            
            // Calculate ATR14 from chart data
            let atr14 = null;
            if (chart.high && chart.low && chart.close && chart.high.length >= 15) {
                const trValues = [];
                for (let i = Math.max(1, chart.high.length - 14); i < chart.high.length; i++) {
                    const high = chart.high[i];
                    const low = chart.low[i];
                    const prevClose = chart.close[i - 1];
                    const tr = Math.max(
                        high - low,
                        Math.abs(high - prevClose),
                        Math.abs(low - prevClose)
                    );
                    trValues.push(tr);
                }
                if (trValues.length > 0) {
                    atr14 = trValues.reduce((a, b) => a + b, 0) / trValues.length;
                }
            }
            
            calculatedData = {
                close: currentPrice,
                sma150: currentSMA150,
                atr14: atr14,
                atr14_percent: atr14 && currentPrice ? (atr14 / currentPrice * 100) : null
            };
        }
        
        // Use results data if available, otherwise use calculated data
        const stock = stockFromResults || calculatedData;
        
        return { symbol, stock, chart };
    });
    
    // Define metrics to display
    const metrics = [
        {
            label: 'Status',
            getValue: (data) => {
                if (!resultsData) return '<span class="status-other">📊 N/A</span>';
                if (resultsData.hot_stocks?.[data.symbol]) return '<span class="status-hot">🔥 Hot</span>';
                if (resultsData.watch_list?.[data.symbol]) return '<span class="status-watch">👀 Watch</span>';
                return '<span class="status-other">📊 Other</span>';
            }
        },
        {
            label: 'Current Price',
            getValue: (data) => data.stock && data.stock.close ? `$${data.stock.close.toFixed(2)}` : 'N/A'
        },
        {
            label: 'SMA 150',
            getValue: (data) => data.stock && data.stock.sma150 ? `$${data.stock.sma150.toFixed(2)}` : 'N/A'
        },
        {
            label: '% Above SMA 150',
            getValue: (data) => {
                if (!data.stock || !data.stock.close || !data.stock.sma150) return 'N/A';
                const pct = ((data.stock.close - data.stock.sma150) / data.stock.sma150 * 100);
                const color = pct >= 0 ? '#10b981' : '#ef4444';
                return `<span style="color: ${color}">${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%</span>`;
            }
        },
        {
            label: 'ATR 14 Days',
            getValue: (data) => data.stock && data.stock.atr14 ? `$${data.stock.atr14.toFixed(2)}` : 'N/A'
        },
        {
            label: 'ATR 14 Days %',
            getValue: (data) => data.stock && data.stock.atr14_percent ? `${data.stock.atr14_percent.toFixed(2)}%` : 'N/A'
        },
        {
            label: '52-Week High',
            getValue: (data) => {
                if (!data.chart) return 'N/A';
                const high = Math.max(...data.chart.high);
                return `$${high.toFixed(2)}`;
            }
        },
        {
            label: '52-Week Low',
            getValue: (data) => {
                if (!data.chart) return 'N/A';
                const low = Math.min(...data.chart.low);
                return `$${low.toFixed(2)}`;
            }
        },
        {
            label: 'Avg Volume',
            getValue: (data) => {
                if (!data.chart) return 'N/A';
                const avg = data.chart.volume.reduce((a, b) => a + b, 0) / data.chart.volume.length;
                return formatVolume(Math.round(avg));
            }
        }
    ];
    
    // Build rows
    tbody.innerHTML = metrics.map(metric => {
        const cells = stocksData.map(data => `<td>${metric.getValue(data)}</td>`).join('');
        // Hide cells for unused columns
        const hiddenCells = selectedStocks.length < 3 ? 
            '<td style="display: none;"></td>'.repeat(3 - selectedStocks.length) : '';
        return `<tr><td class="metric-label">${metric.label}</td>${cells}${hiddenCells}</tr>`;
    }).join('');
}

/**
 * Build charts for comparison
 */
function buildChartsComparison() {
    const container = document.getElementById('charts-container');
    container.innerHTML = '';
    
    selectedStocks.forEach(symbol => {
        const chartWrapper = document.createElement('div');
        chartWrapper.className = 'chart-wrapper';
        
        const title = document.createElement('h4');
        title.textContent = symbol;
        title.className = 'chart-title';
        
        const canvas = document.createElement('canvas');
        canvas.id = `chart-${symbol}`;
        
        chartWrapper.appendChild(title);
        chartWrapper.appendChild(canvas);
        container.appendChild(chartWrapper);
        
        // Create chart
        if (chartData && chartData[symbol]) {
            createComparisonChart(symbol, canvas);
        }
    });
}

/**
 * Create a candlestick chart for comparison
 */
function createComparisonChart(symbol, canvas) {
    const data = chartData[symbol];
    const ctx = canvas.getContext('2d');
    
    // Limit to last 260 days (approximately 1 trading year)
    const maxDays = 260;
    const startIndex = Math.max(0, data.dates.length - maxDays);
    const dates = data.dates.slice(startIndex);
    const opens = data.open.slice(startIndex);
    const highs = data.high.slice(startIndex);
    const lows = data.low.slice(startIndex);
    const closes = data.close.slice(startIndex);
    const sma150Values = data.sma150 ? data.sma150.slice(startIndex) : [];
    
    // Prepare candlestick data
    const candlestickData = dates.map((date, i) => ({
        x: new Date(date).getTime(),
        o: opens[i],
        h: highs[i],
        l: lows[i],
        c: closes[i]
    }));
    
    // Prepare SMA150 line data
    const sma150Data = dates
        .map((date, i) => ({
            x: new Date(date).getTime(),
            y: sma150Values && sma150Values[i] !== null ? sma150Values[i] : null
        }))
        .filter(point => point.y !== null);
    
    // Calculate Y-axis range for displayed data
    const periodHigh = Math.max(...highs);
    const periodLow = Math.min(...lows);
    const priceMin = periodLow * 0.98;
    const priceMax = periodHigh * 1.02;
    
    // Create chart
    const chart = new Chart(ctx, {
        type: 'candlestick',
        data: {
            datasets: [
                {
                    label: symbol,
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
                    order: 2
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
                    order: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            parsing: false,
            interaction: {
                mode: 'index',
                intersect: false,
                axis: 'x'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
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
                                const change = data.c - data.o;
                                const changePct = (change / data.o * 100).toFixed(2);
                                return [
                                    `Open: $${data.o.toFixed(2)}`,
                                    `High: $${data.h.toFixed(2)}`,
                                    `Low: $${data.l.toFixed(2)}`,
                                    `Close: $${data.c.toFixed(2)}`,
                                    `Change: $${change.toFixed(2)} (${changePct}%)`
                                ];
                            } else if (context.dataset.label === 'SMA150') {
                                return `SMA150: $${data.y.toFixed(2)}`;
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
    
    charts.push(chart);
}

/**
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
 * Show notification message
 */
function showNotification(message, type) {
    const notification = document.getElementById('selection-notification');
    notification.textContent = message;
    notification.className = `search-notification ${type}`;
    notification.style.display = 'flex';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 5000);
}
