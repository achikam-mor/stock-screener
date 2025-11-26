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
            
            document.getElementById('crypto-fear-greed-value').textContent = value;
            document.getElementById('crypto-fear-greed-label').textContent = classification;
            
            // Color based on value
            const gauge = document.getElementById('crypto-fear-greed-gauge');
            if (value <= 25) {
                gauge.classList.add('extreme-fear');
            } else if (value <= 45) {
                gauge.classList.add('fear');
            } else if (value <= 55) {
                gauge.classList.add('neutral');
            } else if (value <= 75) {
                gauge.classList.add('greed');
            } else {
                gauge.classList.add('extreme-greed');
            }
        }
    } catch (error) {
        console.error('Error loading Crypto Fear & Greed:', error);
        document.getElementById('crypto-fear-greed-value').textContent = 'N/A';
        document.getElementById('crypto-fear-greed-label').textContent = 'Unavailable';
    }
    
    // CNN Fear & Greed (no free API - show placeholder)
    document.getElementById('fear-greed-value').textContent = '--';
    document.getElementById('fear-greed-label').textContent = 'Check CNN Business';
    document.querySelector('#fear-greed-gauge').style.cursor = 'pointer';
    document.querySelector('#fear-greed-gauge').onclick = function() {
        window.open('https://www.cnn.com/markets/fear-and-greed', '_blank');
    };
    
    // Add note about CNN F&G
    const cnnNote = document.createElement('p');
    cnnNote.className = 'sentiment-note';
    cnnNote.innerHTML = '<a href="https://www.cnn.com/markets/fear-and-greed" target="_blank" style="color: #3b82f6;">Click to view CNN Fear & Greed Index →</a>';
    document.querySelector('#fear-greed-gauge').parentElement.appendChild(cnnNote);
}
