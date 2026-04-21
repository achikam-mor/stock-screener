// Failed tickers page functionality
async function loadFailedPage() {
    const data = await loadResults();
    if (!data) {
        showError();
        return;
    }

    globalData = data;
    updateTimestamp(data);

    const failedTickers = data.failed_tickers || [];
    document.getElementById('total-stocks').textContent = failedTickers.length;

    displayFailedTickers(failedTickers);

    // Check if we should scroll to a specific ticker (from search redirect)
    const urlParams = new URLSearchParams(window.location.search);
    const tickerToFind = urlParams.get('ticker');
    if (tickerToFind) {
        setTimeout(() => scrollToTicker(tickerToFind.toUpperCase()), 200);
    }
}

function displayFailedTickers(tickers) {
    const container = document.getElementById('failed-container');
    
    if (!tickers || tickers.length === 0) {
        container.innerHTML = '<div class="loading">✅ No failed tickers - all stocks processed successfully!</div>';
        return;
    }

    container.innerHTML = tickers.map(ticker => 
        `<div class="failed-ticker-item" data-ticker="${ticker}">${ticker}</div>`
    ).join('');
}

function showError() {
    const container = document.getElementById('failed-container');
    container.innerHTML = `
        <div class="error">
            ⚠️ Unable to load results. Please try again later or check if results.json exists.
        </div>
    `;
}

// Load data when page loads
document.addEventListener('DOMContentLoaded', loadFailedPage);

// Refresh function for auto-refresh
window.refreshCurrentPage = loadFailedPage;
