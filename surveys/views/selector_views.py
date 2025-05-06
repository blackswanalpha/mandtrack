from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from surveys.data.selector_data import (
    QUESTIONNAIRE_CATEGORIES,
    QUESTIONNAIRE_TYPES,
    QUESTIONNAIRE_STATUSES,
    QUESTION_TYPES,
    QUESTION_CATEGORIES
)
# Import the QuestionType model from the correct location
from django.db import models

@login_required
def selector_data_view(request):
    """View to display all selector data"""
    # We're not using the database model for question types anymore
    # Just use the data from selector_data.py

    context = {
        'questionnaire_categories': QUESTIONNAIRE_CATEGORIES,
        'questionnaire_types': QUESTIONNAIRE_TYPES,
        'questionnaire_statuses': QUESTIONNAIRE_STATUSES,
        'question_types': QUESTION_TYPES,
        'question_categories': QUESTION_CATEGORIES,
    }

    return render(request, 'surveys/selector_data.html', context)
