import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Import models
from surveys.models import Questionnaire

# Test if we can filter by is_template
try:
    templates = Questionnaire.objects.filter(is_template=True)
    print(f"Success! Found {templates.count()} templates:")
    for template in templates:
        print(f"  - {template.title} (ID: {template.id})")
except Exception as e:
    print(f"Error: {e}")

# Test if we can access the is_template field
try:
    questionnaires = Questionnaire.objects.all()
    print(f"\nSuccess! Found {questionnaires.count()} questionnaires:")
    for q in questionnaires[:3]:  # Show just the first 3
        print(f"  - {q.title} (ID: {q.id}, is_template: {q.is_template})")
except Exception as e:
    print(f"Error: {e}")
