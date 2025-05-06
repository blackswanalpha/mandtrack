#!/usr/bin/env python
"""
Standalone test script for enhanced scoring functionality.

This script tests the enhanced scoring functionality without relying on Django models.
"""
import json
import math
import random
from datetime import datetime

class EnhancedScoringService:
    """
    Enhanced scoring service for calculating advanced scores.
    
    This is a standalone version of the service for testing.
    """
    def __init__(self, scoring_system):
        self.scoring_system = scoring_system
    
    def calculate_score(self, response):
        """Calculate enhanced score for a response"""
        # Calculate raw score (simplified for testing)
        raw_score = self._calculate_raw_score(response)
        
        # Calculate z-score
        z_score = self._calculate_z_score(raw_score)
        
        # Calculate percentile
        percentile = self._calculate_percentile(z_score)
        
        # Calculate additional data
        additional_data = self._calculate_additional_data(response, raw_score)
        
        # Find score range
        score_range = self._find_score_range(raw_score)
        
        # Create response score
        response_score = {
            'response_id': response['id'],
            'scoring_system_id': self.scoring_system['id'],
            'raw_score': raw_score,
            'z_score': z_score,
            'percentile': percentile,
            'additional_data': additional_data,
            'score_range': score_range
        }
        
        return response_score
    
    def _calculate_raw_score(self, response):
        """Calculate raw score based on answers"""
        # For testing, we'll use a simple algorithm
        raw_score = 0
        
        # Sum up scores from answers
        for answer in response['answers']:
            if 'score' in answer and answer['score'] is not None:
                raw_score += answer['score']
        
        return raw_score
    
    def _calculate_z_score(self, raw_score):
        """Calculate z-score based on population statistics"""
        # For testing, we'll use sample statistics
        mean = 50
        stddev = 15
        
        # Avoid division by zero
        if stddev == 0:
            return 0
        
        # Calculate z-score
        z_score = (raw_score - mean) / stddev
        
        return round(z_score, 2)
    
    def _calculate_percentile(self, z_score):
        """Calculate percentile based on z-score"""
        # Convert z-score to percentile using cumulative distribution function
        percentile = (0.5 * (1 + math.erf(z_score / math.sqrt(2)))) * 100
        
        return round(percentile, 1)
    
    def _calculate_additional_data(self, response, base_score):
        """Calculate additional scoring data"""
        # For testing, we'll generate sample data
        additional_data = {}
        
        # Calculate category scores
        category_scores = {
            'anxiety': random.randint(0, 10),
            'depression': random.randint(0, 10),
            'stress': random.randint(0, 10),
            'wellbeing': random.randint(0, 10)
        }
        additional_data['category_scores'] = category_scores
        
        # Calculate subscale scores
        subscales = {
            'cognitive': random.randint(0, 10),
            'emotional': random.randint(0, 10),
            'physical': random.randint(0, 10),
            'behavioral': random.randint(0, 10)
        }
        additional_data['subscales'] = subscales
        
        # Process conditional logic
        conditional_adjustments = self._process_conditional_logic(response, base_score)
        if conditional_adjustments:
            additional_data['conditional_adjustments'] = conditional_adjustments
        
        return additional_data
    
    def _find_score_range(self, raw_score):
        """Find the score range for a raw score"""
        # For testing, we'll use sample ranges
        ranges = [
            {'id': 1, 'name': 'Low', 'min_score': 0, 'max_score': 30, 'color': 'red', 'interpretation': 'This score indicates a low level of the measured attribute.'},
            {'id': 2, 'name': 'Medium', 'min_score': 31, 'max_score': 70, 'color': 'yellow', 'interpretation': 'This score indicates a moderate level of the measured attribute.'},
            {'id': 3, 'name': 'High', 'min_score': 71, 'max_score': 100, 'color': 'green', 'interpretation': 'This score indicates a high level of the measured attribute.'}
        ]
        
        # Find the range that contains the raw score
        for range_obj in ranges:
            if range_obj['min_score'] <= raw_score <= range_obj['max_score']:
                return range_obj
        
        return None
    
    def _process_conditional_logic(self, response, base_score):
        """Process conditional logic rules"""
        # For testing, we'll use sample conditional logic
        conditional_adjustments = []
        
        # Sample conditional logic
        conditional_logic = [
            {
                'rule_id': 1,
                'condition': 'anxiety_score > 7',
                'adjustment': 5,
                'message': 'High anxiety detected'
            },
            {
                'rule_id': 2,
                'condition': 'depression_score > 7',
                'adjustment': 5,
                'message': 'High depression detected'
            },
            {
                'rule_id': 3,
                'condition': 'stress_score > 7',
                'adjustment': 5,
                'message': 'High stress detected'
            }
        ]
        
        # Get category scores
        category_scores = {
            'anxiety_score': random.randint(0, 10),
            'depression_score': random.randint(0, 10),
            'stress_score': random.randint(0, 10)
        }
        
        # Evaluate conditional logic
        for rule in conditional_logic:
            condition = rule['condition']
            
            # Parse the condition
            parts = condition.split()
            variable = parts[0]
            operator = parts[1]
            value = int(parts[2])
            
            # Evaluate the condition
            if variable in category_scores:
                var_value = category_scores[variable]
                
                if operator == '>' and var_value > value:
                    conditional_adjustments.append({
                        'rule_id': rule['rule_id'],
                        'adjustment': rule['adjustment'],
                        'message': rule['message']
                    })
                elif operator == '>=' and var_value >= value:
                    conditional_adjustments.append({
                        'rule_id': rule['rule_id'],
                        'adjustment': rule['adjustment'],
                        'message': rule['message']
                    })
                elif operator == '<' and var_value < value:
                    conditional_adjustments.append({
                        'rule_id': rule['rule_id'],
                        'adjustment': rule['adjustment'],
                        'message': rule['message']
                    })
                elif operator == '<=' and var_value <= value:
                    conditional_adjustments.append({
                        'rule_id': rule['rule_id'],
                        'adjustment': rule['adjustment'],
                        'message': rule['message']
                    })
                elif operator == '==' and var_value == value:
                    conditional_adjustments.append({
                        'rule_id': rule['rule_id'],
                        'adjustment': rule['adjustment'],
                        'message': rule['message']
                    })
                elif operator == '!=' and var_value != value:
                    conditional_adjustments.append({
                        'rule_id': rule['rule_id'],
                        'adjustment': rule['adjustment'],
                        'message': rule['message']
                    })
        
        return conditional_adjustments

