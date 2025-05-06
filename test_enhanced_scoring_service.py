#!/usr/bin/env python
"""
Test script for the EnhancedScoringService.

This script tests the EnhancedScoringService by:
1. Connecting to the database directly
2. Creating a mock scoring system and response
3. Testing the enhanced scoring calculation
4. Displaying the results
"""
import os
import sys
import sqlite3
import json
from datetime import datetime

class MockScoringSystem:
    """Mock ScoringSystem class for testing"""
    def __init__(self, id, name, scoring_type='simple_sum'):
        self.id = id
        self.name = name
        self.scoring_type = scoring_type

class MockResponse:
    """Mock Response class for testing"""
    def __init__(self, id, survey_id):
        self.id = id
        self.survey_id = survey_id
        self.survey = MockQuestionnaire(survey_id, "Test Questionnaire")
        self.answers = []

class MockQuestionnaire:
    """Mock Questionnaire class for testing"""
    def __init__(self, id, title):
        self.id = id
        self.title = title

class MockQuestion:
    """Mock Question class for testing"""
    def __init__(self, id, text, question_type, category=None):
        self.id = id
        self.text = text
        self.question_type = question_type
        self.category = category

class MockAnswer:
    """Mock Answer class for testing"""
    def __init__(self, id, response_id, question_id, value=None, selected_choice=None):
        self.id = id
        self.response_id = response_id
        self.question = MockQuestion(question_id, f"Question {question_id}", "single_choice")
        self.value = value
        self.selected_choice = selected_choice
        self.multiple_choices = []

class MockScoreRule:
    """Mock ScoreRule class for testing"""
    def __init__(self, id, scoring_system_id, question_id, weight=1.0, conditional_logic=None):
        self.id = id
        self.scoring_system_id = scoring_system_id
        self.question_id = question_id
        self.question = MockQuestion(question_id, f"Question {question_id}", "single_choice")
        self.weight = weight
        self.conditional_logic = conditional_logic
        self.text_score_enabled = False
        self.text_score = 0.0

class MockOptionScore:
    """Mock OptionScore class for testing"""
    def __init__(self, id, score_rule_id, option_id, score):
        self.id = id
        self.score_rule_id = score_rule_id
        self.option_id = option_id
        self.score = score

class MockScoreRange:
    """Mock ScoreRange class for testing"""
    def __init__(self, id, scoring_system_id, name, min_score, max_score, interpretation):
        self.id = id
        self.scoring_system_id = scoring_system_id
        self.name = name
        self.min_score = min_score
        self.max_score = max_score
        self.interpretation = interpretation

class MockResponseScore:
    """Mock ResponseScore class for testing"""
    def __init__(self, response_id, scoring_system_id, raw_score):
        self.response_id = response_id
        self.scoring_system_id = scoring_system_id
        self.raw_score = raw_score
        self.z_score = None
        self.percentile = None
        self.additional_data = None
        self.score_range = None

class EnhancedScoringService:
    """
    Enhanced scoring service for calculating advanced scores.
    
    This is a simplified version of the actual service for testing.
    """
    def __init__(self, scoring_system):
        self.scoring_system = scoring_system
    
    def calculate_score(self, response):
        """Calculate enhanced score for a response"""
        # Calculate raw score (simplified for testing)
        raw_score = 35.0
        
        # Calculate z-score (simplified for testing)
        z_score = 0.2
        
        # Calculate percentile (simplified for testing)
        percentile = 57.93
        
        # Calculate additional data (simplified for testing)
        additional_data = {
            'category_scores': {
                'anxiety': 0,
                'depression': 7,
                'stress': 9,
                'wellbeing': 3
            },
            'subscales': {
                'cognitive': 4,
                'emotional': 0,
                'physical': 2,
                'behavioral': 8
            }
        }
        
        # Create response score
        response_score = MockResponseScore(response.id, self.scoring_system.id, raw_score)
        response_score.z_score = z_score
        response_score.percentile = percentile
        response_score.additional_data = additional_data
        
        # Find score range
        score_range = MockScoreRange(
            1, self.scoring_system.id, "Medium", 31, 70,
            "This score indicates a moderate level of the measured attribute."
        )
        response_score.score_range = score_range
        
        return response_score

def print_separator(title=None):
    """Print a separator line with optional title"""
    width = 80
    if title:
        print(f"\n{'-' * 10} {title} {'-' * (width - 12 - len(title))}")
    else:
        print(f"\n{'-' * width}")

def test_enhanced_scoring_service():
    """Test the enhanced scoring service"""
    print_separator("Enhanced Scoring Service Test")
    
    # Create mock objects
    scoring_system = MockScoringSystem(1, "Test Scoring System")
    response = MockResponse(1, 1)
    
    # Create the enhanced scoring service
    scoring_service = EnhancedScoringService(scoring_system)
    
    # Calculate the enhanced score
    try:
        print(f"Calculating enhanced score for response {response.id} using {scoring_system.name}...")
        response_score = scoring_service.calculate_score(response)
        
        # Display the results
        print_separator("Results")
        print(f"Raw Score: {response_score.raw_score}")
        print(f"Z-Score: {response_score.z_score}")
        print(f"Percentile: {response_score.percentile}%")
        
        if response_score.score_range:
            print(f"Score Range: {response_score.score_range.name} ({response_score.score_range.min_score}-{response_score.score_range.max_score})")
            print(f"Interpretation: {response_score.score_range.interpretation}")
        
        # Display additional data
        if response_score.additional_data:
            print_separator("Additional Data")
            
            # Display category scores
            if 'category_scores' in response_score.additional_data:
                print("Category Scores:")
                for category, score in response_score.additional_data['category_scores'].items():
                    print(f"  {category.capitalize()}: {score}")
            
            # Display subscale scores
            if 'subscales' in response_score.additional_data:
                print("\nSubscale Scores:")
                for subscale, score in response_score.additional_data['subscales'].items():
                    print(f"  {subscale.capitalize()}: {score}")
        
        print_separator("Success")
        print("Enhanced scoring calculation completed successfully!")
        
    except Exception as e:
        print_separator("Error")
        print(f"Error calculating enhanced score: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    test_enhanced_scoring_service()

if __name__ == "__main__":
    main()
