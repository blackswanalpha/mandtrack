"""
Main models for the surveys app.
"""
from django.db import models
from django.conf import settings
from django.utils.text import slugify
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

# Import models from the main models.py file
# We'll use lazy imports to avoid circular imports
from django.apps import apps

def get_model(app_label, model_name):
    """Get a model from the app registry"""
    try:
        return apps.get_model(app_label, model_name)
    except Exception:
        return None

# Define model getters with fallbacks to actual database model names
def get_questionnaire():
    """Get the Questionnaire model"""
    # Try all possible model names
    for model_name in ['Questionnaire', 'Survey', 'questionnaire', 'survey', 'SurveysQuestionnaire']:
        model = get_model('surveys', model_name)
        if model is not None:
            return model
    return None

def get_question_type():
    """Get the QuestionType model"""
    # First try to import directly
    try:
        from surveys.models.question_type import QuestionType
        return QuestionType
    except ImportError:
        # If direct import fails, try to get from app registry
        # Try all possible model names
        for model_name in ['QuestionType', 'questiontype', 'SurveysQuestiontype']:
            model = get_model('surveys', model_name)
            if model is not None:
                return model
        return None

def get_question():
    """Get the Question model"""
    # Try all possible model names
    for model_name in ['Question', 'question', 'SurveysQuestion']:
        model = get_model('surveys', model_name)
        if model is not None:
            return model
    return None

def get_question_choice():
    """Get the QuestionChoice model"""
    # Try all possible model names
    for model_name in ['QuestionChoice', 'questionchoice', 'SurveysQuestionchoice']:
        model = get_model('surveys', model_name)
        if model is not None:
            return model
    return None

def get_qr_code():
    """Get the QRCode model"""
    # Try all possible model names
    for model_name in ['QRCode', 'qrcode', 'SurveysQrcode']:
        model = get_model('surveys', model_name)
        if model is not None:
            return model
    return None

def get_scoring_config():
    """Get the ScoringConfig model"""
    # Try all possible model names
    for model_name in ['ScoringConfig', 'scoringconfig', 'SurveysScoringconfig']:
        model = get_model('surveys', model_name)
        if model is not None:
            return model
    return None

# Re-export the models
__all__ = [
    'get_questionnaire', 'get_question_type', 'get_question', 'get_question_choice',
    'get_qr_code', 'get_scoring_config'
]
