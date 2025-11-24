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
}

// Load data when page loads
document.addEventListener('DOMContentLoaded', initHomePage);

// Refresh function for auto-refresh
window.refreshCurrentPage = initHomePage;
