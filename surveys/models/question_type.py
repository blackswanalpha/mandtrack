"""
Question type model for the surveys app.
This module defines the QuestionType model and related functionality.
"""
from django.db import models
from surveys.data.selector_data import QUESTION_TYPES

class QuestionType(models.Model):
    """
    Model for question types
    """
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    has_choices = models.BooleanField(default=False)
    is_numeric = models.BooleanField(default=False)
    is_text = models.BooleanField(default=False)
    is_date = models.BooleanField(default=False)
    is_file = models.BooleanField(default=False)
    is_scorable = models.BooleanField(default=False)
    default_max_score = models.FloatField(default=0)
    default_scoring_weight = models.FloatField(default=1.0)
    display_order = models.PositiveIntegerField(default=0)
    icon = models.CharField(max_length=50, default='fa-question')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'surveys'
        db_table = 'surveys_questiontype'
        ordering = ['display_order', 'name']
        verbose_name = 'Question Type'
        verbose_name_plural = 'Question Types'

    def __str__(self):
        return f"{self.name} ({self.code})"

    @classmethod
    def get_default_types(cls):
        """Return default question types if none exist"""
        # Create a list of default types based on the QUESTION_TYPES from selector_data.py
        default_types = []
        for i, (code, name) in enumerate(QUESTION_TYPES):
            type_data = {
                'code': code,
                'name': name,
                'description': f"{name} question type",
                'display_order': i + 1,
                'is_text': code in ['text', 'textarea', 'email'],
                'has_choices': code in ['single_choice', 'multiple_choice', 'dropdown', 'radio', 'checkbox', 'country'],
                'is_numeric': code in ['number', 'scale', 'rating', 'slider'],
                'is_date': code in ['date', 'time'],
                'is_file': code in ['file', 'image'],
                'is_scorable': code in ['single_choice', 'multiple_choice', 'scale', 'number', 'rating'],
                'icon': get_icon_for_type(code),
            }
            default_types.append(type_data)

        return default_types


def get_icon_for_type(code):
    """Return an appropriate icon for the question type"""
    icon_map = {
        'text': 'fa-font',
        'textarea': 'fa-align-left',
        'number': 'fa-hashtag',
        'single_choice': 'fa-dot-circle',
        'multiple_choice': 'fa-check-square',
        'scale': 'fa-sliders-h',
        'date': 'fa-calendar',
        'time': 'fa-clock',
        'file': 'fa-file',
        'country': 'fa-globe',
        'email': 'fa-envelope',
        'phone': 'fa-phone',
        'image': 'fa-image',
        'signature': 'fa-signature',
        'location': 'fa-map-marker-alt',
        'rating': 'fa-star',
        'matrix': 'fa-table',
        'slider': 'fa-sliders-h',
        'dropdown': 'fa-caret-down',
        'checkbox': 'fa-check-square',
        'radio': 'fa-circle',
        'hidden': 'fa-eye-slash',
    }
    return icon_map.get(code, 'fa-question')
