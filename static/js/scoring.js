/**
 * Scoring Management JavaScript
 * Handles scoring system functionality including:
 * - Score calculation
 * - Rule management
 * - Range management
 * - API interactions
 */

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeScoringSystem();
});

/**
 * Initialize scoring system functionality
 */
function initializeScoringSystem() {
    // Set up event listeners
    setupCalculateScoreButtons();
    setupRuleManagement();
    setupRangeManagement();
    setupDataRefresh();
}

/**
 * Set up calculate score buttons
 */
function setupCalculateScoreButtons() {
    // Calculate single score
    const calculateScoreButtons = document.querySelectorAll('.calculate-score-btn');
    calculateScoreButtons.forEach(button => {
        button.addEventListener('click', function() {
            const responseId = this.getAttribute('data-response-id');
            const scoringSystemId = this.getAttribute('data-system-id');
            calculateScore(responseId, scoringSystemId);
        });
    });

    // Calculate all scores
    const calculateAllScoresBtn = document.getElementById('calculateAllScoresBtn');
    if (calculateAllScoresBtn) {
        calculateAllScoresBtn.addEventListener('click', function() {
            const scoringSystemId = this.getAttribute('data-system-id');
            calculateAllScores(scoringSystemId);
        });
    }
}

/**
 * Calculate score for a response
 * @param {string} responseId - Response ID
 * @param {string} scoringSystemId - Scoring System ID
 */
function calculateScore(responseId, scoringSystemId) {
    // Show loading indicator
    showToast('Calculating score...', 'info');
    
    // Make API request
    fetch('/dashboard/api/scoring/calculate/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            response_id: responseId,
            scoring_system_id: scoringSystemId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Score calculated successfully!', 'success');
            // Refresh the scores table
            refreshScoresTable();
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Error calculating score: ' + error, 'error');
    });
}

/**
 * Calculate scores for all responses
 * @param {string} scoringSystemId - Scoring System ID
 */
function calculateAllScores(scoringSystemId) {
    // Show confirmation dialog
    if (!confirm('Calculate scores for all responses? This may take a while for questionnaires with many responses.')) {
        return;
    }
    
    // Show loading indicator
    showToast('Calculating all scores...', 'info');
    
    // Make API request
    fetch(`/dashboard/api/scoring/systems/${scoringSystemId}/calculate-all/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`Calculated ${data.count} scores successfully!`, 'success');
            // Refresh the scores table
            refreshScoresTable();
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Error calculating scores: ' + error, 'error');
    });
}

/**
 * Set up rule management
 */
function setupRuleManagement() {
    // Add rule button
    const addRuleBtn = document.getElementById('addRuleBtn');
    if (addRuleBtn) {
        addRuleBtn.addEventListener('click', function() {
            openAddRuleModal();
        });
    }
    
    // View rule buttons
    const viewRuleBtns = document.querySelectorAll('.view-rule-btn');
    viewRuleBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const ruleId = this.getAttribute('data-rule-id');
            openViewRuleModal(ruleId);
        });
    });
    
    // Delete rule buttons
    const deleteRuleBtns = document.querySelectorAll('.delete-rule-btn');
    deleteRuleBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const ruleId = this.getAttribute('data-rule-id');
            deleteRule(ruleId);
        });
    });
}

/**
 * Open modal to add a new rule
 */
function openAddRuleModal() {
    // Implementation will be added
    alert('Add rule modal will be implemented here');
}

/**
 * Open modal to view/edit a rule
 * @param {string} ruleId - Rule ID
 */
function openViewRuleModal(ruleId) {
    // Implementation will be added
    alert(`View rule ${ruleId} modal will be implemented here`);
}

/**
 * Delete a rule
 * @param {string} ruleId - Rule ID
 */
function deleteRule(ruleId) {
    if (!confirm('Are you sure you want to delete this rule?')) {
        return;
    }
    
    // Show loading indicator
    showToast('Deleting rule...', 'info');
    
    // Make API request
    fetch(`/dashboard/api/scoring/rules/${ruleId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Rule deleted successfully!', 'success');
            // Refresh the rules table
            refreshRulesTable();
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Error deleting rule: ' + error, 'error');
    });
}

/**
 * Set up range management
 */
function setupRangeManagement() {
    // Add range button
    const addRangeBtn = document.getElementById('addRangeBtn');
    if (addRangeBtn) {
        addRangeBtn.addEventListener('click', function() {
            openAddRangeModal();
        });
    }
    
    // View range buttons
    const viewRangeBtns = document.querySelectorAll('.view-range-btn');
    viewRangeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const rangeId = this.getAttribute('data-range-id');
            openViewRangeModal(rangeId);
        });
    });
    
    // Delete range buttons
    const deleteRangeBtns = document.querySelectorAll('.delete-range-btn');
    deleteRangeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const rangeId = this.getAttribute('data-range-id');
            deleteRange(rangeId);
        });
    });
}

