from django.test import TestCase
from analytics.services.gemini_service import GeminiService
import os
import unittest

class GeminiServiceTestCase(TestCase):
    """
    Test the Gemini service
    """
    
    def setUp(self):
        """
        Set up the test case
        """
        # Skip tests if no API key is available
        self.api_key = os.environ.get('GEMINI_API_KEY', None)
        if not self.api_key:
            self.skipTest("No Gemini API key available")
        
        self.service = GeminiService(api_key=self.api_key)
    
    def test_analyze_questionnaire_data(self):
        """
        Test analyzing questionnaire data
        """
        # Create sample data
        questionnaire_info = {
            "title": "Mental Health Assessment",
            "category": "mental_health",
            "description": "A questionnaire to assess mental health",
            "total_questions": 5,
            "scoring_method": "weighted_sum"
        }
        
        # Sample response data
        data = {
            "questionnaire": questionnaire_info,
            "respondent": {
                "age": 35,
                "gender": "female",
                "completion_time": 300,
                "total_score": 15,
                "risk_level": "medium"
            },
            "answers": [
                {
                    "question_text": "How often do you feel anxious?",
                    "question_type": "scale",
                    "question_category": "anxiety",
                    "is_scored": True,
                    "answer": 4,
                    "score": 4,
                    "weight": 1.0,
                    "weighted_score": 4.0
                },
                {
                    "question_text": "How often do you feel sad or down?",
                    "question_type": "scale",
                    "question_category": "depression",
                    "is_scored": True,
                    "answer": 3,
                    "score": 3,
                    "weight": 1.0,
                    "weighted_score": 3.0
                },
                {
                    "question_text": "Do you have trouble sleeping?",
                    "question_type": "single_choice",
                    "question_category": "sleep",
                    "is_scored": True,
                    "answer": "Yes, frequently",
                    "score": 4,
                    "weight": 1.0,
                    "weighted_score": 4.0
                },
                {
                    "question_text": "What coping strategies do you use?",
                    "question_type": "multiple_choice",
                    "question_category": "coping",
                    "is_scored": False,
                    "answer": ["Exercise", "Meditation", "Talking to friends"]
                },
                {
                    "question_text": "Any additional comments?",
                    "question_type": "text",
                    "question_category": "general",
                    "is_scored": False,
                    "answer": "I've been feeling more stressed than usual lately due to work pressure."
                }
            ]
        }
        
        # Analyze the data
        result = self.service.analyze_questionnaire_data(data, questionnaire_info)
        
        # Check that the result has the expected structure
        self.assertIn('summary', result)
        self.assertIn('detailed_analysis', result)
        self.assertIn('recommendations', result)
        
        # Print the result for manual inspection
        print("\nGemini API Analysis Result:")
        print(f"Summary: {result.get('summary', '')[:100]}...")
        print(f"Analysis: {result.get('detailed_analysis', '')[:100]}...")
        print(f"Recommendations: {result.get('recommendations', '')[:100]}...")
