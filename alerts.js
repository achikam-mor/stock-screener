/**
 * Price Alerts Feature - Browser notifications for stock price movements
 * Uses localStorage to store alert thresholds and Service Worker for background checking
 */

const ALERTS_STORAGE_KEY = 'stock_price_alerts';
const LAST_PRICES_KEY = 'stock_last_prices';

// ============================================
// ALERTS MANAGEMENT
// ============================================

/**
 * Get all alerts from localStorage
 */
function getAllAlerts() {
    try {
        const alerts = localStorage.getItem(ALERTS_STORAGE_KEY);
        return alerts ? JSON.parse(alerts) : {};
    } catch (e) {
        console.error('[Alerts] Error reading alerts:', e);
        return {};
    }
}

/**
 * Save all alerts to localStorage
 */
function saveAllAlerts(alerts) {
    try {
        localStorage.setItem(ALERTS_STORAGE_KEY, JSON.stringify(alerts));
        console.log('[Alerts] Alerts saved:', Object.keys(alerts).length);
    } catch (e) {
        console.error('[Alerts] Error saving alerts:', e);
    }
}

/**
 * Get alert for a specific ticker
 */
function getAlert(ticker) {
    const alerts = getAllAlerts();
    return alerts[ticker] || null;
}

/**
 * Create or update alert for a ticker
 */
function setAlert(ticker, config) {
    const alerts = getAllAlerts();
    alerts[ticker] = {
        ...config,
        created: new Date().toISOString()
    };
    saveAllAlerts(alerts);
    updateAlertIcons();
    return alerts[ticker];
}

/**
 * Remove alert for a ticker
 */
function removeAlert(ticker) {
    const alerts = getAllAlerts();
    delete alerts[ticker];
    saveAllAlerts(alerts);
    updateAlertIcons();
}

/**
 * Check if a ticker has an alert
 */
function hasAlert(ticker) {
    const alerts = getAllAlerts();
    return !!alerts[ticker];
}

// ============================================
// NOTIFICATION PERMISSION
// ============================================

/**
 * Request notification permission
 */
async function requestNotificationPermission() {
    if (!('Notification' in window)) {
        console.log('[Alerts] Browser does not support notifications');
        return false;
    }
    
    if (Notification.permission === 'granted') {
        return true;
    }
    
    if (Notification.permission !== 'denied') {
        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }
    
    return false;
}

/**
 * Check if notifications are enabled
 */
function notificationsEnabled() {
    return 'Notification' in window && Notification.permission === 'granted';
}

// ============================================
// ALERT CHECKING
// ============================================

/**
 * Check all alerts against current prices
 */
async function checkAlerts(resultsData) {
    if (!resultsData) {
        console.log('[Alerts] No results data for alert checking');
        return;
    }
    
    const alerts = getAllAlerts();
    const alertTickers = Object.keys(alerts);
    
    if (alertTickers.length === 0) {
        console.log('[Alerts] No alerts to check');
        return;
    }
    
    console.log(`[Alerts] Checking ${alertTickers.length} alerts...`);
    
    // Combine all stocks from results
    const allStocks = [
        ...(resultsData.hot_stocks || []),
        ...(resultsData.watch_list || [])
    ];
    
    const triggeredAlerts = [];
    
    for (const ticker of alertTickers) {
        const alert = alerts[ticker];
        const stock = allStocks.find(s => s.symbol === ticker);
        
        if (!stock) continue;
        
        const currentPrice = stock.last_close;
        let triggered = false;
        let message = '';
        
        // Check above threshold
        if (alert.above && currentPrice >= alert.above) {
            triggered = true;
            message = `${ticker} is above $${alert.above} (now $${currentPrice.toFixed(2)})`;
        }
        
        // Check below threshold
        if (alert.below && currentPrice <= alert.below) {
            triggered = true;
            message = `${ticker} is below $${alert.below} (now $${currentPrice.toFixed(2)})`;
        }
        
        // Check percent change from SMA
        if (alert.smaDistance) {
            const distance = stock.distance_percent;
            if (alert.smaDistance.above && distance >= alert.smaDistance.above) {
                triggered = true;
                message = `${ticker} is ${distance.toFixed(2)}% above SMA150`;
            }
            if (alert.smaDistance.below && distance <= alert.smaDistance.below) {
                triggered = true;
                message = `${ticker} is ${Math.abs(distance).toFixed(2)}% below SMA150`;
            }
        }
        
        if (triggered) {
            triggeredAlerts.push({ ticker, message, alert });
        }
    }
    
    // Send notifications for triggered alerts
    for (const { ticker, message, alert } of triggeredAlerts) {
        await sendAlertNotification(ticker, message);
        
        // Remove one-time alerts after triggering
        if (alert.oneTime) {
            removeAlert(ticker);
        }
    }
    
    console.log(`[Alerts] ${triggeredAlerts.length} alerts triggered`);
}

/**
 * Send browser notification for alert
 */
