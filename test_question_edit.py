#!/usr/bin/env python
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')

# Add testserver to ALLOWED_HOSTS
from django.conf import settings
settings.ALLOWED_HOSTS.append('testserver')

django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from surveys.models import SurveysQuestionnaire, SurveysQuestion, SurveysQuestionchoice

# Create a test client
client = Client()

# Get the admin user
User = get_user_model()
admin = User.objects.filter(is_superuser=True).first()

if not admin:
    print("No admin user found. Please create an admin user first.")
    sys.exit(1)

# Force login as admin
client.force_login(admin)

# Get a questionnaire
questionnaire = SurveysQuestionnaire.objects.first()

if not questionnaire:
    print("No questionnaire found. Please create a questionnaire first.")
    sys.exit(1)

# Get a question
question = SurveysQuestion.objects.filter(survey=questionnaire).first()

if not question:
    print("No question found. Please create a question first.")
    sys.exit(1)

print(f"Testing question edit for question ID: {question.id}")

# Prepare form data
form_data = {
    'text': 'Updated Question Text',
    'description': 'Updated Description',
    'question_type': question.question_type,
    'required': 'on',
    'is_scored': 'on',
    'scoring_weight': 1,
    'max_score': 10,
    'category': 'general',
    'order': question.order,
}

# Add choices data
choices = SurveysQuestionchoice.objects.filter(question=question)
for i, choice in enumerate(choices, 1):
    form_data[f'choice_text_{i}'] = f'Updated Choice {i}'
    form_data[f'choice_order_{i}'] = i
    form_data[f'choice_score_{i}'] = i * 2

# Add a new choice
new_choice_index = len(choices) + 1
form_data[f'choice_text_{new_choice_index}'] = f'New Choice {new_choice_index}'
form_data[f'choice_order_{new_choice_index}'] = new_choice_index
form_data[f'choice_score_{new_choice_index}'] = new_choice_index * 2

# Submit the form
response = client.post(f'/surveys/{questionnaire.pk}/questions/{question.id}/edit/', form_data)

# Check the response
if response.status_code == 302:  # Redirect on success
    print("Question updated successfully!")

    # Verify the changes
    updated_question = SurveysQuestion.objects.get(id=question.id)
    print(f"Updated question text: {updated_question.text}")

    # Check choices
    updated_choices = SurveysQuestionchoice.objects.filter(question=updated_question).order_by('order')
    print(f"Number of choices: {updated_choices.count()}")

    for i, choice in enumerate(updated_choices, 1):
        print(f"Choice {i}: {choice.text}, Score: {choice.score}")
else:
    print(f"Failed to update question. Status code: {response.status_code}")
    print(response.content.decode('utf-8')[:500])  # Print first 500 chars of response
