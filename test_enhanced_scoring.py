#!/usr/bin/env python
"""
Test script for enhanced scoring functionality.

This script tests the EnhancedScoringService by:
1. Creating a test scoring system
2. Creating a test response
3. Calculating enhanced scores
4. Displaying the results
"""
import os
import sys
import django
import json
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Import models
from django.contrib.auth import get_user_model
from django.apps import apps
from surveys.models.scoring import ScoringSystem, ScoreRule, ScoreRange, ResponseScore, OptionScore
from feedback.models import Response, Answer
from surveys.services.enhanced_scoring_service import EnhancedScoringService

User = get_user_model()

# Get model references
def get_model(app_label, model_name):
    """Get a model from the app registry"""
    try:
        return apps.get_model(app_label, model_name)
    except Exception as e:
        print(f"Error getting model {app_label}.{model_name}: {str(e)}")
        return None

# Define model getters
Questionnaire = get_model('surveys', 'Questionnaire') or get_model('surveys', 'Survey')
Question = get_model('surveys', 'Question')
QuestionChoice = get_model('surveys', 'QuestionChoice')

def print_separator(title=None):
    """Print a separator line with optional title"""
    width = 80
    if title:
        print(f"\n{'-' * 10} {title} {'-' * (width - 12 - len(title))}")
    else:
        print(f"\n{'-' * width}")

def get_or_create_test_data():
    """Get or create test data for scoring"""
    print_separator("Creating Test Data")

    # Get a test response
    responses = Response.objects.all().order_by('-created_at')
    if responses.exists():
        response = responses.first()
        print(f"Using existing response: {response.id}")
    else:
        print("No responses found. Please create a response first.")
        return None

    # Get or create a test scoring system
    scoring_systems = ScoringSystem.objects.filter(questionnaire=response.survey)
    if scoring_systems.exists():
        scoring_system = scoring_systems.first()
        print(f"Using existing scoring system: {scoring_system.name}")
    else:
        print("No scoring systems found for this questionnaire. Please create a scoring system first.")
        return None

    return response, scoring_system

def test_enhanced_scoring():
    """Test the enhanced scoring functionality"""
    print_separator("Enhanced Scoring Test")

    # Get test data
    test_data = get_or_create_test_data()
    if not test_data:
        return

    response, scoring_system = test_data

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

            # Display conditional adjustments
            if 'conditional_adjustments' in response_score.additional_data:
                print("\nConditional Adjustments:")
                for adjustment in response_score.additional_data['conditional_adjustments']:
                    print(f"  Rule: {adjustment.get('rule_id')}")
                    print(f"  Adjustment: {adjustment.get('adjustment')}")
                    print(f"  Message: {adjustment.get('message')}")
                    print()

        print_separator("Success")
        print("Enhanced scoring calculation completed successfully!")

    except Exception as e:
        print_separator("Error")
        print(f"Error calculating enhanced score: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_scoring()
