/**
 * Export page functionality for downloading stock screening results
 */

// Load and display counts on page load
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('results.json');
        if (!response.ok) throw new Error('Failed to load results');
        
        const data = await response.json();
        
        // Update counts
        document.getElementById('hot-count').textContent = data.summary.hot_stocks_count || 0;
        document.getElementById('watch-count').textContent = data.summary.watch_list_count || 0;
        document.getElementById('total-count').textContent = data.summary.total_analyzed || 0;
        
        // Update timestamp
        updateTimestamp(data.timestamp);
    } catch (error) {
        console.error('Error loading results:', error);
        document.getElementById('hot-count').textContent = 'N/A';
        document.getElementById('watch-count').textContent = 'N/A';
        document.getElementById('total-count').textContent = 'N/A';
    }
});

/**
 * Export data in specified format
 * @param {string} type - 'hot', 'watch', or 'all'
 * @param {string} format - 'json' or 'csv'
 */
async function exportData(type, format) {
    try {
        const response = await fetch('results.json');
        if (!response.ok) throw new Error('Failed to load results');
        
        const data = await response.json();
        
        let exportData;
        let filename;
        
        if (type === 'hot') {
            exportData = data.hot_stocks;
            filename = `hot-stocks-${getDateString()}`;
        } else if (type === 'watch') {
            exportData = data.watch_list;
            filename = `watch-list-${getDateString()}`;
        } else if (type === 'all') {
            exportData = data;
            filename = `complete-results-${getDateString()}`;
        }
        
        if (format === 'json') {
            downloadJSON(exportData, filename);
        } else if (format === 'csv') {
            downloadCSV(exportData, filename);
        }
        
    } catch (error) {
        console.error('Error exporting data:', error);
        alert('Failed to export data. Please try again.');
    }
}

/**
 * Download data as JSON file
 */
function downloadJSON(data, filename) {
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

/**
 * Download data as CSV file
 */
function downloadCSV(data, filename) {
    if (!Array.isArray(data) || data.length === 0) {
        alert('No data available for CSV export');
        return;
    }
    
    // CSV headers
    const headers = [
        'Symbol',
        'Last Close',
        'SMA150',
        'Distance %',
        'ATR14',
        'ATR %',
        'Last Volume',
        'Avg Volume 14D'
    ];
    
    // Build CSV content
    let csvContent = headers.join(',') + '\n';
    
    data.forEach(stock => {
        const row = [
            stock.symbol,
            stock.last_close,
            stock.sma150,
            stock.distance_percent,
            stock.atr,
            stock.atr_percent,
            stock.last_volume,
            stock.avg_volume_14d
        ];
        csvContent += row.join(',') + '\n';
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

/**
 * Get formatted date string for filename
 */
function getDateString() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    return `${year}${month}${day}-${hours}${minutes}`;
}
