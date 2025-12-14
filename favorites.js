/**
 * Favorites Page - Display and manage user's favorite stocks
 * Uses localStorage to persist favorites across sessions
 */

let allFavoriteStocks = [];
let filteredFavoriteStocks = [];
let currentPage = 1;
let stocksPerPage = 20;

// Adjust stocks per page based on screen size
function updateStocksPerPage() {
    if (window.innerWidth <= 768) {
        stocksPerPage = 10;
    } else {
        stocksPerPage = 20;
    }
}

// Initialize favorites page
document.addEventListener('DOMContentLoaded', () => {
    updateStocksPerPage();
    loadFavoritesPage();
    
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
    
    // Listen for favorites changes
    window.addEventListener('favoritesChanged', () => {
        loadFavoritesPage();
    });
});

async function loadFavoritesPage() {
    const data = await loadResults();
    if (!data) {
        showError();
        return;
    }

    globalData = data;
    updateTimestamp(data);

    // Get favorite tickers from localStorage
    const favoriteTickers = getFavorites();
    
    if (favoriteTickers.length === 0) {
        // No favorites - show empty state immediately
        document.getElementById('total-stocks').textContent = '0';
        document.getElementById('no-favorites-message').style.display = 'block';
        document.getElementById('stocks-container').style.display = 'none';
        return;
    }
    
    // Filter stocks that are in favorites from both hot_stocks and watch_list
    const allScreenedStocks = [...data.hot_stocks, ...data.watch_list];
    
    // Remove duplicates and filter by favorites
    const uniqueStocks = new Map();
    allScreenedStocks.forEach(stock => {
        if (favoriteTickers.includes(stock.symbol) && !uniqueStocks.has(stock.symbol)) {
            uniqueStocks.set(stock.symbol, stock);
        }
    });
    
    // Find favorites that aren't in hot_stocks or watch_list (filtered stocks)
    const missingFavorites = favoriteTickers.filter(ticker => !uniqueStocks.has(ticker));
    
    // Load data for missing favorites from individual chart files
    if (missingFavorites.length > 0) {
        await loadFilteredFavorites(missingFavorites, uniqueStocks);
    }
    
    allFavoriteStocks = Array.from(uniqueStocks.values());
    filteredFavoriteStocks = [...allFavoriteStocks];

    // Update total count
    document.getElementById('total-stocks').textContent = filteredFavoriteStocks.length;

    // Show/hide no favorites message
    const noFavoritesMessage = document.getElementById('no-favorites-message');
    const stocksContainer = document.getElementById('stocks-container');
    
    if (allFavoriteStocks.length === 0) {
        noFavoritesMessage.style.display = 'block';
        stocksContainer.style.display = 'none';
    } else {
        noFavoritesMessage.style.display = 'none';
        stocksContainer.style.display = '';
        applyFilters();
    }
}

// Apply cross filter
function applyFilters() {
    const crossFilter = document.getElementById('cross-filter')?.value || 'all';
    
    filteredFavoriteStocks = allFavoriteStocks.filter(stock => {
        // Golden/Death Cross filter
        if (crossFilter !== 'all') {
            if (crossFilter === 'golden' && !stock.golden_cross) return false;
            if (crossFilter === 'death' && !stock.death_cross) return false;
            if (crossFilter === 'any' && !stock.golden_cross && !stock.death_cross) return false;
        }
        return true;
    });
    
    // Reset to page 1 when filters change
    currentPage = 1;
    
    // Update total count
    document.getElementById('total-stocks').textContent = filteredFavoriteStocks.length;
    
    displayCurrentPage();
    setupPagination();
}

// Reset filters
function resetFilters() {
    const crossFilter = document.getElementById('cross-filter');
    if (crossFilter) crossFilter.value = 'all';
    applyFilters();
}

function displayCurrentPage() {
    const container = document.getElementById('stocks-container');
    const startIndex = (currentPage - 1) * stocksPerPage;
    const endIndex = Math.min(startIndex + stocksPerPage, filteredFavoriteStocks.length);
    const pageStocks = filteredFavoriteStocks.slice(startIndex, endIndex);

    if (pageStocks.length === 0) {
        container.innerHTML = '<div class="loading">No favorite stocks matching your filters</div>';
        return;
    }

    container.innerHTML = pageStocks.map(stock => createFavoriteStockCard(stock)).join('');

    // Update page info
    document.getElementById('current-page').textContent = currentPage;
}

