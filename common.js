// Common functionality shared across all pages
let globalData = null;

// ============================================
// LAZY-LOAD ADSENSE WITH INTERSECTION OBSERVER
// ============================================

/**
 * Enhanced AdSense loading with Intersection Observer
 * Ads are only initialized when they come into view
 * This dramatically improves viewability metrics
 */
function lazyLoadAdSense() {
    if (document.readyState === 'complete') {
        initAdSenseWithObserver();
    } else {
        window.addEventListener('load', initAdSenseWithObserver);
    }
}

function initAdSenseWithObserver() {
    // Check if AdSense script already loaded
    if (document.querySelector('script[src*="adsbygoogle"]')) {
        console.log('[AdSense] Script already loaded');
        setupIntersectionObserver();
        return;
    }

    console.log('[AdSense] Loading script...');
    const script = document.createElement('script');
    script.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9520776475659458';
    script.async = true;
    script.crossOrigin = 'anonymous';
    script.onload = () => {
        console.log('[AdSense] Script loaded');
        setupIntersectionObserver();
        initializeStickyAnchorAd();
    };
    script.onerror = () => {
        console.log('[AdSense] Failed to load (ad blocker?)');
    };
    document.head.appendChild(script);
}

/**
 * Intersection Observer for lazy-loading ads when visible
 * Only loads ads when they're about to enter viewport
 */
function setupIntersectionObserver() {
    const adContainers = document.querySelectorAll('.ad-container:not(.ad-sticky-anchor)');
    
    if (!('IntersectionObserver' in window)) {
        // Fallback for older browsers - load all ads immediately
        initializeAllAds();
        return;
    }

    const observerOptions = {
        root: null,
        rootMargin: '200px 0px', // Start loading 200px before ad comes into view
        threshold: 0
    };

    const adObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const container = entry.target;
                const ad = container.querySelector('.adsbygoogle');
                
                if (ad && !ad.dataset.adsbygoogleStatus) {
                    try {
                        (window.adsbygoogle = window.adsbygoogle || []).push({});
                        console.log('[AdSense] Initialized visible ad');
                        container.classList.add('ad-loaded');
                    } catch (e) {
                        console.error('[AdSense] Error initializing ad:', e);
                    }
                }
                observer.unobserve(container);
            }
        });
    }, observerOptions);

    adContainers.forEach(container => {
        adObserver.observe(container);
    });
}

/**
 * Fallback: Initialize all ads immediately (for older browsers)
 */
function initializeAllAds() {
    const ads = document.querySelectorAll('.adsbygoogle');
    ads.forEach((ad, index) => {
        if (!ad.dataset.adsbygoogleStatus) {
            try {
                (window.adsbygoogle = window.adsbygoogle || []).push({});
                console.log(`[AdSense] Initialized ad ${index + 1}`);
            } catch (e) {
                console.error(`[AdSense] Error initializing ad ${index + 1}:`, e);
            }
        }
    });
}

/**
 * Create and initialize sticky anchor ad at bottom of page
 * High viewability = higher CPM
 */
function initializeStickyAnchorAd() {
    // Check if sticky anchor already exists or was closed this session
    if (document.querySelector('.ad-sticky-anchor') || sessionStorage.getItem('stickyAdClosed') === 'true') {
        return;
    }

    // Create sticky anchor container
    const stickyAnchor = document.createElement('div');
    stickyAnchor.className = 'ad-container ad-sticky-anchor';
    stickyAnchor.innerHTML = `
        <button class="ad-sticky-close" onclick="closeStickyAd()" aria-label="Close ad">×</button>
        <ins class="adsbygoogle"
             style="display:block; min-height:50px; width:100%;"
             data-ad-client="ca-pub-9520776475659458"
             data-ad-slot="8162731200"
             data-ad-format="horizontal"
             data-full-width-responsive="true"></ins>
    `;
    
    document.body.appendChild(stickyAnchor);
    
    // Initialize the sticky ad after a small delay
    setTimeout(() => {
        try {
            (window.adsbygoogle = window.adsbygoogle || []).push({});
            console.log('[AdSense] Sticky anchor ad initialized');
            
            // Check if ad actually filled after 3 seconds
            setTimeout(() => {
                const adElement = stickyAnchor.querySelector('.adsbygoogle');
                const adStatus = adElement ? adElement.getAttribute('data-adsbygoogle-status') : null;
                const hasIframe = stickyAnchor.querySelector('iframe');
                
                // Hide container if ad didn't load (no iframe or unfilled status)
                if (!hasIframe && adStatus !== 'done') {
                    console.log('[AdSense] Sticky anchor ad did not fill, hiding container');
                    stickyAnchor.style.display = 'none';
                }
            }, 3000);
        } catch (e) {
            console.error('[AdSense] Sticky anchor error:', e);
            stickyAnchor.style.display = 'none';
        }
    }, 1000);
}

/**
 * Close sticky anchor ad
 */
function closeStickyAd() {
    const stickyAd = document.querySelector('.ad-sticky-anchor');
    if (stickyAd) {
        stickyAd.style.display = 'none';
        // Remember user preference for this session
        sessionStorage.setItem('stickyAdClosed', 'true');
    }
}

/**
 * In-feed ad insertion for stock grids
 * Call this after rendering stock cards
 * @param {string} containerId - ID of the stocks container
 * @param {number} insertAfter - Insert ad after this many cards (default: 8)
 */
function insertInFeedAd(containerId, insertAfter = 8) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const cards = container.querySelectorAll('.stock-card-compact');
    if (cards.length <= insertAfter) return;
    
    // Check if in-feed ad already exists
    if (container.querySelector('.ad-infeed')) return;
    
    // Create in-feed ad
    const adCard = document.createElement('div');
    adCard.className = 'stock-card-compact ad-infeed';
    adCard.innerHTML = `
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="ca-pub-9520776475659458"
             data-ad-slot="4768070238"
             data-ad-format="fluid"
             data-ad-layout-key="-6t+ed+2i-1n-4w"></ins>
    `;
    
    // Insert after the specified number of cards
    const targetCard = cards[insertAfter - 1];
    if (targetCard && targetCard.nextSibling) {
        container.insertBefore(adCard, targetCard.nextSibling);
    } else {
        container.appendChild(adCard);
    }
    
    // Initialize the in-feed ad
    setTimeout(() => {
        try {
            (window.adsbygoogle = window.adsbygoogle || []).push({});
            console.log('[AdSense] In-feed ad initialized');
        } catch (e) {
            console.error('[AdSense] In-feed ad error:', e);
        }
    }, 100);
}

// Initialize lazy AdSense loading
lazyLoadAdSense();

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
                // Force update: unregister old service workers first
                const registrations = await navigator.serviceWorker.getRegistrations();
                for (const registration of registrations) {
                    await registration.unregister();
                    console.log('[PWA] Unregistered old service worker');
                }
                
                // Register new service worker
                const registration = await navigator.serviceWorker.register('service-worker.js');
                console.log('[PWA] Service Worker registered:', registration.scope);
                
                // Force immediate activation
                if (registration.waiting) {
                    registration.waiting.postMessage({ type: 'SKIP_WAITING' });
                }
                
                // Listen for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    console.log('[PWA] New Service Worker installing...');
                    
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // New content is available
                            console.log('[PWA] New content available');
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
