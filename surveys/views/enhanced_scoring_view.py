"""
View for displaying enhanced scoring results.
"""
from django.shortcuts import render
import json
import os

def enhanced_scoring_results(request):
    """
    View for displaying enhanced scoring results.
    """
    # Load the enhanced scoring results from the JSON file
    results_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'enhanced_scoring_results.json')
    
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
    except Exception as e:
        # If the file doesn't exist or can't be read, use sample data
        results = {
            "response_id": 1,
            "scoring_system_id": 1,
            "raw_score": 69,
            "z_score": 1.27,
            "percentile": 89.8,
            "additional_data": {
                "category_scores": {
                    "anxiety": 8,
                    "depression": 7,
                    "stress": 4,
                    "wellbeing": 1
                },
                "subscales": {
                    "cognitive": 3,
                    "emotional": 9,
                    "physical": 2,
                    "behavioral": 0
                }
            },
            "score_range": {
                "id": 2,
                "name": "Medium",
                "min_score": 31,
                "max_score": 70,
                "color": "yellow",
                "interpretation": "This score indicates a moderate level of the measured attribute."
            }
        }
    
    # Prepare the context for the template
    context = {
        'raw_score': results.get('raw_score', 0),
        'z_score': results.get('z_score', 0),
        'percentile': results.get('percentile', 0),
        'score_range': results.get('score_range', {}),
        'category_scores': results.get('additional_data', {}).get('category_scores', {}),
        'subscales': results.get('additional_data', {}).get('subscales', {}),
        'conditional_adjustments': results.get('additional_data', {}).get('conditional_adjustments', []),
        'raw_score_percentage': results.get('raw_score', 0),
        'z_score_percentage': (results.get('z_score', 0) + 3) / 6 * 100,  # Convert z-score to percentage (range -3 to +3)
        'max_score': results.get('score_range', {}).get('max_score', 100),
        'questionnaire_title': 'Test Questionnaire',
        'completed_at': 'May 4, 2025, 1:30 p.m.',
        'scoring_system_name': 'Enhanced Scoring System',
        'back_url': '/questionnaires/',
        'feedback_url': '/questionnaires/feedback/',
        'pdf_export_url': '/questionnaires/export/pdf/',
        'email_report_url': '/questionnaires/export/email/',
    }
    
    return render(request, 'surveys/enhanced_scoring_results.html', context)
