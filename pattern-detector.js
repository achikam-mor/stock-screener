// Pattern Detector page functionality
// Displays all stocks with filtering capabilities for patterns, crosses, and cup & handle formations
let allStocks = [];
let filteredStocks = [];
let currentPage = 1;
let stocksPerPage = 20;
let sectorsData = null;

// Adjust stocks per page based on screen size
function updateStocksPerPage() {
    if (window.innerWidth <= 768) {
        stocksPerPage = 10; // Show 10 stocks per page on mobile
    } else {
        stocksPerPage = 20; // Show 20 stocks per page on desktop
    }
}

function initPatternDetectorPage() {
    updateStocksPerPage();
    loadPatternDetectorData();
    
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
    
    // Re-apply filters when favorites change (if favorites filter is active)
    window.addEventListener('favoritesChanged', () => {
        const favoritesFilter = document.getElementById('favorites-filter');
        if (favoritesFilter && favoritesFilter.value !== 'all') {
            applyFilters();
        }
    });
}

async function loadPatternDetectorData() {
    const data = await loadResults();
    if (!data) {
        showError();
        return;
    }

    globalData = data;
    updateTimestamp(data);

    // Get all stocks with patterns data
    allStocks = data.all_stocks_with_patterns || [];
    filteredStocks = [...allStocks];

    // Update total count
    document.getElementById('total-stocks').textContent = filteredStocks.length;

    // Load sector filter options (sectors are already in the data)
    populateSectorFilterFromData();

    // Check if we should scroll to a specific ticker (from search redirect)
    const urlParams = new URLSearchParams(window.location.search);
    const tickerToFind = urlParams.get('ticker');
    
    if (tickerToFind) {
        // Find which page the ticker is on
        const tickerIndex = filteredStocks.findIndex(s => s.symbol === tickerToFind.toUpperCase());
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

function populateSectorFilterFromData() {
    const sectorSelect = document.getElementById('sector-filter');
    if (!sectorSelect || !allStocks) return;
    
    // Get unique sectors from all stocks
    const sectors = new Set();
    allStocks.forEach(stock => {
        if (stock.sector && stock.sector !== 'Unknown') {
            sectors.add(stock.sector);
        }
    });
    
    // Sort sectors alphabetically
    const sortedSectors = Array.from(sectors).sort();
    
    // Clear existing options except "All"
    sectorSelect.innerHTML = '<option value="all">All Sectors</option>';
    
    // Add sector options
    sortedSectors.forEach(sector => {
        const count = allStocks.filter(s => s.sector === sector).length;
        const option = document.createElement('option');
        option.value = sector;
        option.textContent = `${sector} (${count})`;
        sectorSelect.appendChild(option);
    });
}

function applyFilters() {
    const smaStatusFilter = document.getElementById('sma-status-filter').value;
    const smaDistanceFilter = document.getElementById('sma-distance-filter').value;
    const patternFilter = document.getElementById('pattern-filter').value;
    const crossFilter = document.getElementById('cross-filter').value;
    const cupHandleFilter = document.getElementById('cup-handle-filter').value;
    const sectorFilter = document.getElementById('sector-filter').value;
    const favoritesFilter = document.getElementById('favorites-filter').value;
    const atrFilter = document.getElementById('atr-filter').value;
    const volumeFilter = document.getElementById('volume-filter').value;
    const favorites = getFavorites();
    
    console.log('[Pattern Detector] Applying filters:', { 
        smaStatusFilter, smaDistanceFilter, patternFilter, crossFilter, 
        cupHandleFilter, sectorFilter, favoritesFilter, atrFilter, volumeFilter 
    });
    
    filteredStocks = allStocks.filter(stock => {
        // SMA Status filter (above/below SMA150)
        if (smaStatusFilter !== 'all') {
            if (smaStatusFilter === 'above' && stock.distance_percent < 0) return false;
            if (smaStatusFilter === 'below' && stock.distance_percent >= 0) return false;
        }
        
        // SMA Distance filter (absolute value)
        if (smaDistanceFilter !== 'all') {
            const absDistance = Math.abs(stock.distance_percent);
            const [min, max] = smaDistanceFilter.split('-').map(Number);
            if (absDistance < min || absDistance >= max) return false;
        }
        
        // Candlestick Pattern filter
        if (patternFilter !== 'all') {
            // If "any_pattern" is selected, just check if patterns exist
            if (patternFilter === 'any_pattern') {
                if (!stock.patterns || stock.patterns.length === 0) return false;
            } else {
                // If no patterns array or empty, filter out
                if (!stock.patterns || stock.patterns.length === 0) return false;
                
                const hasPattern = stock.patterns.some(p => {
                    if (patternFilter === 'bullish_confirmed') return p.signal === 'bullish' && p.status === 'confirmed';
                    if (patternFilter === 'pending_bullish') return p.signal === 'bullish' && p.status === 'pending';
                    if (patternFilter === 'pending_bearish') return p.signal === 'bearish' && p.status === 'pending';
                    if (patternFilter === 'bearish_confirmed') return p.signal === 'bearish' && p.status === 'confirmed';
                    return false;
                });
                if (!hasPattern) return false;
            }
        }
        
        // Golden/Death Cross filter
        if (crossFilter !== 'all') {
            if (crossFilter === 'golden' && !stock.golden_cross) return false;
            if (crossFilter === 'death' && !stock.death_cross) return false;
            if (crossFilter === 'any' && !stock.golden_cross && !stock.death_cross) return false;
        }
        
        // Cup and Handle Pattern filter
        if (cupHandleFilter !== 'all') {
            // If no cup_handle_patterns array or empty, filter out
            if (!stock.cup_handle_patterns || stock.cup_handle_patterns.length === 0) return false;
            
            const hasCupHandle = stock.cup_handle_patterns.some(p => {
                if (cupHandleFilter === 'confirmed') return p.status === 'confirmed';
                if (cupHandleFilter === 'forming') return p.status === 'forming';
                if (cupHandleFilter === 'any') return true;
                return false;
            });
            if (!hasCupHandle) return false;
        }
        
        // Sector filter
        if (sectorFilter !== 'all') {
            if (stock.sector !== sectorFilter) return false;
        }
        
        // Favorites filter
        if (favoritesFilter === 'favorites') {
            if (!favorites.includes(stock.symbol)) return false;
        } else if (favoritesFilter === 'non-favorites') {
            if (favorites.includes(stock.symbol)) return false;
        }
        
        // ATR % filter
        if (atrFilter !== 'all') {
            const atrPct = stock.atr_percent || 0;
            const [min, max] = atrFilter.split('-').map(Number);
            if (atrPct < min || atrPct >= max) return false;
        }
        
        // Volume filter
        if (volumeFilter !== 'all') {
            const volumeRatio = stock.avg_volume_14d > 0 ? (stock.last_volume / stock.avg_volume_14d) : 0;
            if (volumeFilter === 'above' && volumeRatio < 1) return false;
            if (volumeFilter === 'below' && volumeRatio >= 1) return false;
            if (volumeFilter === 'high' && volumeRatio < 1.5) return false;
        }
        
        return true;
    });
    
    // Reset to page 1 when filters change
    currentPage = 1;
    
    // Update total count
    document.getElementById('total-stocks').textContent = filteredStocks.length;
    
    console.log(`[Pattern Detector] Filtered to ${filteredStocks.length} stocks`);
    
    displayCurrentPage();
    setupPagination();
}

function resetFilters() {
    document.getElementById('sma-status-filter').value = 'all';
    document.getElementById('sma-distance-filter').value = 'all';
    document.getElementById('pattern-filter').value = 'all';
    document.getElementById('cross-filter').value = 'all';
    document.getElementById('cup-handle-filter').value = 'all';
    document.getElementById('sector-filter').value = 'all';
    document.getElementById('favorites-filter').value = 'all';
    document.getElementById('atr-filter').value = 'all';
    document.getElementById('volume-filter').value = 'all';
    
    console.log('[Pattern Detector] Filters reset');
    applyFilters();
}

function displayCurrentPage() {
    const container = document.getElementById('stocks-container');
    const startIndex = (currentPage - 1) * stocksPerPage;
    const endIndex = Math.min(startIndex + stocksPerPage, filteredStocks.length);
    const pageStocks = filteredStocks.slice(startIndex, endIndex);

    if (pageStocks.length === 0) {
        container.innerHTML = '<div class="loading">No stocks found matching your filters</div>';
        return;
    }

    container.innerHTML = pageStocks.map(stock => createCompactStockCard(stock)).join('');

    // Update page info
    document.getElementById('current-page').textContent = currentPage;
}

function renderPatternDots(patterns) {
    if (!patterns || patterns.length === 0) {
        return '<span class="no-patterns">—</span>';
    }
    
    // Sort patterns by date (oldest first) for left-to-right chronological display
    const sortedPatterns = [...patterns].sort((a, b) => a.date.localeCompare(b.date));
    
    return sortedPatterns.map(pattern => {
        const { signal, status, confidence, days_ago, pattern: patternName, date } = pattern;
        
        // Determine color class
        let colorClass = '';
        if (signal === 'bullish' && status === 'confirmed') colorClass = 'pattern-dot-green';
        else if (signal === 'bullish' && status === 'pending') colorClass = 'pattern-dot-yellow';
        else if (signal === 'bearish' && status === 'pending') colorClass = 'pattern-dot-orange';
        else if (signal === 'bearish' && status === 'confirmed') colorClass = 'pattern-dot-red';
        
        // Format pattern name for display
        const displayName = patternName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const statusIcon = status === 'confirmed' ? '✅' : '⏳';
        
        // Format date (MM/DD)
        const dateObj = new Date(date);
        const formattedDate = `${dateObj.getMonth() + 1}/${dateObj.getDate()}`;
        
        // Create tooltip
        const tooltip = `Pattern: ${displayName} | Signal: ${signal.charAt(0).toUpperCase() + signal.slice(1)} | Status: ${status.charAt(0).toUpperCase() + status.slice(1)} ${statusIcon} | Date: ${date} | Confidence: ${confidence}%`;
        
        return `<div class="pattern-item"><span class="pattern-dot ${colorClass}" title="${tooltip}"></span><span class="pattern-date">${formattedDate}</span></div>`;
    }).join('');
}

function renderCupHandleDots(cupHandlePatterns) {
    if (!cupHandlePatterns || cupHandlePatterns.length === 0) {
        return '';
    }
    
    return cupHandlePatterns.map(pattern => {
        const { status, confidence, breakout_date, rim_price, profit_target, depth_percent, handle_shape } = pattern;
        
        // Determine color and icon
        let colorClass = status === 'confirmed' ? 'cup-handle-confirmed' : 'cup-handle-forming';
        let icon = status === 'confirmed' ? '☕✅' : '🏺';
        
        // Format handle shape for display
        const shapeDisplay = handle_shape ? handle_shape.charAt(0).toUpperCase() + handle_shape.slice(1) : 'Unknown';
        
        // Handle shape emoji
        let shapeEmoji = '';
        if (handle_shape === 'drift') shapeEmoji = '📉';
        else if (handle_shape === 'pennant') shapeEmoji = '🔻';
        else if (handle_shape === 'flag') shapeEmoji = '🏳️';
        
        // Format breakout date
        let dateDisplay = '';
        if (breakout_date) {
            const dateObj = new Date(breakout_date);
            dateDisplay = `${dateObj.getMonth() + 1}/${dateObj.getDate()}`;
        } else {
            dateDisplay = 'Forming';
        }
        
        // Create tooltip with key information including handle shape
        const tooltip = `Cup & Handle ${status.toUpperCase()} | Handle: ${shapeEmoji} ${shapeDisplay} | Rim: $${rim_price} | Target: $${profit_target} (+${depth_percent.toFixed(1)}%) | Confidence: ${confidence}% | ${dateDisplay}`;
        
        return `<span class="cup-handle-icon ${colorClass}" title="${tooltip}">${icon}</span>`;
    }).join('');
}

function createCompactStockCard(stock) {
    const volumeRatio = stock.avg_volume_14d > 0 
        ? (stock.last_volume / stock.avg_volume_14d).toFixed(2) 
        : '0.00';
    
    // Create note icon HTML (function from stock-notes.js if available)
    const noteIconHTML = typeof createNoteIconHTML === 'function' 
        ? createNoteIconHTML(stock.symbol) 
        : '';
    
    // Create cross icon HTML
    let crossIconHTML = '';
    if (stock.golden_cross) {
        crossIconHTML = '<span class="cross-icon golden-cross" title="Golden Cross (50 SMA crossed above 200 SMA)">✨</span>';
    } else if (stock.death_cross) {
        crossIconHTML = '<span class="cross-icon death-cross" title="Death Cross (50 SMA crossed below 200 SMA)">💀</span>';
    }
    
    // Create pattern dots HTML
    const patternDotsHTML = renderPatternDots(stock.patterns);
    
    // Create cup and handle dots HTML
    const cupHandleHTML = renderCupHandleDots(stock.cup_handle_patterns);
    
    // Add SMA status badge
    const smaStatusClass = stock.distance_percent >= 0 ? 'above-sma' : 'below-sma';
    const smaStatusText = stock.distance_percent >= 0 ? 'Above SMA150' : 'Below SMA150';
    const smaStatusBadge = `<span class="sma-status-badge ${smaStatusClass}">${smaStatusText}</span>`;
    
    return `
        <div class="stock-card-compact" data-ticker="${stock.symbol}">
            <div class="stock-header">
                <div class="stock-symbol">
                    ${createFavoriteStarHTML(stock.symbol)}
                    ${noteIconHTML}
                    ${crossIconHTML}
                    ${cupHandleHTML}
                    <input type="checkbox" class="compare-checkbox" value="${stock.symbol}" 
                           onchange="toggleCompareStock('${stock.symbol}')" 
                           title="Select for comparison">
                    ${stock.symbol}
                    ${smaStatusBadge}
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
                ${stock.sector && stock.sector !== 'Unknown' ? `
                <div class="data-row">
                    <span class="label">Sector</span>
                    <span class="value">${stock.sector}</span>
                </div>
                ` : ''}
                <div class="data-row">
                    <span class="label">ATR14</span>
                    <span class="value">${stock.atr !== null ? '$' + stock.atr.toFixed(2) + ' (' + stock.atr_percent.toFixed(2) + '%)' : 'N/A'}</span>
                </div>
                <div class="data-row">
                    <span class="label">Volume</span>
                    <span class="value">${(stock.last_volume / 1000000).toFixed(2)}M</span>
                </div>
                <div class="data-row">
                    <span class="label">Avg Vol 14d</span>
                    <span class="value">${(stock.avg_volume_14d / 1000000).toFixed(2)}M (${volumeRatio}x)</span>
                </div>
                <div class="data-row">
                    <span class="label">Patterns (7d)</span>
                    <span class="value pattern-dots-container">${patternDotsHTML}</span>
                </div>
            </div>
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
    currentPage = page;
    displayCurrentPage();
    setupPagination();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showError() {
    const container = document.getElementById('stocks-container');
    container.innerHTML = `
        <div class="error">
            ⚠️ Unable to load pattern detector data. Please try again later or check if results.json exists.
        </div>
    `;
}

// Refresh function for auto-refresh
window.refreshCurrentPage = loadPatternDetectorData;

// Comparison functionality
let selectedForCompare = [];

function toggleCompareStock(symbol) {
    const checkbox = document.querySelector(`.compare-checkbox[value="${symbol}"]`);
    
    if (checkbox && checkbox.checked) {
        if (selectedForCompare.length >= 3) {
            showCompareNotification('Maximum 3 stocks can be compared at once', 'error');
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
        // Create compare button
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
        showCompareNotification('Please select at least 2 stocks to compare', 'error');
        return;
    }
    
    const tickers = selectedForCompare.join(',');
    window.location.href = `compare.html?tickers=${tickers}`;
}

function showCompareNotification(message, type) {
    const notification = document.getElementById('search-notification');
    notification.textContent = message;
    notification.className = `search-notification ${type}`;
    notification.style.display = 'flex';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

// Initialize page on load
initPatternDetectorPage();