async function sendAlertNotification(ticker, message) {
    if (!notificationsEnabled()) {
        console.log('[Alerts] Notifications not enabled');
        return;
    }
    
    try {
        const notification = new Notification(`🔔 Stock Alert: ${ticker}`, {
            body: message,
            icon: '/favicon.ico',
            tag: `alert-${ticker}`,
            requireInteraction: true
        });
        
        notification.onclick = () => {
            window.focus();
            window.location.href = `chart-viewer.html?ticker=${ticker}`;
        };
        
        console.log(`[Alerts] Notification sent for ${ticker}`);
    } catch (e) {
        console.error('[Alerts] Error sending notification:', e);
    }
}

// ============================================
// UI COMPONENTS
// ============================================

/**
 * Create alert icon HTML for stock cards
 */
function createAlertIconHTML(ticker) {
    const hasAlertClass = hasAlert(ticker) ? 'has-alert' : '';
    return `
        <span class="alert-icon ${hasAlertClass}" 
              data-ticker="${ticker}"
              onclick="openAlertModal('${ticker}', event)"
              title="${hasAlert(ticker) ? 'Edit alert' : 'Set alert'}">
            🔔
        </span>
    `;
}

/**
 * Update all alert icons on the page
 */
function updateAlertIcons() {
    const icons = document.querySelectorAll('.alert-icon');
    icons.forEach(icon => {
        const ticker = icon.dataset.ticker;
        if (hasAlert(ticker)) {
            icon.classList.add('has-alert');
            icon.title = 'Edit alert';
        } else {
            icon.classList.remove('has-alert');
            icon.title = 'Set alert';
        }
    });
}

/**
 * Open alert modal for a ticker
 */
function openAlertModal(ticker, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    console.log(`[Alerts] Opening modal for ${ticker}`);
    
    // Get existing alert
    const existingAlert = getAlert(ticker);
    
    // Create modal if it doesn't exist
    let modal = document.getElementById('alert-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'alert-modal';
        modal.className = 'note-modal'; // Reuse note modal styles
        document.body.appendChild(modal);
    }
    
    modal.innerHTML = `
        <div class="note-modal-content">
            <div class="note-modal-header">
                <h3>🔔 Price Alert for ${ticker}</h3>
                <button class="note-modal-close" onclick="closeAlertModal()">&times;</button>
            </div>
            <div class="note-modal-body">
                <div class="alert-form">
                    <div class="alert-field">
                        <label>Alert when price goes ABOVE:</label>
                        <input type="number" id="alert-above" step="0.01" placeholder="e.g. 150.00" 
                               value="${existingAlert?.above || ''}">
                    </div>
                    <div class="alert-field">
                        <label>Alert when price goes BELOW:</label>
                        <input type="number" id="alert-below" step="0.01" placeholder="e.g. 100.00"
                               value="${existingAlert?.below || ''}">
                    </div>
                    <div class="alert-field">
                        <label>
                            <input type="checkbox" id="alert-one-time" ${existingAlert?.oneTime ? 'checked' : ''}>
                            One-time alert (remove after triggering)
                        </label>
                    </div>
                </div>
                ${!notificationsEnabled() ? `
                    <div class="alert-permission-notice">
                        ⚠️ Browser notifications are not enabled. 
                        <button onclick="requestNotificationPermission().then(closeAlertModal)">Enable Notifications</button>
                    </div>
                ` : ''}
            </div>
            <div class="note-modal-footer">
                <button class="note-btn note-btn-delete" onclick="deleteAlertFromModal('${ticker}')" ${!existingAlert ? 'disabled' : ''}>
                    🗑️ Delete
                </button>
                <button class="note-btn note-btn-cancel" onclick="closeAlertModal()">
                    Cancel
                </button>
                <button class="note-btn note-btn-save" onclick="saveAlertFromModal('${ticker}')">
                    💾 Save Alert
                </button>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeAlertModal();
        }
    });
}

/**
 * Close alert modal
 */
function closeAlertModal() {
    const modal = document.getElementById('alert-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Save alert from modal
 */
function saveAlertFromModal(ticker) {
    const above = parseFloat(document.getElementById('alert-above').value) || null;
    const below = parseFloat(document.getElementById('alert-below').value) || null;
    const oneTime = document.getElementById('alert-one-time').checked;
    
    if (!above && !below) {
        showNotification('Please set at least one price threshold', 'error');
        return;
    }
    
    setAlert(ticker, { above, below, oneTime });
    closeAlertModal();
    showNotification(`Alert set for ${ticker}`, 'success');
}

/**
 * Delete alert from modal
 */
function deleteAlertFromModal(ticker) {
    if (confirm(`Delete alert for ${ticker}?`)) {
        removeAlert(ticker);
        closeAlertModal();
        showNotification(`Alert removed for ${ticker}`, 'info');
    }
}

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize alerts on page load
 */
function initAlerts() {
    console.log('[Alerts] Initializing...');
    
    // Check alerts when results data is available
    if (typeof globalData !== 'undefined' && globalData) {
        checkAlerts(globalData);
    }
    
    // Check alerts periodically (every 5 minutes when page is open)
    setInterval(() => {
        if (typeof globalData !== 'undefined' && globalData) {
            checkAlerts(globalData);
        }
    }, 5 * 60 * 1000);
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAlerts);
} else {
    initAlerts();
}

console.log('[Alerts] Module loaded');
