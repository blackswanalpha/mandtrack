import os
import sys
import django
from django.core import checks
from django.apps import apps

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Get the members app config
members_app_config = apps.get_app_config('members')

# Run model checks for the members app
errors = checks.run_checks(app_configs=[members_app_config])

if errors:
    print("Errors found in members app:")
    for error in errors:
        print(f"- {error}")
else:
    print("No errors found in members app!")

# Specifically check the MemberAccess model
from members.models import MemberAccess
print(f"\nMemberAccess.questionnaire field points to: {MemberAccess._meta.get_field('questionnaire').remote_field.model.__name__}")
