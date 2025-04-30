#!/usr/bin/env python
"""
Script to create test data for MindTrack development and send it to Neon Postgres database
"""
import os
import sys
import django
import random
import time
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Add a small delay to ensure database connection is established
time.sleep(1)
print("Connected to database...")

from django.contrib.auth import get_user_model
from django.utils import timezone
from surveys.models import Survey, Question, QuestionChoice, QRCode
from feedback.models import SurveyResponse, Answer
from groups.models import Organization, OrganizationMember

User = get_user_model()

def create_users():
    """Create test users"""
    print("Creating test users...")

    # Create admin user if it doesn't exist
    admin_user, created = User.objects.get_or_create(
        username='admin',
        email='admin@example.com',
        defaults={
            'is_staff': True,
            'is_superuser': True,
        }
    )

    if created:
        admin_user.set_password('adminpassword')
        admin_user.save()
        print(f"Created admin user: {admin_user.email}")

    # Create regular users
    regular_users = []
    for i in range(1, 6):
        user, created = User.objects.get_or_create(
            username=f'user{i}',
            email=f'user{i}@example.com',
        )

        if created:
            user.set_password(f'password{i}')
            user.save()
            print(f"Created regular user: {user.email}")

        regular_users.append(user)

    return admin_user, regular_users

def create_organizations(users):
    """Create test organizations"""
    print("Creating test organizations...")

    admin_user = users[0]
    regular_users = users[1]

    organizations = []
    org_types = ['healthcare', 'education', 'corporate', 'nonprofit', 'government']

    for i in range(3):
        org, created = Organization.objects.get_or_create(
            name=f"Organization {i+1}",
            defaults={
                'description': f"This is test organization {i+1}",
                'type': random.choice(org_types),
                'created_by': admin_user,
            }
        )

        if created:
            print(f"Created organization: {org.name}")

        # Add members to the organization
        for user in regular_users[:3]:
            member, member_created = OrganizationMember.objects.get_or_create(
                organization=org,
                user=user,
                defaults={
                    'role': 'member',
                }
            )

            if member_created:
                print(f"Added {user.email} to {org.name}")

        organizations.append(org)

    return organizations

def create_surveys(users, organizations):
    """Create test surveys"""
    print("Creating test surveys...")

    admin_user = users[0]
    regular_users = users[1]

    surveys = []
    survey_categories = ['mental_health', 'satisfaction', 'feedback', 'assessment', 'custom']
    survey_statuses = ['draft', 'active', 'archived']

    # Create surveys for each organization
    for i, org in enumerate(organizations):
        for j in range(2):
            survey, created = Survey.objects.get_or_create(
                title=f"{org.name} Survey {j+1}",
                defaults={
                    'slug': f"{org.name.lower().replace(' ', '-')}-survey-{j+1}",
                    'description': f"This is a test survey for {org.name}",
                    'instructions': "Please answer all questions honestly.",
                    'category': random.choice(survey_categories),
                    'status': random.choice(survey_statuses),
                    'created_by': admin_user,
                    'organization': org,
                }
            )

            if created:
                print(f"Created survey: {survey.title}")

                # Create questions for the survey
                for k in range(5):
                    question = Question.objects.create(
                        survey=survey,
                        text=f"Question {k+1} for {survey.title}",
                        question_type='radio',
                        required=True,
                        order=k+1,
                    )

                    # Create choices for multiple choice questions
                    for l in range(4):
                        QuestionChoice.objects.create(
                            question=question,
                            text=f"Choice {l+1}",
                            order=l+1,
                            score=l+1,
                        )

                    print(f"  Created question: {question.text}")

            surveys.append(survey)

    # Create personal surveys for regular users
    for i, user in enumerate(regular_users[:2]):
        survey, created = Survey.objects.get_or_create(
            title=f"{user.username}'s Personal Survey",
            defaults={
                'slug': f"{user.username.lower()}-personal-survey",
                'description': f"This is a personal survey created by {user.username}",
                'instructions': "Please answer all questions honestly.",
                'category': 'custom',
                'status': 'active',
                'created_by': user,
            }
        )

        if created:
            print(f"Created personal survey: {survey.title}")

            # Create questions for the survey
            for k in range(3):
                question = Question.objects.create(
                    survey=survey,
                    text=f"Question {k+1} for {survey.title}",
                    question_type='radio',
                    required=True,
                    order=k+1,
                )

                # Create choices for multiple choice questions
                for l in range(4):
                    QuestionChoice.objects.create(
                        question=question,
                        text=f"Choice {l+1}",
                        order=l+1,
                        score=l+1,
                    )

                print(f"  Created question: {question.text}")

        surveys.append(survey)

    return surveys