function createFavoriteStockCard(stock) {
    const volumeRatio = stock.avg_volume_14d > 0 
        ? (stock.last_volume / stock.avg_volume_14d).toFixed(2) 
        : '0.00';
    
    // Determine category based on whether stock is filtered or screened
    let categoryClass, categoryBadge;
    if (stock.isFiltered) {
        categoryClass = 'filtered-stock';
        categoryBadge = '<span class="stock-badge filtered-badge">📊 Filtered</span>';
    } else if (stock.distance_percent >= 0) {
        categoryClass = 'hot-stock';
        categoryBadge = '<span class="stock-badge hot-badge">🔥 Hot</span>';
    } else {
        categoryClass = 'watch-stock';
        categoryBadge = '<span class="stock-badge watch-badge">👀 Watch</span>';
    }
    
    // Create cross icon HTML
    let crossIconHTML = '';
    if (stock.golden_cross) {
        crossIconHTML = '<span class="cross-icon golden-cross" title="Golden Cross (50 SMA crossed above 200 SMA)">✨</span>';
    } else if (stock.death_cross) {
        crossIconHTML = '<span class="cross-icon death-cross" title="Death Cross (50 SMA crossed below 200 SMA)">💀</span>';
    }
    
    return `
        <div class="stock-card-compact ${categoryClass}" data-ticker="${stock.symbol}">
            <div class="stock-header">
                <div class="stock-symbol">
                    ${createFavoriteStarHTML(stock.symbol)}
                    ${crossIconHTML}
                    <input type="checkbox" class="compare-checkbox" value="${stock.symbol}" 
                           onchange="toggleCompareStock('${stock.symbol}')" 
                           title="Select for comparison">
                    ${stock.symbol}
                    ${categoryBadge}
                </div>
                <a href="chart-viewer.html?ticker=${stock.symbol}" class="chart-btn">
                    📈 Launch Chart
                </a>
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
    const totalPages = Math.ceil(filteredFavoriteStocks.length / stocksPerPage);
    document.getElementById('total-pages').textContent = totalPages || 1;

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

/**
 * Load data for filtered favorites from individual chart files
 * Creates stock objects with basic data for display
 */
async function loadFilteredFavorites(tickers, stockMap) {
    const loadPromises = tickers.map(async (ticker) => {
        try {
            const response = await fetch(`charts/${ticker}.json`);
            if (response.ok) {
                const chartData = await response.json();
                
                // Calculate basic metrics from chart data
                const closes = chartData.close;
                const volumes = chartData.volume;
                const lastIndex = closes.length - 1;
                
                // Calculate SMA150 from the last 150 closes
                const sma150Period = Math.min(150, closes.length);
                const sma150Values = closes.slice(-sma150Period);
                const sma150 = sma150Values.reduce((a, b) => a + b, 0) / sma150Values.length;
                
                // Calculate ATR14 (simplified - using close differences)
                const atrPeriod = Math.min(14, closes.length - 1);
                let trSum = 0;
                for (let i = closes.length - atrPeriod; i < closes.length; i++) {
                    const high = chartData.high[i];
                    const low = chartData.low[i];
                    const prevClose = closes[i - 1];
                    const tr = Math.max(high - low, Math.abs(high - prevClose), Math.abs(low - prevClose));
                    trSum += tr;
                }
                const atr = trSum / atrPeriod;
                
                // Calculate average volume over 14 days
                const volPeriod = Math.min(14, volumes.length);
                const avgVolume = volumes.slice(-volPeriod).reduce((a, b) => a + b, 0) / volPeriod;
                
                // Create stock object compatible with display functions
                const stock = {
                    symbol: ticker,
                    last_close: closes[lastIndex],
                    sma150: sma150,
                    distance_percent: ((closes[lastIndex] - sma150) / sma150) * 100,
                    atr: atr,
                    atr_percent: (atr / closes[lastIndex]) * 100,
                    last_volume: volumes[lastIndex],
                    avg_volume_14d: avgVolume,
                    isFiltered: true  // Mark as filtered stock
                };
                
                stockMap.set(ticker, stock);
            }
        } catch (error) {
            console.log(`Could not load chart data for ${ticker}:`, error);
        }
    });
    
    await Promise.all(loadPromises);
}

// Comparison functionality (same as stocks-page.js)
let selectedForCompare = [];

function toggleCompareStock(symbol) {
    const checkbox = document.querySelector(`.compare-checkbox[value="${symbol}"]`);
    
    if (checkbox && checkbox.checked) {
        if (selectedForCompare.length >= 3) {
            showNotification('Maximum 3 stocks can be compared at once', 'error');
            checkbox.checked = false;
            return;
        }
        if (!selectedForCompare.includes(symbol)) {
            selectedForCompare.push(symbol);
        }
    } else {
        selectedForCompare = selectedForCompare.filter(s => s !== symbol);
    }
    
    updateCompareButton();
}

function updateCompareButton() {
    let compareBtn = document.getElementById('compare-selected-btn');
    
    if (selectedForCompare.length > 0 && !compareBtn) {
        const container = document.querySelector('.page-info');
        compareBtn = document.createElement('button');
        compareBtn.id = 'compare-selected-btn';
        compareBtn.className = 'compare-selected-button';
        compareBtn.onclick = navigateToCompare;
        container.appendChild(compareBtn);
    }
    
    if (compareBtn) {
        if (selectedForCompare.length === 0) {
            compareBtn.remove();
        } else {
            compareBtn.textContent = `🔄 Compare ${selectedForCompare.length} Stock${selectedForCompare.length > 1 ? 's' : ''}`;
            compareBtn.disabled = selectedForCompare.length < 2;
        }
    }
}

function navigateToCompare() {
    if (selectedForCompare.length < 2) {
        showNotification('Please select at least 2 stocks to compare', 'error');
        return;
    }
    
    const tickers = selectedForCompare.join(',');
    window.location.href = `compare.html?tickers=${tickers}`;
}

// Refresh function for auto-refresh
window.refreshCurrentPage = loadFavoritesPage;
