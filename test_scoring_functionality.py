import os
import sys
import django
import json
import random
import numpy as np
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Import models directly from the models.py file
from surveys.models.scoring import (
    ScoringSystem, ScoreRule, ScoreRange, ResponseScore, OptionScore
)
from feedback.models import Response, Answer
from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_data():
    """Create test data for scoring functionality."""
    print("Creating test data...")
    
    # Create a scoring system
    scoring_system, created = ScoringSystem.objects.get_or_create(
        name="Test Scoring System",
        defaults={
            'description': 'A test scoring system',
            'scoring_method': 'weighted_sum',
            'max_score': 100,
            'passing_score': 60,
        }
    )
    
    if created:
        print(f"Created ScoringSystem: {scoring_system.name}")
    else:
        print(f"Using existing ScoringSystem: {scoring_system.name}")
    
    # Create some score ranges
    ranges = [
        {'min_score': 0, 'max_score': 20, 'label': 'Very Low', 'color': '#FF0000'},
        {'min_score': 21, 'max_score': 40, 'label': 'Low', 'color': '#FFA500'},
        {'min_score': 41, 'max_score': 60, 'label': 'Medium', 'color': '#FFFF00'},
        {'min_score': 61, 'max_score': 80, 'label': 'High', 'color': '#00FF00'},
        {'min_score': 81, 'max_score': 100, 'label': 'Very High', 'color': '#008000'},
    ]
    
    for range_data in ranges:
        score_range, created = ScoreRange.objects.get_or_create(
            scoring_system=scoring_system,
            min_score=range_data['min_score'],
            max_score=range_data['max_score'],
            defaults={
                'label': range_data['label'],
                'color': range_data['color'],
                'description': f"Scores between {range_data['min_score']} and {range_data['max_score']}",
            }
        )
        
        if created:
            print(f"Created ScoreRange: {score_range.label}")
        else:
            print(f"Using existing ScoreRange: {score_range.label}")
    
    # Create some response scores
    for i in range(10):
        raw_score = random.randint(0, 100)
        z_score = (raw_score - 50) / 15  # Assuming mean=50, std=15
        percentile = 100 * (0.5 + 0.5 * np.math.erf(z_score / np.sqrt(2)))
        
        response_score, created = ResponseScore.objects.get_or_create(
            scoring_system=scoring_system,
            defaults={
                'raw_score': raw_score,
                'normalized_score': raw_score,
                'z_score': z_score,
                'percentile': percentile,
                'additional_data': json.dumps({
                    'category_scores': {
                        'anxiety': random.randint(0, 10),
                        'depression': random.randint(0, 10),
                        'stress': random.randint(0, 10),
                    }
                }),
                'scored_at': datetime.now(),
            }
        )
        
        if created:
            print(f"Created ResponseScore: {response_score.id} with raw_score={raw_score}, z_score={z_score:.2f}, percentile={percentile:.2f}")
        else:
            print(f"Using existing ResponseScore: {response_score.id}")

def test_scoring_functionality():
    """Test the scoring functionality."""
    print("\nTesting scoring functionality...")
    
    # Get all scoring systems
    scoring_systems = ScoringSystem.objects.all()
    print(f"Found {scoring_systems.count()} scoring systems")
    
    for system in scoring_systems:
        print(f"\nScoring System: {system.name}")
        print(f"Method: {system.scoring_method}")
        print(f"Max Score: {system.max_score}")
        print(f"Passing Score: {system.passing_score}")
        
        # Get all score ranges for this system
        ranges = ScoreRange.objects.filter(scoring_system=system)
        print(f"Found {ranges.count()} score ranges")
        
        for range_obj in ranges:
            print(f"  Range: {range_obj.label} ({range_obj.min_score}-{range_obj.max_score})")
        
        # Get all response scores for this system
        scores = ResponseScore.objects.filter(scoring_system=system)
        print(f"Found {scores.count()} response scores")
        
        for score in scores:
            print(f"  Score ID: {score.id}")
            print(f"    Raw Score: {score.raw_score}")
            print(f"    Normalized Score: {score.normalized_score}")
            print(f"    Z-Score: {score.z_score:.2f}")
            print(f"    Percentile: {score.percentile:.2f}")
            
            # Get the score range for this score
            score_range = system.get_score_range(score.normalized_score)
            if score_range:
                print(f"    Range: {score_range.label}")
            else:
                print(f"    Range: Not found")
            
            # Parse the additional data
            if score.additional_data:
                try:
                    additional_data = json.loads(score.additional_data)
                    print(f"    Additional Data: {additional_data}")
                except json.JSONDecodeError:
                    print(f"    Additional Data: Invalid JSON")

if __name__ == "__main__":
    create_test_data()
    test_scoring_functionality()
