"""
Script to test if the templates work with the new models.
"""
import os
import django
import uuid
import json
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils import timezone

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

from users.models import User, UserProfile
from surveys.models import Questionnaire, Question, QuestionChoice, QRCode
from feedback.models import Response, Answer, AIAnalysis

def create_test_data():
    """Create test data for templates."""
    try:
        # Try to use existing data if available
        # This avoids creating new records and potential UUID/bigint conflicts

        # Look for an existing user
        user = User.objects.filter(is_active=True).first()
        if not user:
            # If no user exists, create one with a unique username
            unique_username = f'testuser_{uuid.uuid4().hex[:8]}_{int(timezone.now().timestamp())}'
            unique_email = f'{unique_username}@example.com'

            user = User.objects.create_user(
                username=unique_username,
                email=unique_email,
                password='testpass123',
                role='user',
                email_verified=True
            )
            print(f"Created new user: {user.username}")
        else:
            print(f"Using existing user: {user.username}")

        # Look for an existing questionnaire
        questionnaire = Questionnaire.objects.filter(is_active=True).first()
        if not questionnaire:
            # Create a new questionnaire using Django's ORM
            try:
                # Get the model fields to understand what we need to provide
                questionnaire = Questionnaire.objects.create(
                    title="Test Questionnaire",
                    slug="test-questionnaire",
                    description="A test questionnaire for template testing",
                    instructions="Please answer all questions",
                    category="mental_health",
                    status="active",
                    is_template=False,
                    requires_auth=False,
                    allow_anonymous=True,
                    created_by=user,
                    is_active=True,
                    is_public=True,
                    type='standard',
                    estimated_time=10,
                    tags=json.dumps(["test", "template"]),  # Convert list to JSON string
                    language='en',
                )
                print(f"Created new questionnaire: {questionnaire.title}")

                # Create a test question
                question = Question.objects.create(
                    questionnaire=questionnaire,
                    text="How are you feeling today?",
                    description="Rate your mood",
                    type="single_choice",
                    required=True,
                    order=1,
                    is_scored=True,
                    is_visible=True,
                    scoring_weight=1.0,
                    max_score=5,
                )

                # Create choices for the question
                choices = [
                    {"text": "Very Bad", "score": 1},
                    {"text": "Bad", "score": 2},
                    {"text": "Neutral", "score": 3},
                    {"text": "Good", "score": 4},
                    {"text": "Very Good", "score": 5},
                ]

                for i, choice_data in enumerate(choices):
                    QuestionChoice.objects.create(
                        question=question,
                        text=choice_data["text"],
                        order=i + 1,
                        score=choice_data["score"],
                    )
            except Exception as e:
                print(f"Error creating questionnaire: {e}")
                # If we failed to create a questionnaire, try to find an existing one
                questionnaire = Questionnaire.objects.first()
                if not questionnaire:
                    raise Exception("Could not create or find a questionnaire")
        else:
            print(f"Using existing questionnaire: {questionnaire.title}")

        # Look for an existing response
        response = Response.objects.filter(questionnaire=questionnaire).first()
        if not response:
            try:
                # Create a test response
                response = Response.objects.create(
                    questionnaire=questionnaire,
                    user=user,
                    patient_name="Test Patient",
                    patient_email="patient@example.com",
                    score=4,
                    risk_level="low",
                    status="completed",
                    metadata=json.dumps({}),  # Convert dict to JSON string
                    notes="Test notes",
                )
                print(f"Created new response for patient: {response.patient_name}")
            except Exception as e:
                print(f"Error creating response: {e}")
                # If we failed to create a response, try to find an existing one
                response = Response.objects.first()
                if not response:
                    raise Exception("Could not create or find a response")
        else:
            print(f"Using existing response for patient: {response.patient_name}")

        print("Test data ready!")
        return {
            'user': user,
            'questionnaire': questionnaire,
            'response': response,
        }

    except Exception as e:
        print(f"Error creating test data: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_dashboard_template():
    """Test the dashboard template with the new models."""
    test_data = create_test_data()
    if not test_data:
        return

    try:
        # Get data for the dashboard template
        user = test_data['user']
        questionnaire = test_data['questionnaire']
        response = test_data['response']

        # Create context for the dashboard template
        context = {
            'total_questionnaires': 1,
            'total_responses': 1,
            'recent_responses': [response],
            'questionnaires': [questionnaire],
            'active_questionnaires': 1,
            'draft_questionnaires': 0,
            'archived_questionnaires': 0,
            'total_users': 1,
            'total_organizations': 0,
        }

        # Render the dashboard template
        template_content = render_to_string('dashboard/user_dashboard.html', context)

        # Check if the template rendered successfully
        if template_content:
            print("Dashboard template rendered successfully!")

            # Check if the questionnaire title is in the rendered template
            if questionnaire.title in template_content:
                print(f"Questionnaire title '{questionnaire.title}' found in the template.")
            else:
                print(f"Questionnaire title '{questionnaire.title}' not found in the template.")

            # Check if the response patient name is in the rendered template
            if response.patient_name in template_content:
                print(f"Response patient name '{response.patient_name}' found in the template.")
            else:
                print(f"Response patient name '{response.patient_name}' not found in the template.")
        else:
            print("Dashboard template rendering failed.")

    except Exception as e:
        print(f"Error testing dashboard template: {e}")

if __name__ == "__main__":
    print("Starting template test...")
    try:
        test_dashboard_template()
        print("Template test completed.")
    except Exception as e:
        print(f"Error in main: {e}")
