/**
 * Completion Tracker
 * 
 * This script tracks the completion of questionnaires by sending events to the server.
 * It tracks the following events:
 * - Start: When the questionnaire is first loaded
 * - Answer: When a question is answered
 * - Navigation: When the user navigates between questions
 * - Completion: When the questionnaire is completed
 * - Abandonment: When the user leaves the page without completing
 */

class CompletionTracker {
    constructor(responseId, csrfToken) {
        this.responseId = responseId;
        this.csrfToken = csrfToken;
        this.isStarted = false;
        this.isCompleted = false;
        this.currentQuestionId = null;
        this.completionPercentage = 0;
        
        // Bind event handlers
        this.handleBeforeUnload = this.handleBeforeUnload.bind(this);
        
        // Add event listeners
        window.addEventListener('beforeunload', this.handleBeforeUnload);
        
        // Initialize
        this.init();
    }
    
    /**
     * Initialize the tracker
     */
    async init() {
        // Track start event
        await this.trackStart();
        
        // Set up answer tracking
        this.setupAnswerTracking();
        
        // Set up navigation tracking
        this.setupNavigationTracking();
    }
    
    /**
     * Track the start of the questionnaire
     */
    async trackStart() {
        try {
            const response = await fetch(`/responses/${this.responseId}/track/start/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.isStarted = true;
                this.completionPercentage = data.completion_percentage;
                console.log('Tracking started:', data);
                
                // Update progress bar if it exists
                this.updateProgressBar();
            }
        } catch (error) {
            console.error('Error tracking start:', error);
        }
    }
    
    /**
     * Set up tracking for answer submissions
     */
    setupAnswerTracking() {
        // Find all form elements that submit answers
        const forms = document.querySelectorAll('form[data-question-id]');
        
        forms.forEach(form => {
            form.addEventListener('submit', async (event) => {
                // Don't prevent the default form submission
                // We'll track the answer in parallel
                
                const questionId = form.dataset.questionId;
                
                // Track the answer submission
                await this.trackAnswer(questionId);
            });
        });
        
        // Also track changes to inputs that might not have a form submission
        const inputs = document.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            // Find the closest form or question container
            const container = input.closest('[data-question-id]');
            
            if (container) {
                const questionId = container.dataset.questionId;
                
                // For checkboxes and radios
                if (input.type === 'checkbox' || input.type === 'radio') {
                    input.addEventListener('change', async () => {
                        await this.trackAnswer(questionId);
                    });
                }
                
                // For text inputs, track on blur
                if (input.type === 'text' || input.tagName === 'TEXTAREA' || input.tagName === 'SELECT') {
                    input.addEventListener('blur', async () => {
                        await this.trackAnswer(questionId);
                    });
                }
            }
        });
    }
    
    /**
     * Track an answer submission
     */
    async trackAnswer(questionId) {
        try {
            const response = await fetch(`/responses/${this.responseId}/track/answer/${questionId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.completionPercentage = data.completion_percentage;
                console.log('Answer tracked:', data);
                
                // Update progress bar if it exists
                this.updateProgressBar();
                
                // If the questionnaire is now completed, track completion
                if (data.is_completed && !this.isCompleted) {
                    await this.trackCompletion();
                }
            }
        } catch (error) {
            console.error('Error tracking answer:', error);
        }
    }
    
    /**
     * Set up tracking for navigation between questions
     */
    setupNavigationTracking() {
        // Find all navigation buttons
        const navButtons = document.querySelectorAll('[data-nav-direction]');
        
        navButtons.forEach(button => {
            button.addEventListener('click', async () => {
                const direction = button.dataset.navDirection;
                const currentQuestionId = button.closest('[data-question-id]')?.dataset.questionId;
                const nextQuestionId = button.dataset.nextQuestionId;
                
                await this.trackNavigation(currentQuestionId, nextQuestionId, direction);
            });
        });
    }
    
    /**
     * Track navigation between questions
     */
    async trackNavigation(currentQuestionId, nextQuestionId, direction) {
        try {
            const response = await fetch(`/responses/${this.responseId}/track/navigation/?current=${currentQuestionId || ''}&next=${nextQuestionId || ''}&direction=${direction || 'forward'}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentQuestionId = nextQuestionId;
                console.log('Navigation tracked:', data);
            }
        } catch (error) {
            console.error('Error tracking navigation:', error);
        }
    }
    
    /**
     * Track the completion of the questionnaire
     */
    async trackCompletion() {
        try {
            const response = await fetch(`/responses/${this.responseId}/track/completion/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.isCompleted = true;
                console.log('Completion tracked:', data);
                
                // Remove the beforeunload event listener since we're done
                window.removeEventListener('beforeunload', this.handleBeforeUnload);
            }
        } catch (error) {
            console.error('Error tracking completion:', error);
        }
    }
    
    /**
     * Track abandonment when the user leaves the page
     */
    async trackAbandonment(reason = 'page_close') {
        // Only track abandonment if we've started but not completed
        if (this.isStarted && !this.isCompleted) {
            try {
                // Use the sendBeacon API to ensure the request is sent even if the page is unloading
                const url = `/responses/${this.responseId}/track/abandonment/?reason=${reason}`;
                const data = new FormData();
                data.append('csrfmiddlewaretoken', this.csrfToken);
                
                navigator.sendBeacon(url, data);
                
                console.log('Abandonment tracked');
            } catch (error) {
                console.error('Error tracking abandonment:', error);
            }
        }
    }
    
    /**
     * Handle the beforeunload event
     */
    handleBeforeUnload(event) {
        // Track abandonment when the user leaves the page
        this.trackAbandonment('page_close');
        
        // If the questionnaire is not completed, show a confirmation dialog
        if (this.isStarted && !this.isCompleted && this.completionPercentage > 0) {
            const message = 'You have not completed the questionnaire. Are you sure you want to leave?';
            event.returnValue = message;
            return message;
        }
    }
    
    /**
     * Update the progress bar if it exists
     */
    updateProgressBar() {
        const progressBar = document.querySelector('.completion-progress-bar');
        const progressText = document.querySelector('.completion-progress-text');
        
        if (progressBar) {
            progressBar.style.width = `${this.completionPercentage}%`;
        }
        
        if (progressText) {
            progressText.textContent = `${Math.round(this.completionPercentage)}%`;
        }
    }
    
    /**
     * Clean up event listeners
     */
    destroy() {
        window.removeEventListener('beforeunload', this.handleBeforeUnload);
    }
}

// Initialize the tracker when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const responseIdElement = document.querySelector('[data-response-id]');
    const csrfTokenElement = document.querySelector('[name="csrfmiddlewaretoken"]');
    
    if (responseIdElement && csrfTokenElement) {
        const responseId = responseIdElement.dataset.responseId;
        const csrfToken = csrfTokenElement.value;
        
        window.completionTracker = new CompletionTracker(responseId, csrfToken);
    }
});
