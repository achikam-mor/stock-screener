/**
 * Market Overview page - Fear & Greed sentiment indicators
 */

// Load market data on page load
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Load pre-fetched market data (timestamp is included in market_data.json)
        await loadMarketData();
    } catch (error) {
        console.error('Error loading market data:', error);
    }
});

/**
 * Load market data from pre-fetched JSON file
 */
async function loadMarketData() {
    try {
        const response = await fetch('market_data.json');
        if (response.ok) {
            const data = await response.json();
            
            // Update timestamp
            if (data.last_updated) {
                const date = new Date(data.last_updated);
                document.getElementById('last-updated').textContent = 
                    `Last updated: ${date.toLocaleString()}`;
            }
            
            // Load CNN Fear & Greed
            if (data.cnn_fear_greed && data.cnn_fear_greed.available) {
                createFearGreedScale(
                    'fear-greed-gauge',
                    data.cnn_fear_greed.score,
                    data.cnn_fear_greed.rating,
                    'CNN Fear & Greed Index',
                    data.cnn_fear_greed.previous_close
                );
            } else {
                // Fallback to link if data not available
                showCNNFallback();
            }
            
            // Load Crypto Fear & Greed
            if (data.crypto_fear_greed && data.crypto_fear_greed.available) {
                createFearGreedScale(
                    'crypto-fear-greed-gauge',
                    data.crypto_fear_greed.score,
                    data.crypto_fear_greed.rating,
                    'Crypto Fear & Greed Index'
                );
            } else {
                // Fallback to API call
                await loadCryptoFearGreedFromAPI();
            }
            
            // Load Asset Prices
            if (data.assets) {
                displayAssetPrices(data.assets);
            }
        } else {
            // market_data.json not found, use fallbacks
            await loadCryptoFearGreedFromAPI();
            showCNNFallback();
        }
    } catch (error) {
        console.error('Error loading market data:', error);
        await loadCryptoFearGreedFromAPI();
        showCNNFallback();
    }
}

/**
 * Load Crypto Fear & Greed directly from API (fallback)
 */
async function loadCryptoFearGreedFromAPI() {
    try {
        const response = await fetch('https://api.alternative.me/fng/?limit=1');
        if (response.ok) {
            const data = await response.json();
            const value = parseInt(data.data[0].value);
            const classification = data.data[0].value_classification;
            
            createFearGreedScale('crypto-fear-greed-gauge', value, classification, 'Crypto Fear & Greed Index');
        }
    } catch (error) {
        console.error('Error loading Crypto Fear & Greed:', error);
        document.getElementById('crypto-fear-greed-gauge').innerHTML = 
            '<div class="gauge-error">Data Unavailable</div>';
    }
}

/**
 * Show CNN fallback link
 */
function showCNNFallback() {
    const cnnGauge = document.getElementById('fear-greed-gauge');
    cnnGauge.innerHTML = `
        <div class="gauge-placeholder">
            <p style="font-size: 1.1rem; margin-bottom: 10px;">📊 CNN Fear & Greed Index</p>
            <p style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 15px;">Data temporarily unavailable</p>
            <a href="https://www.cnn.com/markets/fear-and-greed" target="_blank" 
               style="display: inline-block; padding: 10px 20px; background: #3b82f6; color: white; 
                      text-decoration: none; border-radius: 8px; font-weight: 600;">
                View on CNN Business →
            </a>
        </div>
    `;
}

/**
 * Create a horizontal fear & greed scale gauge
 */
function createFearGreedScale(containerId, value, label, title, previousClose = null) {
    const container = document.getElementById(containerId);
    
    // Determine color based on value
    let needleColor;
    if (value <= 25) {
        needleColor = '#ef4444'; // Extreme Fear
    } else if (value <= 45) {
        needleColor = '#f59e0b'; // Fear
    } else if (value <= 55) {
        needleColor = '#6b7280'; // Neutral
    } else if (value <= 75) {
        needleColor = '#10b981'; // Greed
    } else {
        needleColor = '#10b981'; // Extreme Greed
    }
    
    const needlePosition = value; // 0-100 scale
    
    // Calculate change from previous close
    let changeHtml = '';
    if (previousClose !== null && previousClose !== undefined) {
        const change = value - previousClose;
        const changeSign = change >= 0 ? '+' : '';
        const changeColor = change >= 0 ? '#10b981' : '#ef4444';
        changeHtml = `<div class="gauge-change" style="color: ${changeColor}; font-size: 0.85rem; margin-top: 5px;">${changeSign}${change} from previous</div>`;
    }
    
    container.innerHTML = `
        <div class="gauge-title">${title}</div>
        <div class="scale-gauge">
            <div class="scale-bar">
                <div class="scale-segment extreme-fear-bg"></div>
                <div class="scale-segment fear-bg"></div>
                <div class="scale-segment neutral-bg"></div>
                <div class="scale-segment greed-bg"></div>
                <div class="scale-segment extreme-greed-bg"></div>
            </div>
            <div class="scale-needle" style="left: ${needlePosition}%; background: ${needleColor};"></div>
            <div class="scale-labels">
                <span>0</span>
                <span>25</span>
                <span>50</span>
                <span>75</span>
                <span>100</span>
            </div>
        </div>
        <div class="gauge-value-display">
            <div class="gauge-current-value" style="color: ${needleColor};">${value}</div>
            <div class="gauge-current-label" style="color: ${needleColor};">${label}</div>
            ${changeHtml}
        </div>
        <div class="scale-legend">
            <span class="legend-label" style="color: #ef4444;">Extreme Fear</span>
            <span class="legend-label" style="color: #f59e0b;">Fear</span>
            <span class="legend-label" style="color: #6b7280;">Neutral</span>
            <span class="legend-label" style="color: #10b981;">Greed</span>
            <span class="legend-label" style="color: #10b981;">Extreme Greed</span>
        </div>
    `;
}

/**
 * Display asset prices (Gold, Silver, Bitcoin, Ethereum)
 */
function displayAssetPrices(assets) {
    const icons = {
        gold: '🥇',
        silver: '🥈',
        bitcoin: '₿',
        ethereum: 'Ξ'
    };
    
    const container = document.getElementById('assets-grid');
    if (!container) return;
    
    let html = '';
    
    for (const [key, asset] of Object.entries(assets)) {
        if (asset.available) {
            const changeColor = asset.change >= 0 ? '#10b981' : '#ef4444';
            const changeSign = asset.change >= 0 ? '+' : '';
            
            html += `
                <div class="asset-card">
                    <div class="asset-icon">${icons[key] || '💰'}</div>
                    <div class="asset-name">${asset.name}</div>
                    <div class="asset-price">$${asset.price.toLocaleString()}</div>
                    <div class="asset-change" style="color: ${changeColor};">
                        ${changeSign}$${asset.change.toLocaleString()} (${changeSign}${asset.change_percent}%)
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="asset-card unavailable">
                    <div class="asset-icon">${icons[key] || '💰'}</div>
                    <div class="asset-name">${asset.name || key}</div>
                    <div class="asset-price">Unavailable</div>
                </div>
            `;
        }
    }
    
    container.innerHTML = html;
}
