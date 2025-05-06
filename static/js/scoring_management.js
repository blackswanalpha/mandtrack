/**
 * Scoring Management System
 * 
 * This script handles the scoring management functionality including:
 * - Fetching scoring data from the API
 * - Calculating scores for responses
 * - Managing scoring rules and ranges
 * - Visualizing score distributions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize scoring management
    initializeScoringManagement();
});

/**
 * Initialize scoring management functionality
 */
function initializeScoringManagement() {
    // Set up event listeners for scoring system creation
    setupScoringSystemCreation();
    
    // Set up event listeners for scoring calculation
    setupScoreCalculation();
    
    // Set up event listeners for rule management
    setupRuleManagement();
    
    // Set up event listeners for range management
    setupRangeManagement();
}

/**
 * Set up scoring system creation
 */
function setupScoringSystemCreation() {
    // Create scoring system button
    const createScoringSystemBtns = document.querySelectorAll('[data-action="create-scoring-system"]');
    createScoringSystemBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const questionnaireId = this.getAttribute('data-questionnaire-id');
            const questionnaireTitle = this.getAttribute('data-questionnaire-title');
            openCreateScoringSystemModal(questionnaireId, questionnaireTitle);
        });
    });
    
    // Close modal buttons
    const closeModalBtns = document.querySelectorAll('[data-action="close-modal"]');
    closeModalBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const modalId = this.getAttribute('data-modal-id');
            closeModal(modalId);
        });
    });
}

/**
 * Open create scoring system modal
 * @param {string} questionnaireId - Questionnaire ID
 * @param {string} questionnaireTitle - Questionnaire title
 */
function openCreateScoringSystemModal(questionnaireId, questionnaireTitle) {
    // Set questionnaire ID in form
    document.getElementById('questionnaire_id').value = questionnaireId;
    
    // Set default name based on questionnaire title
    document.getElementById('name').value = `Scoring for ${questionnaireTitle}`;
    
    // Show modal
    document.getElementById('createScoringModal').classList.remove('hidden');
}

/**
 * Close modal
 * @param {string} modalId - Modal ID
 */
function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

/**
 * Set up score calculation
 */
function setupScoreCalculation() {
    // Calculate all scores button
    const calculateAllScoresBtn = document.getElementById('calculateAllScoresBtn');
    if (calculateAllScoresBtn) {
        calculateAllScoresBtn.addEventListener('click', function() {
            const scoringSystemId = this.getAttribute('data-system-id');
            calculateAllScores(scoringSystemId);
        });
    }
    
    // Calculate individual score buttons
    const calculateScoreBtns = document.querySelectorAll('[data-action="calculate-score"]');
    calculateScoreBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const responseId = this.getAttribute('data-response-id');
            const scoringSystemId = this.getAttribute('data-system-id');
            calculateScore(responseId, scoringSystemId);
        });
    });
}

/**
 * Calculate score for a response
 * @param {string} responseId - Response ID
 * @param {string} scoringSystemId - Scoring system ID
 */
