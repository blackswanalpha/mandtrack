from django.core.management.base import BaseCommand
from django.db import transaction
from surveys.models import Questionnaire, Question, QuestionType
from surveys.data.selector_data import (
    QUESTIONNAIRE_CATEGORIES,
    QUESTIONNAIRE_TYPES,
    QUESTIONNAIRE_STATUSES,
    QUESTION_TYPES,
    QUESTION_CATEGORIES
)

class Command(BaseCommand):
    help = 'Initialize selector data for questionnaires and questions'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Initializing selector data...'))
        
        # Initialize question types
        self.initialize_question_types()
        
        self.stdout.write(self.style.SUCCESS('Selector data initialization complete!'))
    
    @transaction.atomic
    def initialize_question_types(self):
        """Initialize question types"""
        # Get default question types from the model
        default_types = QuestionType.get_default_types()
        
        # Create a dictionary of existing types
        existing_types = {qt.code: qt for qt in QuestionType.objects.all()}
        
        # Create or update question types
        created_count = 0
        updated_count = 0
        
        for type_data in default_types:
            code = type_data['code']
            if code in existing_types:
                # Update existing type
                question_type = existing_types[code]
                for key, value in type_data.items():
                    setattr(question_type, key, value)
                question_type.save()
                updated_count += 1
            else:
                # Create new type
                QuestionType.objects.create(**type_data)
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Question types: {created_count} created, {updated_count} updated'
        ))
