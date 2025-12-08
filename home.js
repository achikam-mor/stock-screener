// Home page specific functionality
async function initHomePage() {
    const data = await loadResults();
    if (!data) {
        console.error('Failed to load data');
        return;
    }

    globalData = data;
    updateTimestamp(data);

    // Update summary cards
    document.getElementById('hot-count').textContent = data.summary.hot_stocks_count;
    document.getElementById('watch-count').textContent = data.summary.watch_list_count;
    document.getElementById('filtered-count').textContent = data.summary.filtered_by_sma_count;
    document.getElementById('total-count').textContent = data.summary.total_analyzed;
    document.getElementById('failed-count').textContent = data.summary.failed_count;
    
    // Load and display market summary
    await loadMarketSummary();
}

/**
 * Load market data and display dynamic summary
 */
async function loadMarketSummary() {
    const summaryContainer = document.getElementById('market-summary');
    if (!summaryContainer) return;
    
    try {
        const response = await fetch('market_data.json');
        if (!response.ok) {
            summaryContainer.innerHTML = '<div class="market-summary-error">Market data temporarily unavailable</div>';
            return;
        }
        
        const marketData = await response.json();
        displayMarketSummary(marketData, summaryContainer);
    } catch (error) {
        console.error('Error loading market summary:', error);
        summaryContainer.innerHTML = '<div class="market-summary-error">Unable to load market overview</div>';
    }
}

/**
 * Display formatted market summary
 */
function displayMarketSummary(data, container) {
    // Get current date formatted nicely
    const now = new Date();
    const dateOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const formattedDate = now.toLocaleDateString('en-US', dateOptions);
    
    // Get sentiment class based on score
    const getSentimentClass = (score) => {
        if (score <= 25) return 'highlight-fear';
        if (score <= 45) return 'highlight-fear';
        if (score <= 55) return 'highlight-neutral';
        return 'highlight-greed';
    };
    
    // Build CNN Fear & Greed text
    let cnnText = '';
    if (data.cnn_fear_greed && data.cnn_fear_greed.available) {
        const cnnClass = getSentimentClass(data.cnn_fear_greed.score);
        cnnText = `The <strong>CNN Fear & Greed Index</strong> stands at <span class="${cnnClass}">${data.cnn_fear_greed.score} (${data.cnn_fear_greed.rating})</span>`;
    }
    
    // Build Crypto Fear & Greed text
    let cryptoText = '';
    if (data.crypto_fear_greed && data.crypto_fear_greed.available) {
        const cryptoClass = getSentimentClass(data.crypto_fear_greed.score);
        cryptoText = `while the <strong>Crypto Fear & Greed Index</strong> is at <span class="${cryptoClass}">${data.crypto_fear_greed.score} (${data.crypto_fear_greed.rating})</span>`;
    }
    
    // Build asset prices text
    let assetText = '';
    if (data.assets) {
        const assetParts = [];
        
        if (data.assets.gold && data.assets.gold.available) {
            const changeSign = data.assets.gold.change >= 0 ? '+' : '';
            assetParts.push(`<span class="highlight-gold">Gold</span> at <strong>$${data.assets.gold.price.toLocaleString()}</strong> (${changeSign}${data.assets.gold.change_percent}%)`);
        }
        
        if (data.assets.silver && data.assets.silver.available) {
            const changeSign = data.assets.silver.change >= 0 ? '+' : '';
            assetParts.push(`<span class="highlight-silver">Silver</span> at <strong>$${data.assets.silver.price.toLocaleString()}</strong> (${changeSign}${data.assets.silver.change_percent}%)`);
        }
        
        if (data.assets.bitcoin && data.assets.bitcoin.available) {
            const changeSign = data.assets.bitcoin.change >= 0 ? '+' : '';
            assetParts.push(`<span class="highlight-bitcoin">Bitcoin</span> at <strong>$${data.assets.bitcoin.price.toLocaleString()}</strong> (${changeSign}${data.assets.bitcoin.change_percent}%)`);
        }
        
        if (data.assets.ethereum && data.assets.ethereum.available) {
            const changeSign = data.assets.ethereum.change >= 0 ? '+' : '';
            assetParts.push(`<span class="highlight-ethereum">Ethereum</span> at <strong>$${data.assets.ethereum.price.toLocaleString()}</strong> (${changeSign}${data.assets.ethereum.change_percent}%)`);
        }
        
        if (assetParts.length > 0) {
            // Join with commas and "and" for the last item
            if (assetParts.length === 1) {
                assetText = assetParts[0];
            } else if (assetParts.length === 2) {
                assetText = assetParts.join(' and ');
            } else {
                assetText = assetParts.slice(0, -1).join(', ') + ', and ' + assetParts[assetParts.length - 1];
            }
        }
    }
    
    // Construct the full summary
    let summaryParts = [];
    if (cnnText) summaryParts.push(cnnText);
    if (cryptoText) summaryParts.push(cryptoText);
    
    let sentimentSummary = summaryParts.join(', ');
    if (sentimentSummary) sentimentSummary += '.';
    
    let assetSummary = '';
    if (assetText) {
        assetSummary = `In the commodities and crypto markets, ${assetText}.`;
    }
    
    // Get overall market sentiment description
    let overallSentiment = '';
    if (data.cnn_fear_greed && data.cnn_fear_greed.available) {
        const score = data.cnn_fear_greed.score;
        if (score <= 25) {
            overallSentiment = 'Markets are showing signs of <span class="highlight-fear">extreme fear</span>, which historically has presented buying opportunities for long-term investors.';
        } else if (score <= 45) {
            overallSentiment = 'Market sentiment indicates <span class="highlight-fear">fear</span>, suggesting cautious positioning may be warranted.';
        } else if (score <= 55) {
            overallSentiment = 'Markets are in a <span class="highlight-neutral">neutral</span> state, with balanced sentiment among investors.';
        } else if (score <= 75) {
            overallSentiment = 'Market sentiment shows <span class="highlight-greed">greed</span>, indicating bullish conditions but potential for pullbacks.';
        } else {
            overallSentiment = 'Markets are exhibiting <span class="highlight-greed">extreme greed</span>, which often precedes market corrections.';
        }
    }
    
    container.innerHTML = `
        <div class="market-summary-header">
            <h3>📈 Today's Market Snapshot</h3>
            <span class="market-summary-date">${formattedDate}</span>
        </div>
        <div class="market-summary-content">
            ${sentimentSummary ? `<p>${sentimentSummary}</p>` : ''}
            ${assetSummary ? `<p>${assetSummary}</p>` : ''}
            ${overallSentiment ? `<p>${overallSentiment}</p>` : ''}
            <p>Use our stock screener to identify trading opportunities based on <strong>SMA150</strong> technical analysis. Browse <a href="hot-stocks.html" style="color: var(--hot-color);">Hot Stocks</a> trading above their moving average or check the <a href="watch-list.html" style="color: var(--watch-color);">Watch List</a> for potential reversal plays.</p>
        </div>
    `;
}

// Load data when page loads
document.addEventListener('DOMContentLoaded', initHomePage);

// Refresh function for auto-refresh
window.refreshCurrentPage = initHomePage;
