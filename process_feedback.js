/**
 * Simple script to process enhanced scoring feedback data.
 * 
 * This script demonstrates how to process feedback data from the enhanced scoring feedback form.
 * In a real application, this would be a server-side script that saves the data to a database.
 */

// Function to process feedback data
function processFeedback(data) {
    // Validate the data
    if (!data.accuracy_rating || !data.usefulness_rating) {
        return {
            success: false,
            message: 'Missing required fields'
        };
    }
    
    // Add timestamp
    data.timestamp = new Date().toISOString();
    
    // In a real application, you would save the data to a database here
    // For this demo, we'll just log the data to the console
    console.log('Processing feedback:', data);
    
    // Return success response
    return {
        success: true,
        message: 'Feedback processed successfully',
        data: data
    };
}

// Function to load feedback data from localStorage
function loadFeedbackData() {
    const feedbackData = localStorage.getItem('enhancedScoringFeedback');
    if (feedbackData) {
        return JSON.parse(feedbackData);
    }
    return null;
}

// Function to save feedback data to localStorage
function saveFeedbackData(data) {
    // Get existing feedback data
    let feedbackData = localStorage.getItem('enhancedScoringFeedbackList');
    let feedbackList = [];
    
    if (feedbackData) {
        feedbackList = JSON.parse(feedbackData);
    }
    
    // Add new feedback data
    feedbackList.push(data);
    
    // Save to localStorage
    localStorage.setItem('enhancedScoringFeedbackList', JSON.stringify(feedbackList));
}

// Function to display feedback data
function displayFeedbackData() {
    // Get feedback data
    const feedbackData = localStorage.getItem('enhancedScoringFeedbackList');
    if (!feedbackData) {
        console.log('No feedback data found');
        return;
    }
    
    // Parse feedback data
    const feedbackList = JSON.parse(feedbackData);
    
    // Display feedback data
    console.log('Feedback data:', feedbackList);
    
    // Calculate average ratings
    let totalAccuracy = 0;
    let totalUsefulness = 0;
    
    feedbackList.forEach(feedback => {
        totalAccuracy += parseInt(feedback.accuracy_rating);
        totalUsefulness += parseInt(feedback.usefulness_rating);
    });
    
    const avgAccuracy = totalAccuracy / feedbackList.length;
    const avgUsefulness = totalUsefulness / feedbackList.length;
    
    console.log('Average accuracy rating:', avgAccuracy.toFixed(2));
    console.log('Average usefulness rating:', avgUsefulness.toFixed(2));
    
    // Count preferred features
    const preferredFeatures = {};
    
    feedbackList.forEach(feedback => {
        if (feedback.preferred_features) {
            if (Array.isArray(feedback.preferred_features)) {
                feedback.preferred_features.forEach(feature => {
                    preferredFeatures[feature] = (preferredFeatures[feature] || 0) + 1;
                });
            } else {
                preferredFeatures[feedback.preferred_features] = (preferredFeatures[feedback.preferred_features] || 0) + 1;
            }
        }
    });
    
    console.log('Preferred features:', preferredFeatures);
}

// Process feedback when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Load feedback data
    const feedbackData = loadFeedbackData();
    
    if (feedbackData) {
        // Process feedback data
        const result = processFeedback(feedbackData);
        
        if (result.success) {
            // Save feedback data
            saveFeedbackData(result.data);
            
            // Clear the form data
            localStorage.removeItem('enhancedScoringFeedback');
            
            // Display feedback data
            displayFeedbackData();
        } else {
            console.error('Error processing feedback:', result.message);
        }
    }
});
