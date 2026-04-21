// Filtered stocks page functionality
let filteredStocks = [];
let currentPage = 1;
let stocksPerPage = 50; // More per page since these are simpler items

// Adjust stocks per page based on screen size
function updateStocksPerPage() {
    if (window.innerWidth <= 768) {
        stocksPerPage = 30;
    } else {
        stocksPerPage = 50;
    }
}

async function loadFilteredPage() {
    updateStocksPerPage();
    
    const data = await loadResults();
    if (!data) {
        showError();
        return;
    }

    globalData = data;
    updateTimestamp(data);

    filteredStocks = data.filtered_by_sma || [];
    document.getElementById('total-stocks').textContent = filteredStocks.length;

    // Check if we should scroll to a specific ticker (from search redirect)
    const urlParams = new URLSearchParams(window.location.search);
    const tickerToFind = urlParams.get('ticker');
    
    if (tickerToFind) {
        // Find which page the ticker is on
        const tickerIndex = filteredStocks.findIndex(t => t === tickerToFind.toUpperCase());
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
    
    // Re-adjust on window resize
    window.addEventListener('resize', () => {
        const oldPerPage = stocksPerPage;
        updateStocksPerPage();
        if (oldPerPage !== stocksPerPage) {
            const firstStockIndex = (currentPage - 1) * oldPerPage;
            currentPage = Math.floor(firstStockIndex / stocksPerPage) + 1;
            displayCurrentPage();
            setupPagination();
        }
    });
}

function displayCurrentPage() {
    const container = document.getElementById('filtered-container');
    const startIndex = (currentPage - 1) * stocksPerPage;
    const endIndex = Math.min(startIndex + stocksPerPage, filteredStocks.length);
    const pageStocks = filteredStocks.slice(startIndex, endIndex);

    if (pageStocks.length === 0) {
        container.innerHTML = '<div class="loading">No filtered stocks found</div>';
        return;
    }

    container.innerHTML = pageStocks.map(ticker => createFilteredTickerItem(ticker)).join('');

    // Update page info
    document.getElementById('current-page').textContent = currentPage;
}

function createFilteredTickerItem(ticker) {
    const isFav = isFavorite(ticker);
    return `
        <div class="filtered-ticker-item" data-ticker="${ticker}">
            <span class="favorite-star ${isFav ? 'is-favorite' : ''}" 
                  data-ticker="${ticker}" 
                  onclick="toggleFavorite('${ticker}', event)"
                  title="${isFav ? 'Remove from favorites' : 'Add to favorites'}">
                ${isFav ? '★' : '☆'}
            </span>
            <a href="chart-viewer.html?ticker=${ticker}" class="filtered-ticker-link">
                <span class="ticker-symbol">${ticker}</span>
                <span class="view-chart-icon">📈</span>
            </a>
        </div>
    `;
}

function setupPagination() {
    const totalPages = Math.ceil(filteredStocks.length / stocksPerPage);
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
    const totalPages = Math.ceil(filteredStocks.length / stocksPerPage);
    if (page < 1 || page > totalPages) return;
    
    currentPage = page;
    displayCurrentPage();
    setupPagination();
    
    // Scroll to top of list
    document.getElementById('filtered-container').scrollIntoView({ behavior: 'smooth' });
}

function showError() {
    const container = document.getElementById('filtered-container');
    container.innerHTML = `
        <div class="error">
            ⚠️ Unable to load results. Please try again later or check if results.json exists.
        </div>
    `;
}

// Load data when page loads
document.addEventListener('DOMContentLoaded', loadFilteredPage);

// Refresh function for auto-refresh
window.refreshCurrentPage = loadFilteredPage;
