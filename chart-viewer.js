/**
 * Chart Viewer - Interactive Candlestick Charts with TradingView Lightweight Charts
 */

let chartData = null;
let currentChart = null;
let resultsData = null;

// Load chart data on page load
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
        const response = await fetch('chart_data.json');
        if (response.ok) {
            const data = await response.json();
            chartData = data.stocks;
            
            // Update timestamp
            if (data.last_updated) {
                const date = new Date(data.last_updated);
                document.getElementById('last-updated').textContent = 
                    `Last updated: ${date.toLocaleString()}`;
            } else {
                document.getElementById('last-updated').textContent = 'Timestamp unavailable';
            }
            
            // Check if chart data is empty
            if (!chartData || Object.keys(chartData).length === 0) {
                document.getElementById('last-updated').textContent = 'No chart data available yet';
                console.log('Chart data file is empty');
            } else {
                console.log(`Chart data loaded: ${Object.keys(chartData).length} stocks available`);
            }
            
            // Check if ticker is in URL parameter
            const urlParams = new URLSearchParams(window.location.search);
            const ticker = urlParams.get('ticker');
            if (ticker) {
                document.getElementById('chart-ticker-search').value = ticker.toUpperCase();
                loadChart();
            }
        } else {
            document.getElementById('last-updated').textContent = 'Chart data not found';
            console.error('Chart data file not found');
        }
    } catch (error) {
        console.error('Error loading chart data:', error);
        document.getElementById('last-updated').textContent = 'Error loading chart data';
        showNotification('Chart data unavailable. Please run the workflow to generate charts.', 'error');
    }
    
    // Handle Enter key in search box
    document.getElementById('chart-ticker-search').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            loadChart();
        }
    });
});

/**
 * Load and display chart for the searched ticker
 */
function loadChart() {
    const ticker = document.getElementById('chart-ticker-search').value.trim().toUpperCase();
    
    if (!ticker) {
        showNotification('Please enter a ticker symbol', 'error');
        return;
    }
    
    if (!chartData) {
        showNotification('Chart data not loaded yet. Please wait...', 'error');
        return;
    }
    
    if (!chartData[ticker]) {
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
    
    // Show success notification
    showNotification(`Loading chart for ${ticker}...`, 'success');
    
    // Display the chart
    displayCandlestickChart(ticker, chartData[ticker]);
}

/**
 * Display candlestick chart using TradingView Lightweight Charts
 */
function displayCandlestickChart(ticker, data) {
    const chartSection = document.getElementById('chart-section');
    chartSection.style.display = 'block';
    
    // Update chart title
    document.getElementById('chart-title').textContent = `${ticker} - Candlestick Chart`;
    document.getElementById('chart-data-points').textContent = `${data.dates.length} trading days`;
    
    // Calculate statistics
    const currentPrice = data.close[data.close.length - 1];
    const periodHigh = Math.max(...data.high);
    const periodLow = Math.min(...data.low);
    const avgVolume = Math.round(data.volume.reduce((a, b) => a + b, 0) / data.volume.length);
    
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
        currentChart.remove();
        currentChart = null;
    }
    
    // Get chart container (not canvas anymore)
    const chartContainer = document.getElementById('candlestickChart');
    
    // Clear the container
    chartContainer.innerHTML = '';
    
    try {
        // Create chart with TradingView Lightweight Charts
        currentChart = LightweightCharts.createChart(chartContainer, {
            width: chartContainer.clientWidth,
            height: 500,
            layout: {
                background: { color: '#0f172a' },
                textColor: '#94a3b8',
            },
            grid: {
                vertLines: { color: '#1e293b' },
                horzLines: { color: '#1e293b' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: {
                    color: '#64748b',
                    width: 1,
                    style: LightweightCharts.LineStyle.Dashed,
                },
                horzLine: {
                    color: '#64748b',
                    width: 1,
                    style: LightweightCharts.LineStyle.Dashed,
                },
            },
            rightPriceScale: {
                borderColor: '#334155',
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.2,
                },
            },
            timeScale: {
                borderColor: '#334155',
                timeVisible: true,
                secondsVisible: false,
            },
        });
        
        // Add candlestick series
        const candlestickSeries = currentChart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#ef4444',
            borderUpColor: '#10b981',
            borderDownColor: '#ef4444',
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        });
        
        // Prepare data in Lightweight Charts format
        // Convert dates to timestamps (seconds since epoch)
        const candlestickData = data.dates.map((date, i) => ({
            time: Math.floor(new Date(date).getTime() / 1000), // Convert to seconds
            open: data.open[i],
            high: data.high[i],
            low: data.low[i],
            close: data.close[i]
        }));
        
        // Sort by time (just in case)
        candlestickData.sort((a, b) => a.time - b.time);
        
        // Set the data
        candlestickSeries.setData(candlestickData);
        
        // Fit content to view
        currentChart.timeScale().fitContent();
        
        // Handle window resize
        const resizeObserver = new ResizeObserver(entries => {
            if (currentChart && entries.length > 0) {
                const newWidth = entries[0].contentRect.width;
                currentChart.applyOptions({ width: newWidth });
            }
        });
        resizeObserver.observe(chartContainer);
        
        // Store observer for cleanup
        currentChart._resizeObserver = resizeObserver;
        
        console.log(`Chart created for ${ticker} with ${candlestickData.length} candles`);
        
    } catch (error) {
        console.error('Error creating chart:', error);
        showNotification('Error displaying chart. Please try again.', 'error');
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