function calculateScore(responseId, scoringSystemId) {
    // Show loading indicator
    showToast('Calculating score...', 'info');
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Make API request
    fetch('/dashboard/api/scoring/calculate/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
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
            // Refresh the page to show updated scores
            window.location.reload();
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
 * @param {string} scoringSystemId - Scoring system ID
 */
function calculateAllScores(scoringSystemId) {
    // Show confirmation dialog
    if (!confirm('Calculate scores for all responses? This may take a while for questionnaires with many responses.')) {
        return;
    }
    
    // Show loading indicator
    showToast('Calculating all scores...', 'info');
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Make API request
    fetch(`/dashboard/api/scoring/systems/${scoringSystemId}/calculate-all/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`Calculated ${data.count} scores successfully!`, 'success');
            // Refresh the page to show updated scores
            window.location.reload();
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
            const scoringSystemId = this.getAttribute('data-system-id');
            openAddRuleModal(scoringSystemId);
        });
    }
    
    // View rule buttons
    const viewRuleBtns = document.querySelectorAll('[data-action="view-rule"]');
    viewRuleBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const ruleId = this.getAttribute('data-rule-id');
            openViewRuleModal(ruleId);
        });
    });
    
    // Delete rule buttons
    const deleteRuleBtns = document.querySelectorAll('[data-action="delete-rule"]');
    deleteRuleBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const ruleId = this.getAttribute('data-rule-id');
            deleteRule(ruleId);
        });
    });
}

/**
 * Open add rule modal
 * @param {string} scoringSystemId - Scoring system ID
 */
function openAddRuleModal(scoringSystemId) {
    // Set scoring system ID in form
    document.getElementById('rule_scoring_system_id').value = scoringSystemId;
    
    // Show modal
    document.getElementById('addRuleModal').classList.remove('hidden');
}

/**
 * Open view rule modal
 * @param {string} ruleId - Rule ID
 */
function openViewRuleModal(ruleId) {
    // Show loading indicator
    showToast('Loading rule details...', 'info');
    
    // Make API request to get rule details
    fetch(`/dashboard/api/scoring/rules/${ruleId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.rule) {
                // Populate modal with rule details
                document.getElementById('view_rule_id').value = data.rule.id;
                document.getElementById('view_rule_question').textContent = data.rule.question_text;
                document.getElementById('view_rule_weight').value = data.rule.weight;
                
                // Show modal
                document.getElementById('viewRuleModal').classList.remove('hidden');
            } else {
                showToast('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            showToast('Error loading rule details: ' + error, 'error');
        });
}

/**
 * Delete rule
 * @param {string} ruleId - Rule ID
 */
function deleteRule(ruleId) {
    // Show confirmation dialog
    if (!confirm('Are you sure you want to delete this rule?')) {
        return;
    }
    
    // Show loading indicator
    showToast('Deleting rule...', 'info');
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Make API request
    fetch(`/dashboard/api/scoring/rules/${ruleId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Rule deleted successfully!', 'success');
            // Refresh the page to show updated rules
            window.location.reload();
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
            const scoringSystemId = this.getAttribute('data-system-id');
            openAddRangeModal(scoringSystemId);
        });
    }
    
    // View range buttons
    const viewRangeBtns = document.querySelectorAll('[data-action="view-range"]');
    viewRangeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const rangeId = this.getAttribute('data-range-id');
            openViewRangeModal(rangeId);
        });
    });
    
    // Delete range buttons
    const deleteRangeBtns = document.querySelectorAll('[data-action="delete-range"]');
    deleteRangeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const rangeId = this.getAttribute('data-range-id');
            deleteRange(rangeId);
        });
    });
}

/**
 * Open add range modal
 * @param {string} scoringSystemId - Scoring system ID
 */
function openAddRangeModal(scoringSystemId) {
    // Set scoring system ID in form
    document.getElementById('range_scoring_system_id').value = scoringSystemId;
    
    // Show modal
    document.getElementById('addRangeModal').classList.remove('hidden');
}

/**
 * Open view range modal
 * @param {string} rangeId - Range ID
 */
function openViewRangeModal(rangeId) {
    // Show loading indicator
    showToast('Loading range details...', 'info');
    
    // Make API request to get range details
    fetch(`/dashboard/api/scoring/ranges/${rangeId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.range) {
                // Populate modal with range details
                document.getElementById('view_range_id').value = data.range.id;
                document.getElementById('view_range_name').value = data.range.name;
                document.getElementById('view_range_min_score').value = data.range.min_score;
                document.getElementById('view_range_max_score').value = data.range.max_score;
                document.getElementById('view_range_color').value = data.range.color;
                document.getElementById('view_range_description').value = data.range.description;
                
                // Show modal
                document.getElementById('viewRangeModal').classList.remove('hidden');
            } else {
                showToast('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            showToast('Error loading range details: ' + error, 'error');
        });
}

/**
 * Delete range
 * @param {string} rangeId - Range ID
 */
function deleteRange(rangeId) {
    // Show confirmation dialog
    if (!confirm('Are you sure you want to delete this range?')) {
        return;
    }
    
    // Show loading indicator
    showToast('Deleting range...', 'info');
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Make API request
    fetch(`/dashboard/api/scoring/ranges/${rangeId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Range deleted successfully!', 'success');
            // Refresh the page to show updated ranges
            window.location.reload();
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Error deleting range: ' + error, 'error');
    });
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
    toast.className = 'mb-3 p-4 rounded-md shadow-lg transform transition-all duration-300 ease-in-out opacity-0 translate-y-2';
    
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
        toast.classList.remove('opacity-0', 'translate-y-2');
        toast.classList.add('opacity-100', 'translate-y-0');
    }, 10);
    
    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove('opacity-100', 'translate-y-0');
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}
