/**
 * Market Overview page - VIX chart and sentiment indicators
 */

let vixChart = null;

// Load market data on page load
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Load VIX data
        await loadVixData();
        
        // Load Fear & Greed indicators
        await loadFearGreedIndicators();
        
        // Update timestamp from results
        const response = await fetch('results.json');
        if (response.ok) {
            const data = await response.json();
            updateTimestamp(data.timestamp);
        }
    } catch (error) {
        console.error('Error loading market data:', error);
    }
});

/**
 * Load and display VIX data
 */
async function loadVixData() {
    try {
        const response = await fetch('vix_data.json');
        if (!response.ok) {
            throw new Error('VIX data not available');
        }
        
        const vixData = await response.json();
        
        // Create chart
        createVixChart(vixData.dates, vixData.values);
        
        // Update statistics
        const currentVix = vixData.values[vixData.values.length - 1];
        const avgVix = vixData.values.reduce((a, b) => a + b, 0) / vixData.values.length;
        const minVix = Math.min(...vixData.values);
        const maxVix = Math.max(...vixData.values);
        
        document.getElementById('current-vix').textContent = currentVix.toFixed(2);
        document.getElementById('avg-vix').textContent = avgVix.toFixed(2);
        document.getElementById('range-vix').textContent = `${minVix.toFixed(2)} - ${maxVix.toFixed(2)}`;
        
        // Color current VIX based on level
        const currentVixElement = document.getElementById('current-vix');
        if (currentVix < 15) {
            currentVixElement.style.color = '#10b981'; // Green - Low
        } else if (currentVix < 25) {
            currentVixElement.style.color = '#f59e0b'; // Orange - Medium
        } else {
            currentVixElement.style.color = '#ef4444'; // Red - High
        }
        
    } catch (error) {
        console.error('Error loading VIX data:', error);
        document.querySelector('.chart-container').innerHTML = 
            '<div class="error">VIX data temporarily unavailable. Please check back later.</div>';
    }
}

/**
 * Create VIX chart using Chart.js
 */
function createVixChart(dates, values) {
    const ctx = document.getElementById('vixChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (vixChart) {
        vixChart.destroy();
    }
    
    vixChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'VIX',
                data: values,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 6,
                pointBackgroundColor: '#3b82f6',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointHoverBackgroundColor: '#2563eb',
                pointHoverBorderColor: '#ffffff',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2.5,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 41, 59, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#f1f5f9',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            return 'VIX: ' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: '#334155',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#94a3b8',
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    grid: {
                        color: '#334155',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#94a3b8',
                        callback: function(value) {
                            return value.toFixed(0);
                        }
                    },
                    beginAtZero: false
                }
            }
        }
    });
}

/**
 * Load Fear & Greed indicators
 */
async function loadFearGreedIndicators() {
    // Load Crypto Fear & Greed (has free API)
    try {
        const response = await fetch('https://api.alternative.me/fng/?limit=1');
        if (response.ok) {
            const data = await response.json();
            const value = parseInt(data.data[0].value);
            const classification = data.data[0].value_classification;
            
            // Update gauge with scale
            createFearGreedScale('crypto-fear-greed-gauge', value, classification);
        }
    } catch (error) {
        console.error('Error loading Crypto Fear & Greed:', error);
        document.getElementById('crypto-fear-greed-gauge').innerHTML = 
            '<div class="gauge-error">Data Unavailable</div>';
    }
    
    // CNN Fear & Greed (no free API - show placeholder)
    const cnnGauge = document.getElementById('fear-greed-gauge');
    cnnGauge.innerHTML = `
        <div class="gauge-placeholder">
            <p style="font-size: 1.1rem; margin-bottom: 10px;">📊 CNN Fear & Greed Index</p>
            <p style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 15px;">No free API available</p>
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
function createFearGreedScale(containerId, value, label) {
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
    
    container.innerHTML = `
        <div class="gauge-title">Crypto Fear & Greed Index</div>
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
