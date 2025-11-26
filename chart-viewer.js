/**
 * Chart Viewer - Interactive Candlestick Charts
 */

let chartData = null;
let currentChart = null;

// Load chart data on page load
document.addEventListener('DOMContentLoaded', async () => {
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
        showNotification(`No data available for ${ticker}. Stock may not have been analyzed or data fetch failed.`, 'error');
        document.getElementById('chart-section').style.display = 'none';
        return;
    }
    
    // Show success notification
    showNotification(`Loading chart for ${ticker}...`, 'success');
    
    // Display the chart
    displayCandlestickChart(ticker, chartData[ticker]);
}

/**
 * Display candlestick chart using Chart.js
 */
function displayCandlestickChart(ticker, data) {
    const chartSection = document.getElementById('chart-section');
    chartSection.style.display = 'block';
    
    // Update chart title
    document.getElementById('chart-title').textContent = `${ticker} - Candlestick Chart`;
    document.getElementById('chart-data-points').textContent = `${data.dates.length} trading days`;
    
    // Prepare candlestick data
    const candlestickData = data.dates.map((date, i) => ({
        x: date,
        o: data.open[i],
        h: data.high[i],
        l: data.low[i],
        c: data.close[i]
    }));
    
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
        currentChart.destroy();
    }
    
    // Create candlestick chart
    const ctx = document.getElementById('candlestickChart').getContext('2d');
    
    currentChart = new Chart(ctx, {
        type: 'candlestick',
        data: {
            datasets: [{
                label: ticker,
                data: candlestickData,
                color: {
                    up: '#10b981',    // Green for bullish
                    down: '#ef4444',  // Red for bearish
                    unchanged: '#6b7280'
                },
                borderColor: {
                    up: '#10b981',
                    down: '#ef4444',
                    unchanged: '#6b7280'
                }
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 41, 59, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#f1f5f9',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            const data = context.raw;
                            return [
                                `Open: $${data.o.toFixed(2)}`,
                                `High: $${data.h.toFixed(2)}`,
                                `Low: $${data.l.toFixed(2)}`,
                                `Close: $${data.c.toFixed(2)}`,
                                `Change: $${(data.c - data.o).toFixed(2)} (${((data.c - data.o) / data.o * 100).toFixed(2)}%)`
                            ];
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
    
    // Scroll to chart
    chartSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
    const notification = document.getElementById('chart-notification');
    notification.textContent = message;
    notification.className = `search-notification ${type}`;
    notification.style.display = 'flex';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 5000);
}
