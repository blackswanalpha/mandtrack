import os
import sys
import django
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Import models directly from the models.py file
from surveys.models.scoring import ResponseScore, ScoreRule

def test_response_score_fields():
    """Test that the ResponseScore model has the new fields."""
    print("Testing ResponseScore fields...")
    
    # Get all fields in the ResponseScore model
    fields = [field.name for field in ResponseScore._meta.get_fields()]
    
    # Check if the new fields are present
    new_fields = ['z_score', 'percentile', 'additional_data']
    for field in new_fields:
        if field in fields:
            print(f"✓ Field '{field}' exists in ResponseScore model")
        else:
            print(f"✗ Field '{field}' does NOT exist in ResponseScore model")
    
    # Try to create a ResponseScore with the new fields
    try:
        # This is just a test, so we don't need to save it
        score = ResponseScore(
            z_score=1.5,
            percentile=95.0,
            additional_data=json.dumps({"category_scores": {"anxiety": 8, "depression": 5}})
        )
        print("✓ Successfully created ResponseScore with new fields")
    except Exception as e:
        print(f"✗ Failed to create ResponseScore with new fields: {e}")

def test_score_rule_fields():
    """Test that the ScoreRule model has the new fields."""
    print("\nTesting ScoreRule fields...")
    
    # Get all fields in the ScoreRule model
    fields = [field.name for field in ScoreRule._meta.get_fields()]
    
    # Check if the new fields are present
    if 'conditional_logic' in fields:
        print("✓ Field 'conditional_logic' exists in ScoreRule model")
    else:
        print("✗ Field 'conditional_logic' does NOT exist in ScoreRule model")
    
    # Try to create a ScoreRule with the new fields
    try:
        # This is just a test, so we don't need to save it
        rule = ScoreRule(
            conditional_logic=json.dumps({
                "if": {"question_id": 1, "answer": "Yes"},
                "then": {"score": 5},
                "else": {"score": 0}
            })
        )
        print("✓ Successfully created ScoreRule with new fields")
    except Exception as e:
        print(f"✗ Failed to create ScoreRule with new fields: {e}")

if __name__ == "__main__":
    test_response_score_fields()
    test_score_rule_fields()
