// Stocks page functionality (for hot-stocks and watch-list pages)
let currentPageType = 'hot'; // 'hot' or 'watch'
let allStocks = [];
let currentPage = 1;
let stocksPerPage = 20;

// Adjust stocks per page based on screen size
function updateStocksPerPage() {
    if (window.innerWidth <= 768) {
        stocksPerPage = 10; // Show 10 stocks per page on mobile
    } else {
        stocksPerPage = 20; // Show 20 stocks per page on desktop
    }
}

function initStocksPage(pageType) {
    currentPageType = pageType;
    updateStocksPerPage();
    loadStocksPage();
    
    // Re-adjust on window resize
    window.addEventListener('resize', () => {
        const oldPerPage = stocksPerPage;
        updateStocksPerPage();
        if (oldPerPage !== stocksPerPage) {
            // Recalculate current page to maintain position
            const firstStockIndex = (currentPage - 1) * oldPerPage;
            currentPage = Math.floor(firstStockIndex / stocksPerPage) + 1;
            displayCurrentPage();
            setupPagination();
        }
    });
}

async function loadStocksPage() {
    const data = await loadResults();
    if (!data) {
        showError();
        return;
    }

    globalData = data;
    updateTimestamp(data);

    // Get stocks based on page type
    allStocks = currentPageType === 'hot' ? data.hot_stocks : data.watch_list;

    // Update total count
    document.getElementById('total-stocks').textContent = allStocks.length;

    // Check if we should scroll to a specific ticker (from search redirect)
    const urlParams = new URLSearchParams(window.location.search);
    const tickerToFind = urlParams.get('ticker');
    
    if (tickerToFind) {
        // Find which page the ticker is on
        const tickerIndex = allStocks.findIndex(s => s.symbol === tickerToFind.toUpperCase());
        if (tickerIndex >= 0) {
            currentPage = Math.floor(tickerIndex / stocksPerPage) + 1;
        }
    }

    displayCurrentPage();
    setupPagination();

    // Scroll to ticker if specified
    if (tickerToFind) {
        setTimeout(() => scrollToTicker(tickerToFind.toUpperCase()), 200);
    }
}

function displayCurrentPage() {
    const container = document.getElementById('stocks-container');
    const startIndex = (currentPage - 1) * stocksPerPage;
    const endIndex = Math.min(startIndex + stocksPerPage, allStocks.length);
    const pageStocks = allStocks.slice(startIndex, endIndex);

    if (pageStocks.length === 0) {
        container.innerHTML = '<div class="loading">No stocks found in this category</div>';
        return;
    }

    container.innerHTML = pageStocks.map(stock => createCompactStockCard(stock, currentPageType)).join('');

    // Update page info
    document.getElementById('current-page').textContent = currentPage;
}

function createCompactStockCard(stock, type) {
    const volumeRatio = stock.avg_volume_14d > 0 
        ? (stock.last_volume / stock.avg_volume_14d).toFixed(2) 
        : '0.00';
    
    return `
        <div class="stock-card-compact" data-ticker="${stock.symbol}">
            <div class="stock-header">
                <div class="stock-symbol">${stock.symbol}</div>
                <span class="badge badge-${type}">
                    ${type === 'hot' ? '🔥' : '👀'}
                </span>
            </div>
            <div class="stock-data">
                <div class="data-row">
                    <span class="label">Close</span>
                    <span class="value">$${stock.last_close.toFixed(2)}</span>
                </div>
                <div class="data-row">
                    <span class="label">SMA150</span>
                    <span class="value">$${stock.sma150.toFixed(2)}</span>
                </div>
                <div class="data-row">
                    <span class="label">Distance</span>
                    <span class="value ${stock.distance_percent >= 0 ? 'positive' : 'negative'}">
                        ${stock.distance_percent > 0 ? '+' : ''}${stock.distance_percent.toFixed(2)}%
                    </span>
                </div>
                <div class="data-row">
                    <span class="label">ATR14</span>
                    <span class="value">$${stock.atr.toFixed(2)} (${stock.atr_percent.toFixed(2)}%)</span>
                </div>
                <div class="data-row">
                    <span class="label">Volume</span>
                    <span class="value">${(stock.last_volume / 1000000).toFixed(2)}M</span>
                </div>
                <div class="data-row">
                    <span class="label">Avg Vol 14d</span>
                    <span class="value">${(stock.avg_volume_14d / 1000000).toFixed(2)}M (${volumeRatio}x)</span>
                </div>
            </div>
        </div>
    `;
}

function setupPagination() {
    const totalPages = Math.ceil(allStocks.length / stocksPerPage);
    document.getElementById('total-pages').textContent = totalPages;

    const paginationContainer = document.getElementById('pagination-controls');
    
    if (totalPages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }

    let paginationHTML = '';

    // Previous button
    if (currentPage > 1) {
        paginationHTML += `<button class="page-btn" onclick="goToPage(${currentPage - 1})">← Previous</button>`;
    }

    // Page numbers
    const maxPagesToShow = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
    let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);

    if (endPage - startPage < maxPagesToShow - 1) {
        startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }

    if (startPage > 1) {
        paginationHTML += `<button class="page-btn" onclick="goToPage(1)">1</button>`;
        if (startPage > 2) {
            paginationHTML += `<span class="page-ellipsis">...</span>`;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === currentPage ? 'active' : '';
        paginationHTML += `<button class="page-btn ${activeClass}" onclick="goToPage(${i})">${i}</button>`;
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += `<span class="page-ellipsis">...</span>`;
        }
        paginationHTML += `<button class="page-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }

    // Next button
    if (currentPage < totalPages) {
        paginationHTML += `<button class="page-btn" onclick="goToPage(${currentPage + 1})">Next →</button>`;
    }

    paginationContainer.innerHTML = paginationHTML;
}

function goToPage(page) {
    currentPage = page;
    displayCurrentPage();
    setupPagination();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showError() {
    const container = document.getElementById('stocks-container');
    container.innerHTML = `
        <div class="error">
            ⚠️ Unable to load results. Please try again later or check if results.json exists.
        </div>
    `;
}

// Refresh function for auto-refresh
window.refreshCurrentPage = loadStocksPage;
