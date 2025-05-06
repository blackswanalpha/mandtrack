from django.core.management.base import BaseCommand
import sys
import traceback
from surveys.data.selector_data import QUESTION_TYPES

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

# Try different ways to import QuestionType
try:
    # First try direct import
    from surveys.models import QuestionType
    print("Successfully imported QuestionType directly")
except ImportError:
    try:
        # Try using the getter function
        from surveys.models.main import get_question_type
        QuestionType = get_question_type()
        print(f"Got QuestionType using getter: {QuestionType}")

        # If QuestionType is None, try to get it from the app registry
        if QuestionType is None:
            from django.apps import apps
            try:
                QuestionType = apps.get_model('surveys', 'QuestionType')
                print(f"Got QuestionType from app registry: {QuestionType}")
            except LookupError:
                print("QuestionType not found in app registry")
                # Define a minimal QuestionType class for fallback
                from django.db import models

                class QuestionType(models.Model):
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

                    @classmethod
                    def get_default_types(cls):
                        """Return default question types"""
                        default_types = []
                        for i, (code, name) in enumerate(QUESTION_TYPES):
                            type_data = {
                                'code': code,
                                'name': name,
                                'display_order': i + 1,
                                'is_text': code in ['text', 'textarea', 'email'],
                                'has_choices': code in ['single_choice', 'multiple_choice', 'dropdown', 'radio', 'checkbox', 'country'],
                                'is_numeric': code in ['number', 'scale', 'rating', 'slider'],
                                'is_date': code in ['date', 'time'],
                                'is_file': code in ['file', 'image'],
                                'is_scorable': code in ['single_choice', 'multiple_choice', 'scale', 'number', 'rating'],
                                'icon': get_icon_for_type(code),
                                'description': f"{name} question type"
                            }
                            default_types.append(type_data)
                        return default_types
                print("Created fallback QuestionType class")
    except Exception as e:
        print(f"Error importing QuestionType: {e}")
        traceback.print_exc()

class Command(BaseCommand):
    help = 'Initialize question types including country question type'

    def handle(self, *args, **options):
        # Get default question types from the model
        default_types = QuestionType.get_default_types()

        # Create a dictionary of existing types
        existing_types = {qt.code: qt for qt in QuestionType.objects.all()}

        # Add country question type if not in default types
        country_type = next((t for t in default_types if t['code'] == 'country'), None)
        if not country_type:
            default_types.append({
                'code': 'country',
                'name': 'Country',
                'is_text': False,
                'has_choices': True,
                'display_order': len(default_types) + 1
            })

        # Ensure all question types from selector_data.py are included
        for code, name in QUESTION_TYPES:
            if code not in [t['code'] for t in default_types]:
                default_types.append({
                    'code': code,
                    'name': name,
                    'is_text': code in ['text', 'textarea', 'email'],
                    'has_choices': code in ['single_choice', 'multiple_choice', 'dropdown', 'radio', 'checkbox', 'country'],
                    'is_numeric': code in ['number', 'scale', 'rating', 'slider'],
                    'is_date': code in ['date', 'time'],
                    'is_file': code in ['file', 'image'],
                    'is_scorable': code in ['single_choice', 'multiple_choice', 'scale', 'number', 'rating'],
                    'display_order': len(default_types) + 1
                })

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
            f'Successfully initialized question types: {created_count} created, {updated_count} updated'
        ))
