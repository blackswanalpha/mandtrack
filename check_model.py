import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Import the model
from members.models import MemberAccess

# Check if the model can be imported without errors
print("MemberAccess model imported successfully!")
print(f"MemberAccess.questionnaire field points to: {MemberAccess._meta.get_field('questionnaire').remote_field.model.__name__}")
