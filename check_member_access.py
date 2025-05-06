import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Import the model directly
from members.models import MemberAccess

# Check the model field
print(f"MemberAccess.questionnaire field points to: {MemberAccess._meta.get_field('questionnaire').remote_field.model.__name__}")
print(f"Model app label: {MemberAccess._meta.get_field('questionnaire').remote_field.model._meta.app_label}")
print(f"Full model path: {MemberAccess._meta.get_field('questionnaire').remote_field.model._meta.app_label}.{MemberAccess._meta.get_field('questionnaire').remote_field.model.__name__}")