def print_separator(title=None):
    """Print a separator line with optional title"""
    width = 80
    if title:
        print(f"\n{'-' * 10} {title} {'-' * (width - 12 - len(title))}")
    else:
        print(f"\n{'-' * width}")

def create_test_data():
    """Create test data for scoring"""
    print_separator("Creating Test Data")
    
    # Create a test scoring system
    scoring_system = {
        'id': 1,
        'name': 'Test Scoring System',
        'description': 'A test scoring system for enhanced scoring',
        'scoring_type': 'simple_sum',
        'created_at': datetime.now().isoformat()
    }
    print(f"Created test scoring system: {scoring_system['name']}")
    
    # Create a test response
    response = {
        'id': 1,
        'survey_id': 1,
        'status': 'completed',
        'patient_email': 'test@example.com',
        'patient_age': 30,
        'patient_gender': 'male',
        'completion_time': 120,
        'created_at': datetime.now().isoformat(),
        'answers': []
    }
    print(f"Created test response: {response['id']}")
    
    # Create test answers
    for i in range(10):
        answer = {
            'id': i + 1,
            'response_id': response['id'],
            'question_id': i + 1,
            'score': random.randint(1, 10),
            'created_at': datetime.now().isoformat()
        }
        response['answers'].append(answer)
    
    print(f"Created {len(response['answers'])} test answers")
    
    return response, scoring_system

def test_enhanced_scoring():
    """Test the enhanced scoring functionality"""
    print_separator("Enhanced Scoring Test")
    
    # Create test data
    response, scoring_system = create_test_data()
    
    # Create the enhanced scoring service
    scoring_service = EnhancedScoringService(scoring_system)
    
    # Calculate the enhanced score
    try:
        print(f"Calculating enhanced score for response {response['id']} using {scoring_system['name']}...")
        response_score = scoring_service.calculate_score(response)
        
        # Display the results
        print_separator("Results")
        print(f"Raw Score: {response_score['raw_score']}")
        print(f"Z-Score: {response_score['z_score']}")
        print(f"Percentile: {response_score['percentile']}%")
        
        if response_score['score_range']:
            print(f"Score Range: {response_score['score_range']['name']} ({response_score['score_range']['min_score']}-{response_score['score_range']['max_score']})")
            print(f"Interpretation: {response_score['score_range']['interpretation']}")
        
        # Display additional data
        if response_score['additional_data']:
            print_separator("Additional Data")
            
            # Display category scores
            if 'category_scores' in response_score['additional_data']:
                print("Category Scores:")
                for category, score in response_score['additional_data']['category_scores'].items():
                    print(f"  {category.capitalize()}: {score}")
            
            # Display subscale scores
            if 'subscales' in response_score['additional_data']:
                print("\nSubscale Scores:")
                for subscale, score in response_score['additional_data']['subscales'].items():
                    print(f"  {subscale.capitalize()}: {score}")
            
            # Display conditional adjustments
            if 'conditional_adjustments' in response_score['additional_data']:
                print("\nConditional Adjustments:")
                for adjustment in response_score['additional_data']['conditional_adjustments']:
                    print(f"  Rule: {adjustment['rule_id']}")
                    print(f"  Adjustment: {adjustment['adjustment']}")
                    print(f"  Message: {adjustment['message']}")
                    print()
        
        # Save the results to a file
        with open('enhanced_scoring_results.json', 'w') as f:
            json.dump(response_score, f, indent=2)
        print(f"Results saved to enhanced_scoring_results.json")
        
        print_separator("Success")
        print("Enhanced scoring calculation completed successfully!")
        
    except Exception as e:
        print_separator("Error")
        print(f"Error calculating enhanced score: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_scoring()
