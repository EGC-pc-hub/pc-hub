/**
 * Dynamic Download Counter - Updates download count without page refresh
 * This version avoids race conditions by updating the UI after download completes
 */

/**
 * Update the download counter display in the UI
 */
function updateDownloadCounter(datasetId) {
    // Find all download counter elements for this dataset
    const counterElements = document.querySelectorAll(
        `[data-download-counter="${datasetId}"]`
    );
    
    counterElements.forEach((element) => {
        // Get current count and increment - trim whitespace and parse only the number
        let currentCount = parseInt(element.textContent.trim()) || 0;
        currentCount += 1;
        
        // Update the text - set as string to ensure clean replacement
        element.textContent = String(currentCount);
        
        // Update the label (singular/plural)
        const labelSpan = element.parentElement.querySelector('[data-download-label]');
        if (labelSpan) {
            labelSpan.textContent = currentCount === 1 ? 'download' : 'downloads';
        }
    });
}

/**
 * Fetch and update download counts from server
 */
async function refreshAllCounters() {
    const counterElements = document.querySelectorAll('[data-download-counter]');
    const datasetIds = new Set();
    
    // Collect all unique dataset IDs
    counterElements.forEach(element => {
        const datasetId = element.getAttribute('data-download-counter');
        if (datasetId) {
            datasetIds.add(datasetId);
        }
    });
    
    // Fetch and update each counter
    for (const datasetId of datasetIds) {
        try {
            const response = await fetch(`/dataset/${datasetId}/stats`);
            if (response.ok) {
                const data = await response.json();
                
                // Update all counter elements for this dataset
                const elements = document.querySelectorAll(`[data-download-counter="${datasetId}"]`);
                elements.forEach(element => {
                    // Set as string to ensure clean replacement
                    element.textContent = String(data.download_count || 0);
                    
                    // Update label
                    const labelSpan = element.parentElement.querySelector('[data-download-label]');
                    if (labelSpan) {
                        labelSpan.textContent = data.download_count === 1 ? 'download' : 'downloads';
                    }
                });
            }
        } catch (error) {
            console.error(`Error fetching stats for dataset ${datasetId}:`, error);
        }
    }
}

/**
 * Handle download button click
 */
function handleDownload(event, datasetId) {
    // Update counter immediately
    updateDownloadCounter(datasetId);
    
    // Let the default link behavior continue (download will proceed normally)
    // No need to prevent default or manipulate window.location
}

/**
 * Initialize download tracking when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    // Find all download buttons and attach event listeners
    const downloadButtons = document.querySelectorAll('[data-download-btn]');
    
    downloadButtons.forEach(button => {
        const datasetId = button.getAttribute('data-dataset-id');
        
        // Add click handler that updates counter but doesn't prevent default
        button.addEventListener('click', function(event) {
            handleDownload(event, datasetId);
        });
    });
    
    // Refresh counters when page becomes visible (user returns to tab/page)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            // Page is now visible, refresh all counters
            refreshAllCounters();
        }
    });
});