def create_responses(users, surveys):
    """Create test responses"""
    print("Creating test responses...")

    admin_user = users[0]
    regular_users = users[1]

    responses = []

    # Create responses for each survey
    for survey in surveys:
        if survey.status == 'active':
            # Create responses from regular users
            for user in regular_users[:3]:
                # Skip if user created the survey
                if user == survey.created_by:
                    continue

                response, created = SurveyResponse.objects.get_or_create(
                    survey=survey,
                    respondent=user,
                    defaults={
                        'status': 'completed',
                        'started_at': timezone.now() - timedelta(days=random.randint(1, 30)),
                        'completed_at': timezone.now() - timedelta(days=random.randint(0, 10)),
                        'ip_address': '127.0.0.1',
                        'user_agent': 'Mozilla/5.0 (Test User Agent)',
                    }
                )

                if created:
                    # Set a random total score
                    response.total_score = random.randint(5, 20)
                    response.save()

                    print(f"Created response for {survey.title} by {user.email}")

                    # Create answers for each question
                    for question in survey.questions.all():
                        # Get a random choice
                        choices = question.choices.all()
                        if choices.exists():
                            choice = random.choice(list(choices))

                            Answer.objects.create(
                                response=response,
                                question=question,
                                selected_choice=choice,
                                text_answer='',
                                numeric_value=choice.score,
                            )

                responses.append(response)

            # Create anonymous responses
            for i in range(2):
                response, created = SurveyResponse.objects.get_or_create(
                    survey=survey,
                    respondent_email=f"anonymous{i+1}@example.com",
                    defaults={
                        'respondent_name': f"Anonymous User {i+1}",
                        'status': 'completed',
                        'started_at': timezone.now() - timedelta(days=random.randint(1, 30)),
                        'completed_at': timezone.now() - timedelta(days=random.randint(0, 10)),
                        'ip_address': '127.0.0.1',
                        'user_agent': 'Mozilla/5.0 (Test User Agent)',
                    }
                )

                if created:
                    # Set a random total score
                    response.total_score = random.randint(5, 20)
                    response.save()

                    print(f"Created anonymous response for {survey.title}")

                    # Create answers for each question
                    for question in survey.questions.all():
                        # Get a random choice
                        choices = question.choices.all()
                        if choices.exists():
                            choice = random.choice(list(choices))

                            Answer.objects.create(
                                response=response,
                                question=question,
                                selected_choice=choice,
                                text_answer='',
                                numeric_value=choice.score,
                            )

                responses.append(response)

    return responses

def create_qr_codes(users, surveys):
    """Create test QR codes"""
    print("Creating test QR codes...")

    admin_user = users[0]

    qr_codes = []

    # Create QR codes for active surveys
    for survey in surveys:
        if survey.status == 'active':
            qr_code, created = QRCode.objects.get_or_create(
                survey=survey,
                name=f"QR Code for {survey.title}",
                defaults={
                    'description': f"Scan this QR code to access {survey.title}",
                    'url': f"http://localhost:8000/surveys/{survey.slug}/",
                    'is_active': True,
                    'created_by': admin_user,
                }
            )

            if created:
                print(f"Created QR code for {survey.title}")

            qr_codes.append(qr_code)

    return qr_codes

def main():
    """Main function to create test data"""
    print("Creating test data for MindTrack and sending to Neon Postgres database...")

    try:
        # Create users
        users = create_users()

        # Create organizations
        organizations = create_organizations(users)

        # Create surveys
        surveys = create_surveys(users, organizations)

        # Create responses
        responses = create_responses(users, surveys)

        # Create QR codes
        qr_codes = create_qr_codes(users, surveys)

        print("\nTest data creation complete!")
        print(f"Created {len(users[1]) + 1} users")
        print(f"Created {len(organizations)} organizations")
        print(f"Created {len(surveys)} surveys")
        print(f"Created {len(responses)} responses")
        print(f"Created {len(qr_codes)} QR codes")
        print("\nAll data has been successfully sent to the Neon Postgres database!")

    except Exception as e:
        print(f"\nError creating test data: {e}")
        print("Please check your database connection and try again.")

if __name__ == '__main__':
    main()
