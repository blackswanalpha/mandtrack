from django.core.management.base import BaseCommand
from django.db import models
from surveys.models import Questionnaire
from surveys.data.selector_data import (
    QUESTIONNAIRE_CATEGORIES,
    QUESTIONNAIRE_TYPES,
    QUESTIONNAIRE_STATUSES
)

class Command(BaseCommand):
    help = 'Initialize questionnaire selector data (categories, types, and statuses)'

    def handle(self, *args, **options):
        # Check if the Questionnaire model has the necessary class attributes
        # If not, add them dynamically
        
        # Add category choices if not present
        if not hasattr(Questionnaire, 'CATEGORY_CHOICES'):
            Questionnaire.CATEGORY_CHOICES = QUESTIONNAIRE_CATEGORIES
            self.stdout.write(self.style.SUCCESS('Added CATEGORY_CHOICES to Questionnaire model'))
        
        # Add type choices if not present
        if not hasattr(Questionnaire, 'TYPE_CHOICES'):
            Questionnaire.TYPE_CHOICES = QUESTIONNAIRE_TYPES
            self.stdout.write(self.style.SUCCESS('Added TYPE_CHOICES to Questionnaire model'))
        
        # Add status choices if not present
        if not hasattr(Questionnaire, 'STATUS_CHOICES'):
            Questionnaire.STATUS_CHOICES = QUESTIONNAIRE_STATUSES
            self.stdout.write(self.style.SUCCESS('Added STATUS_CHOICES to Questionnaire model'))
        
        # Update existing questionnaires with valid category, type, and status values if needed
        self.update_questionnaire_fields()
        
        self.stdout.write(self.style.SUCCESS('Successfully initialized questionnaire selector data'))
    
    def update_questionnaire_fields(self):
        """Update existing questionnaires with valid selector values"""
        # Get all valid codes for each field
        valid_categories = [code for code, _ in QUESTIONNAIRE_CATEGORIES]
        valid_types = [code for code, _ in QUESTIONNAIRE_TYPES]
        valid_statuses = [code for code, _ in QUESTIONNAIRE_STATUSES]
        
        # Set default values
        default_category = valid_categories[0] if valid_categories else 'general'
        default_type = valid_types[0] if valid_types else 'standard'
        default_status = valid_statuses[0] if valid_statuses else 'draft'
        
        # Update questionnaires with invalid or empty category values
        category_updates = 0
        for questionnaire in Questionnaire.objects.filter(
            models.Q(category__isnull=True) | 
            ~models.Q(category__in=valid_categories)
        ):
            questionnaire.category = default_category
            questionnaire.save(update_fields=['category'])
            category_updates += 1
        
        # Update questionnaires with invalid or empty type values
        type_updates = 0
        for questionnaire in Questionnaire.objects.filter(
            models.Q(type__isnull=True) | 
            ~models.Q(type__in=valid_types)
        ):
            questionnaire.type = default_type
            questionnaire.save(update_fields=['type'])
            type_updates += 1
        
        # Update questionnaires with invalid or empty status values
        status_updates = 0
        for questionnaire in Questionnaire.objects.filter(
            models.Q(status__isnull=True) | 
            ~models.Q(status__in=valid_statuses)
        ):
            questionnaire.status = default_status
            questionnaire.save(update_fields=['status'])
            status_updates += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Updated questionnaires: {category_updates} categories, {type_updates} types, {status_updates} statuses'
        ))
