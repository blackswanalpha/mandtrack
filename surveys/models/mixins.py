"""
Model mixins for the surveys app.
These mixins provide reusable functionality for models.
"""
from django.db import models
from surveys.data.selector_data import (
    QUESTIONNAIRE_CATEGORIES,
    QUESTIONNAIRE_TYPES,
    QUESTIONNAIRE_STATUSES
)

class QuestionnaireSelectorMixin:
    """
    Mixin to add selector fields to the Questionnaire model.
    This ensures that the model has the proper choices for category, type, and status fields.
    """
    # Define the choices as class attributes
    CATEGORY_CHOICES = QUESTIONNAIRE_CATEGORIES
    TYPE_CHOICES = QUESTIONNAIRE_TYPES
    STATUS_CHOICES = QUESTIONNAIRE_STATUSES
    
    @classmethod
    def add_to_class(cls, model_class):
        """
        Add this mixin's attributes to the given model class.
        """
        # Add choices as class attributes
        model_class.CATEGORY_CHOICES = cls.CATEGORY_CHOICES
        model_class.TYPE_CHOICES = cls.TYPE_CHOICES
        model_class.STATUS_CHOICES = cls.STATUS_CHOICES
        
        # Define the fields with choices if they don't already exist
        if not hasattr(model_class, 'category') or not model_class._meta.get_field('category').choices:
            # If the field exists but doesn't have choices, update it
            try:
                field = model_class._meta.get_field('category')
                field.choices = cls.CATEGORY_CHOICES
            except models.FieldDoesNotExist:
                # If the field doesn't exist, add it
                category_field = models.CharField(
                    max_length=50, 
                    choices=cls.CATEGORY_CHOICES,
                    blank=True, 
                    null=True,
                    help_text="The category of the questionnaire"
                )
                model_class.add_to_class('category', category_field)
        
        if not hasattr(model_class, 'type') or not model_class._meta.get_field('type').choices:
            try:
                field = model_class._meta.get_field('type')
                field.choices = cls.TYPE_CHOICES
            except models.FieldDoesNotExist:
                type_field = models.CharField(
                    max_length=50, 
                    choices=cls.TYPE_CHOICES,
                    default='standard',
                    help_text="The type of the questionnaire"
                )
                model_class.add_to_class('type', type_field)
        
        if not hasattr(model_class, 'status') or not model_class._meta.get_field('status').choices:
            try:
                field = model_class._meta.get_field('status')
                field.choices = cls.STATUS_CHOICES
            except models.FieldDoesNotExist:
                status_field = models.CharField(
                    max_length=20, 
                    choices=cls.STATUS_CHOICES,
                    default='draft',
                    help_text="The status of the questionnaire"
                )
                model_class.add_to_class('status', status_field)
        
        return model_class
