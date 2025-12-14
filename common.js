// Common functionality shared across all pages
let globalData = null;

// ============================================
// PWA SERVICE WORKER REGISTRATION
// ============================================

/**
 * Register the service worker for PWA functionality
 */
function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', async () => {
            try {
                const registration = await navigator.serviceWorker.register('/service-worker.js');
                console.log('[PWA] Service Worker registered:', registration.scope);
                
                // Listen for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    console.log('[PWA] New Service Worker installing...');
                    
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // New content is available
                            console.log('[PWA] New content available, refresh to update');
                            showNotification('App update available! Refresh to get the latest version.', 'info');
                        }
                    });
                });
            } catch (error) {
                console.log('[PWA] Service Worker registration failed:', error);
            }
        });
    }
}

// Initialize service worker
registerServiceWorker();

// ============================================
// FAVORITES MANAGEMENT (localStorage-based)
// ============================================

const FAVORITES_STORAGE_KEY = 'stock_favorites';

// Get all favorite tickers from localStorage
function getFavorites() {
    try {
        const favorites = localStorage.getItem(FAVORITES_STORAGE_KEY);
        return favorites ? JSON.parse(favorites) : [];
    } catch (e) {
        console.error('Error reading favorites from localStorage:', e);
        return [];
    }
}

// Save favorites to localStorage
function saveFavorites(favorites) {
    try {
        localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(favorites));
    } catch (e) {
        console.error('Error saving favorites to localStorage:', e);
    }
}

// Check if a ticker is a favorite
function isFavorite(ticker) {
    const favorites = getFavorites();
    return favorites.includes(ticker);
}

// Toggle favorite status for a ticker
function toggleFavorite(ticker, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    const favorites = getFavorites();
    const index = favorites.indexOf(ticker);
    
    if (index === -1) {
        // Add to favorites
        favorites.push(ticker);
        showNotification(`${ticker} added to favorites ⭐`, 'success');
    } else {
        // Remove from favorites
        favorites.splice(index, 1);
        showNotification(`${ticker} removed from favorites`, 'info');
    }
    
    saveFavorites(favorites);
    updateAllFavoriteStars();
    
    // Dispatch custom event for pages to react
    window.dispatchEvent(new CustomEvent('favoritesChanged', { detail: { ticker, isFavorite: index === -1 } }));
}

// Update all favorite star icons on the current page
function updateAllFavoriteStars() {
    const stars = document.querySelectorAll('.favorite-star');
    const favorites = getFavorites();
    
    stars.forEach(star => {
        const ticker = star.dataset.ticker;
        if (favorites.includes(ticker)) {
            star.classList.add('is-favorite');
            star.textContent = '★';
            star.title = 'Remove from favorites';
        } else {
            star.classList.remove('is-favorite');
            star.textContent = '☆';
            star.title = 'Add to favorites';
        }
    });
}

// Create a favorite star HTML element
function createFavoriteStarHTML(ticker) {
    const isFav = isFavorite(ticker);
    return `
        <span class="favorite-star ${isFav ? 'is-favorite' : ''}" 
              data-ticker="${ticker}" 
              onclick="toggleFavorite('${ticker}', event)"
              title="${isFav ? 'Remove from favorites' : 'Add to favorites'}">
            ${isFav ? '★' : '☆'}
        </span>
    `;
}

// ============================================
// END FAVORITES MANAGEMENT
// ============================================

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
                timeZone: 'America/New_York'
            })} (New York Time)`;
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

    // Search in failed tickers - show message but don't offer redirect to failed page
    const inFailed = globalData.failed_tickers.includes(ticker);
    if (inFailed) {
        // Just show a notification that this stock's data couldn't be fetched
        // Don't offer to redirect to failed stocks page
        showNotification(`Ticker "${ticker}" data unavailable (failed to fetch)`, 'error');
        return;
    }

    // Search in filtered by SMA (stocks that didn't meet the ±4% SMA distance criteria)
    const inFiltered = globalData.filtered_by_sma && globalData.filtered_by_sma.includes(ticker);
    if (inFiltered) {
        handleSearchResult('filtered', ticker, 'Filtered Stocks');
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
        'failed': 'failed-tickers.html',
        'filtered': 'filtered-stocks.html'
    };

    // If ticker is on current page, scroll to it
    if ((currentPage === 'hot-stocks.html' && foundIn === 'hot') ||
        (currentPage === 'watch-list.html' && foundIn === 'watch') ||
        (currentPage === 'failed-tickers.html' && foundIn === 'failed') ||
        (currentPage === 'filtered-stocks.html' && foundIn === 'filtered')) {
        
        scrollToTicker(ticker);
        return;
    }

    // Ticker is on a different page - show notification with redirect option
    showNotificationWithRedirect(ticker, listName, pageMap[foundIn]);
}

// Scroll to ticker on current page
function scrollToTicker(ticker) {
    // For stocks pages (hot/watch), we need to find which page the ticker is on
    if (typeof allStocks !== 'undefined' && allStocks.length > 0) {
        const tickerIndex = allStocks.findIndex(s => s.symbol === ticker);
        if (tickerIndex >= 0) {
            // Calculate which page the ticker is on
            const targetPage = Math.floor(tickerIndex / stocksPerPage) + 1;
            
            // If we're not on the right page, go to it first
            if (typeof currentPage !== 'undefined' && currentPage !== targetPage) {
                if (typeof goToPage === 'function') {
                    goToPage(targetPage);
                }
            }
            
            // Wait a bit for the page to render
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
                    showNotification(`Ticker "${ticker}" not found`, 'error');
                }
            }, 300);
            return;
        }
    }
    
    // For filtered stocks page - array of ticker strings
    if (typeof filteredStocks !== 'undefined' && filteredStocks.length > 0) {
        const tickerIndex = filteredStocks.findIndex(t => t === ticker);
        if (tickerIndex >= 0) {
            // Calculate which page the ticker is on
            const targetPage = Math.floor(tickerIndex / stocksPerPage) + 1;
            
            // If we're not on the right page, go to it first
            if (typeof currentPage !== 'undefined' && currentPage !== targetPage) {
                if (typeof goToPage === 'function') {
                    goToPage(targetPage);
                }
            }
            
            // Wait a bit for the page to render
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
                    showNotification(`Ticker "${ticker}" not found`, 'error');
                }
            }, 300);
            return;
        }
    }
    
    // Fallback for non-paginated pages or failed tickers page
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
function showNotification(message, type, duration = 3000) {
    const notification = document.getElementById('search-notification');
    if (!notification) return;
    
    notification.textContent = message;
    notification.className = `search-notification ${type}`;
    notification.style.display = 'block';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, duration);
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
