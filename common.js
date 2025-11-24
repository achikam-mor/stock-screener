// Common functionality shared across all pages
let globalData = null;

// Load results data
async function loadResults() {
    try {
        const response = await fetch('results.json');
        if (!response.ok) {
            throw new Error('Failed to load results');
        }
        globalData = await response.json();
        return globalData;
    } catch (error) {
        console.error('Error loading results:', error);
        return null;
    }
}

// Update timestamp display
function updateTimestamp(data) {
    const timestamp = new Date(data.timestamp);
    const timestampEl = document.getElementById('last-updated');
    if (timestampEl) {
        timestampEl.textContent = 
            `Last Updated: ${timestamp.toLocaleString('en-US', { 
                dateStyle: 'medium', 
                timeStyle: 'short',
                timeZone: 'Asia/Jerusalem'
            })} (Jerusalem Time)`;
    }
}

// Global search functionality
async function searchTicker() {
    const input = document.getElementById('ticker-search');
    const notification = document.getElementById('search-notification');
    const ticker = input.value.trim().toUpperCase();
    
    if (!ticker) {
        showNotification('Please enter a ticker', 'error');
        return;
    }

    if (!globalData) {
        globalData = await loadResults();
    }

    if (!globalData) {
        showNotification('Failed to load data', 'error');
        return;
    }

    // Search in hot stocks
    const inHot = globalData.hot_stocks.find(s => s.symbol === ticker);
    if (inHot) {
        handleSearchResult('hot', ticker, 'Hot Stocks');
        return;
    }

    // Search in watch list
    const inWatch = globalData.watch_list.find(s => s.symbol === ticker);
    if (inWatch) {
        handleSearchResult('watch', ticker, 'Watch List');
        return;
    }

    // Search in failed tickers
    const inFailed = globalData.failed_tickers.includes(ticker);
    if (inFailed) {
        handleSearchResult('failed', ticker, 'Failed Tickers');
        return;
    }

    showNotification(`Ticker "${ticker}" not found`, 'error');
}

// Handle search result based on current page
function handleSearchResult(foundIn, ticker, listName) {
    const currentPage = window.location.pathname.split('/').pop();
    
    // Map page types to file names
    const pageMap = {
        'hot': 'hot-stocks.html',
        'watch': 'watch-list.html',
        'failed': 'failed-tickers.html'
    };

    // If ticker is on current page, scroll to it
    if ((currentPage === 'hot-stocks.html' && foundIn === 'hot') ||
        (currentPage === 'watch-list.html' && foundIn === 'watch') ||
        (currentPage === 'failed-tickers.html' && foundIn === 'failed')) {
        
        scrollToTicker(ticker);
        return;
    }

    // Ticker is on a different page - show notification with redirect option
    showNotificationWithRedirect(ticker, listName, pageMap[foundIn]);
}

// Scroll to ticker on current page
function scrollToTicker(ticker) {
    // Wait a bit for pagination to render if needed
    setTimeout(() => {
        const element = document.querySelector(`[data-ticker="${ticker}"]`);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Highlight the element
            element.style.transition = 'background-color 0.3s ease';
            const originalBg = window.getComputedStyle(element).backgroundColor;
            element.style.backgroundColor = 'rgba(0, 123, 255, 0.3)';
            
            setTimeout(() => {
                element.style.backgroundColor = originalBg;
            }, 2000);
            
            showNotification(`Found: ${ticker}`, 'success');
        } else {
            showNotification(`Ticker "${ticker}" not found on current page`, 'error');
        }
    }, 100);
}

// Show notification message
function showNotification(message, type) {
    const notification = document.getElementById('search-notification');
    if (!notification) return;
    
    notification.textContent = message;
    notification.className = `search-notification ${type}`;
    notification.style.display = 'block';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

// Show notification with redirect button
function showNotificationWithRedirect(ticker, listName, targetPage) {
    const notification = document.getElementById('search-notification');
    if (!notification) return;
    
    notification.innerHTML = `
        <span>Ticker "${ticker}" found in ${listName}</span>
        <button onclick="window.location.href='${targetPage}?ticker=${ticker}'" class="redirect-btn">
            Go to ${listName} →
        </button>
    `;
    notification.className = 'search-notification info';
    notification.style.display = 'flex';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 5000);
}

// Allow Enter key to trigger search
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('ticker-search');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchTicker();
            }
        });
    }
});

// Auto-refresh every 5 minutes
setInterval(async () => {
    globalData = await loadResults();
    if (window.refreshCurrentPage) {
        window.refreshCurrentPage();
    }
}, 5 * 60 * 1000);
