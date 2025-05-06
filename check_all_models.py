import os
import sys
import django
from django.apps import apps

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Check all models for references to surveys models
problematic_models = []

for model in apps.get_models():
    for field in model._meta.fields:
        if hasattr(field, 'remote_field') and field.remote_field and field.remote_field.model:
            if hasattr(field.remote_field.model, '__name__'):
                model_name = field.remote_field.model.__name__
                if model_name in ['Questionnaire', 'Question', 'QuestionChoice', 'QRCode', 'ScoringConfig']:
                    app_label = field.remote_field.model._meta.app_label if hasattr(field.remote_field.model, '_meta') else 'unknown'
                    problematic_models.append({
                        'model': f"{model._meta.app_label}.{model.__name__}",
                        'field': field.name,
                        'references': f"{app_label}.{model_name}",
                        'should_reference': f"surveys.Surveys{model_name}"
                    })

# Print results
if problematic_models:
    print("Found potentially problematic model references:")
    for item in problematic_models:
        print(f"Model: {item['model']}, Field: {item['field']}, References: {item['references']}, Should reference: {item['should_reference']}")
else:
    print("No problematic model references found!")
