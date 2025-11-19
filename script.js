// Fetch and display stock screening results
async function loadResults() {
    try {
        const response = await fetch('results.json');
        if (!response.ok) {
            throw new Error('Failed to load results');
        }
        
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        console.error('Error loading results:', error);
        showError();
    }
}

function displayResults(data) {
    // Update timestamp
    const timestamp = new Date(data.timestamp);
    document.getElementById('last-updated').textContent = 
        `Last Updated: ${timestamp.toLocaleString('en-US', { 
            dateStyle: 'medium', 
            timeStyle: 'short',
            timeZone: 'Asia/Jerusalem'
        })} (Jerusalem Time)`;

    // Update summary cards
    document.getElementById('hot-count').textContent = data.summary.hot_stocks_count;
    document.getElementById('watch-count').textContent = data.summary.watch_list_count;
    document.getElementById('total-count').textContent = data.summary.total_analyzed;
    document.getElementById('failed-count').textContent = data.summary.failed_count;

    // Display hot stocks
    displayStocks(data.hot_stocks, 'hot-stocks-container', 'hot');

    // Display watch list
    displayStocks(data.watch_list, 'watch-list-container', 'watch');

    // Display failed tickers
    if (data.failed_tickers && data.failed_tickers.length > 0) {
        displayFailedTickers(data.failed_tickers);
    }
}

function displayStocks(stocks, containerId, type) {
    const container = document.getElementById(containerId);
    
    if (!stocks || stocks.length === 0) {
        container.innerHTML = '<div class="loading">No stocks found in this category</div>';
        return;
    }

    container.innerHTML = stocks.map(stock => `
        <div class="stock-card">
            <div class="stock-symbol">
                ${stock.symbol}
                <span class="badge badge-${type}">
                    ${type === 'hot' ? '🔥 Above SMA' : '👀 Below SMA'}
                </span>
            </div>
            <div class="stock-info">
                <div class="info-row">
                    <span class="info-label">Last Close</span>
                    <span class="info-value">$${stock.last_close.toFixed(2)}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">SMA150</span>
                    <span class="info-value">$${stock.sma150.toFixed(2)}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Distance from SMA</span>
                    <span class="info-value ${stock.distance_percent >= 0 ? 'distance-positive' : 'distance-negative'}">
                        ${stock.distance_percent > 0 ? '+' : ''}${stock.distance_percent.toFixed(2)}%
                    </span>
                </div>
                <div class="info-row">
                    <span class="info-label">ATR14</span>
                    <span class="info-value">$${stock.atr.toFixed(2)}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">ATR %</span>
                    <span class="info-value">${stock.atr_percent.toFixed(2)}%</span>
                </div>
            </div>
        </div>
    `).join('');
}

function displayFailedTickers(tickers) {
    const section = document.getElementById('failed-section');
    const container = document.getElementById('failed-tickers-container');
    
    section.style.display = 'block';
    
    container.innerHTML = `
        <div class="failed-list">
            ${tickers.map(ticker => `
                <span class="failed-ticker">${ticker}</span>
            `).join('')}
        </div>
    `;
}

function showError() {
    const containers = ['hot-stocks-container', 'watch-list-container'];
    containers.forEach(id => {
        const container = document.getElementById(id);
        container.innerHTML = `
            <div class="error">
                ⚠️ Unable to load results. Please try again later or check if results.json exists.
            </div>
        `;
    });
}

// Load results when page loads
document.addEventListener('DOMContentLoaded', loadResults);

// Auto-refresh every 5 minutes
setInterval(loadResults, 5 * 60 * 1000);
