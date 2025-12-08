/**
 * Chart Viewer - Interactive Candlestick Charts with TradingView Lightweight Charts
 * Uses on-demand loading - individual stock files loaded only when requested
 */

let stockList = null;  // List of available stocks
let currentChart = null;
let resultsData = null;
let chartCache = {};  // Cache for loaded chart data

// Load stock list on page load (small file, loads instantly)
document.addEventListener('DOMContentLoaded', async () => {
    // Load results.json to check filtered stocks
    try {
        const resultsResponse = await fetch('results.json');
        if (resultsResponse.ok) {
            resultsData = await resultsResponse.json();
        }
    } catch (error) {
        console.log('Could not load results.json');
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
                document.getElementById('last-updated').textContent = 
                    `Last updated: ${date.toLocaleString()}`;
            } else {
                document.getElementById('last-updated').textContent = 'Ready to search';
            }
            
            // Check if stock list is empty
            if (!stockList || stockList.length === 0) {
                document.getElementById('last-updated').textContent = 'No chart data available yet';
                console.log('Stock list is empty');
            } else {
                console.log(`Stock list loaded: ${stockList.length} stocks available`);
            }
            
            // Check if ticker is in URL parameter
            const urlParams = new URLSearchParams(window.location.search);
            const ticker = urlParams.get('ticker');
            if (ticker) {
                document.getElementById('chart-ticker-search').value = ticker.toUpperCase();
                loadChart();
            }
        } else {
            document.getElementById('last-updated').textContent = 'Stock list not found';
            console.error('Stock list file not found');
        }
    } catch (error) {
        console.error('Error loading stock list:', error);
        document.getElementById('last-updated').textContent = 'Error loading stock list';
        showNotification('Stock list unavailable. Please run the workflow to generate data.', 'error');
    }
    
    // Handle Enter key in search box
    document.getElementById('chart-ticker-search').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            loadChart();
        }
    });
});

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
        displayCandlestickChart(ticker, chartCache[ticker]);
        return;
    }
    
    // Fetch individual stock data on-demand
    try {
        const response = await fetch(`charts/${ticker}.json`);
        if (response.ok) {
            const chartData = await response.json();
            chartCache[ticker] = chartData;  // Cache for future use
            displayCandlestickChart(ticker, chartData);
        } else {
            showNotification(`Could not load chart data for ${ticker}`, 'error');
            document.getElementById('chart-section').style.display = 'none';
        }
    } catch (error) {
        console.error(`Error loading chart for ${ticker}:`, error);
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
    
    // Limit to last 260 days (approximately 1 trading year)
    const maxDays = 260;
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
    
    document.getElementById('chart-data-points').textContent = `${dates.length} trading days`;
    
    // Calculate statistics for displayed period
    const currentPrice = closes[closes.length - 1];
    const periodHigh = Math.max(...highs);
    const periodLow = Math.min(...lows);
    const avgVolume = Math.round(volumes.reduce((a, b) => a + b, 0) / volumes.length);
    
    // Update statistics
    document.getElementById('current-price').textContent = `$${currentPrice.toFixed(2)}`;
    document.getElementById('period-high').textContent = `$${periodHigh.toFixed(2)}`;
    document.getElementById('period-low').textContent = `$${periodLow.toFixed(2)}`;
    document.getElementById('avg-volume').textContent = formatVolume(avgVolume);
    
    // Color current price based on change
    const priceChange = data.close[data.close.length - 1] - data.close[0];
    document.getElementById('current-price').style.color = priceChange >= 0 ? '#10b981' : '#ef4444';
    
    // Destroy existing chart if any
    if (currentChart) {
        currentChart.destroy();
        currentChart = null;
    }
    
    // Get canvas and context
    const canvas = document.getElementById('candlestickChart');
    const ctx = canvas.getContext('2d');
    
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
            options: {
                responsive: true,
                maintainAspectRatio: false,
                parsing: false, // Data is already in correct format
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

