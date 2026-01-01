/**
 * Service Worker for Stock Screener Pro PWA
 * Provides offline support and caching for better performance
 */

const CACHE_NAME = 'stock-screener-v5';
const STATIC_CACHE = 'static-v5';
const DATA_CACHE = 'data-v5';

// Static assets to cache immediately
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/home.html',
    '/hot-stocks.html',
    '/watch-list.html',
    '/chart-viewer.html',
    '/compare.html',
    '/favorites.html',
    '/market-overview.html',
    '/filtered-stocks.html',
    '/export.html',
    '/styles.css',
    '/common.js',
    '/home.js',
    '/stocks-page.js',
    '/chart-viewer.js',
    '/compare.js',
    '/favorites.js',
    '/market-overview.js',
    '/stock-notes.js'
];

// External CDN resources to cache
const CDN_RESOURCES = [
    'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js',
    'https://cdn.jsdelivr.net/npm/luxon@2.3.0/build/global/luxon.min.js',
    'https://cdn.jsdelivr.net/npm/chartjs-adapter-luxon@1.1.0/dist/chartjs-adapter-luxon.min.js',
    'https://cdn.jsdelivr.net/npm/chartjs-chart-financial@0.1.1/dist/chartjs-chart-financial.min.js'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');
    
    event.waitUntil(
        Promise.all([
            // Cache static assets
            caches.open(STATIC_CACHE).then((cache) => {
                console.log('[Service Worker] Caching static assets');
                return cache.addAll(STATIC_ASSETS.map(url => {
                    return new Request(url, { cache: 'no-cache' });
                })).catch(err => {
                    console.log('[Service Worker] Some static assets failed to cache:', err);
                });
            }),
            // Cache CDN resources
            caches.open(STATIC_CACHE).then((cache) => {
                console.log('[Service Worker] Caching CDN resources');
                return Promise.all(CDN_RESOURCES.map(url => {
                    return fetch(url)
                        .then(response => cache.put(url, response))
                        .catch(err => console.log('[Service Worker] Failed to cache CDN:', url, err));
                }));
            })
        ]).then(() => {
            console.log('[Service Worker] Installation complete');
            return self.skipWaiting();
        })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== STATIC_CACHE && cacheName !== DATA_CACHE) {
                        console.log('[Service Worker] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('[Service Worker] Activation complete');
            return self.clients.claim();
        })
    );
});

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Handle different types of requests
    if (url.pathname.endsWith('.json')) {
        // JSON data files - Network first, cache fallback
        event.respondWith(networkFirstStrategy(request, DATA_CACHE));
    } else if (STATIC_ASSETS.includes(url.pathname) || url.hostname !== location.hostname) {
        // Static assets and CDN - Cache first, network fallback
        event.respondWith(cacheFirstStrategy(request, STATIC_CACHE));
    } else {
        // Everything else - Network first
        event.respondWith(networkFirstStrategy(request, STATIC_CACHE));
    }
});

/**
 * Cache first strategy - Try cache, fall back to network
 */
async function cacheFirstStrategy(request, cacheName) {
    try {
        const cache = await caches.open(cacheName);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            // Reduced logging for performance
            // console.log('[Service Worker] Cache hit:', request.url);
            return cachedResponse;
        }
        
        // console.log('[Service Worker] Cache miss, fetching:', request.url);
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[Service Worker] Fetch failed:', request.url, error);
        
        // Return offline fallback page for navigation requests
        if (request.mode === 'navigate') {
            return caches.match('/index.html');
        }
        
        throw error;
    }
}

/**
 * Network first strategy - Try network, fall back to cache
 */
async function networkFirstStrategy(request, cacheName) {
    try {
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[Service Worker] Network failed, trying cache:', request.url);
        
        const cache = await caches.open(cacheName);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline fallback for navigation requests
        if (request.mode === 'navigate') {
            return caches.match('/index.html');
        }
        
        throw error;
    }
}

// Listen for messages from the main app
self.addEventListener('message', (event) => {
    console.log('[Service Worker] Message received:', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CLEAR_CACHE') {
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => caches.delete(cacheName))
            );
        }).then(() => {
            event.ports[0].postMessage({ status: 'Cache cleared' });
        });
    }
});

// Push notification handling (for future server-side push)
self.addEventListener('push', (event) => {
    console.log('[Service Worker] Push received');
    
    const options = {
        body: event.data ? event.data.text() : 'Stock update!',
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'view',
                title: 'View Chart'
            },
            {
                action: 'dismiss',
                title: 'Dismiss'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('Stock Screener', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    console.log('[Service Worker] Notification clicked:', event.action);
    
    event.notification.close();
    
    if (event.action === 'view' || !event.action) {
        event.waitUntil(
            clients.openWindow('/hot-stocks.html')
        );
    }
});

console.log('[Service Worker] Script loaded');