/**
 * Open modal to add a new range
 */
function openAddRangeModal() {
    // Implementation will be added
    alert('Add range modal will be implemented here');
}

/**
 * Open modal to view/edit a range
 * @param {string} rangeId - Range ID
 */
function openViewRangeModal(rangeId) {
    // Implementation will be added
    alert(`View range ${rangeId} modal will be implemented here`);
}

/**
 * Delete a range
 * @param {string} rangeId - Range ID
 */
function deleteRange(rangeId) {
    if (!confirm('Are you sure you want to delete this range?')) {
        return;
    }
    
    // Show loading indicator
    showToast('Deleting range...', 'info');
    
    // Make API request
    fetch(`/dashboard/api/scoring/ranges/${rangeId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Range deleted successfully!', 'success');
            // Refresh the ranges table
            refreshRangesTable();
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Error deleting range: ' + error, 'error');
    });
}

/**
 * Set up data refresh
 */
function setupDataRefresh() {
    // Refresh button
    const refreshBtn = document.getElementById('refreshDataBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            refreshAllData();
        });
    }
}

/**
 * Refresh all data
 */
function refreshAllData() {
    refreshRulesTable();
    refreshRangesTable();
    refreshScoresTable();
}

/**
 * Refresh rules table
 */
function refreshRulesTable() {
    const rulesContainer = document.getElementById('score-rules');
    if (rulesContainer) {
        // Show loading indicator
        rulesContainer.innerHTML = '<div class="p-5 text-center"><i class="fas fa-spinner fa-spin mr-2"></i> Loading rules...</div>';
        
        // Get scoring system ID
        const scoringSystemId = document.getElementById('scoring-system-id').value;
        
        // Make API request
        fetch(`/dashboard/api/scoring/systems/${scoringSystemId}/`)
            .then(response => response.json())
            .then(data => {
                // Update rules table
                // Implementation will be added
            })
            .catch(error => {
                rulesContainer.innerHTML = `<div class="p-5 text-center text-red-600">Error loading rules: ${error}</div>`;
            });
    }
}

/**
 * Refresh ranges table
 */
function refreshRangesTable() {
    const rangesContainer = document.getElementById('score-ranges');
    if (rangesContainer) {
        // Show loading indicator
        rangesContainer.innerHTML = '<div class="p-5 text-center"><i class="fas fa-spinner fa-spin mr-2"></i> Loading ranges...</div>';
        
        // Get scoring system ID
        const scoringSystemId = document.getElementById('scoring-system-id').value;
        
        // Make API request
        fetch(`/dashboard/api/scoring/systems/${scoringSystemId}/`)
            .then(response => response.json())
            .then(data => {
                // Update ranges table
                // Implementation will be added
            })
            .catch(error => {
                rangesContainer.innerHTML = `<div class="p-5 text-center text-red-600">Error loading ranges: ${error}</div>`;
            });
    }
}

/**
 * Refresh scores table
 */
function refreshScoresTable() {
    const scoresContainer = document.getElementById('recent-scores');
    if (scoresContainer) {
        // Show loading indicator
        scoresContainer.innerHTML = '<div class="p-5 text-center"><i class="fas fa-spinner fa-spin mr-2"></i> Loading scores...</div>';
        
        // Get scoring system ID
        const scoringSystemId = document.getElementById('scoring-system-id').value;
        
        // Make API request
        fetch(`/dashboard/api/scoring/systems/${scoringSystemId}/`)
            .then(response => response.json())
            .then(data => {
                // Update scores table
                // Implementation will be added
            })
            .catch(error => {
                scoresContainer.innerHTML = `<div class="p-5 text-center text-red-600">Error loading scores: ${error}</div>`;
            });
    }
}

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type of toast (success, error, info)
 */
function showToast(message, type = 'info') {
    // Check if toast container exists
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        // Create toast container
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'fixed bottom-4 right-4 z-50';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast
    const toast = document.createElement('div');
    toast.className = 'mb-3 p-4 rounded-md shadow-lg transform transition-all duration-300 ease-in-out';
    
    // Set toast color based on type
    if (type === 'success') {
        toast.className += ' bg-green-500 text-white';
    } else if (type === 'error') {
        toast.className += ' bg-red-500 text-white';
    } else {
        toast.className += ' bg-blue-500 text-white';
    }
    
    // Set toast content
    toast.innerHTML = message;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Animate toast in
    setTimeout(() => {
        toast.classList.add('translate-y-0', 'opacity-100');
    }, 10);
    
    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

/**
 * Get CSRF token from cookies
 * @returns {string} CSRF token
 */
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length, cookie.length);
        }
    }
    return '';
}
