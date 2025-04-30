"""
Script to generate sample data for all models.
"""
import os
import django
import sys
import random
from datetime import datetime, timedelta
import uuid

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Import models after Django setup
from django.contrib.auth import get_user_model
from users.models import UserProfile, ClientLoginHistory
from accounts.models import AdminProfile, AdminLoginHistory
from surveys.models import Questionnaire, Question, QuestionChoice, QRCode, ScoringConfig, EmailTemplate
from feedback.models import Response, Answer, AIAnalysis
from groups.models import Organization, OrganizationMember

User = get_user_model()

def create_users(num_users=10):
    """Create sample users"""
    print(f"Creating {num_users} sample users...")

    # Create admin user if it doesn't exist
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin',
            email_verified=True
        )

        # Create admin profile
        AdminProfile.objects.create(
            user=admin_user,
            department='IT',
            position='System Administrator',
            employee_id='EMP001',
            access_level='full',
            preferences={'theme': 'dark', 'notifications': True}
        )

        print(f"Created admin user: {admin_user.email}")

    # Create staff user if it doesn't exist
    if not User.objects.filter(username='staff').exists():
        staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staff123',
            role='staff',
            is_staff=True,
            email_verified=True
        )

        # Create admin profile
        AdminProfile.objects.create(
            user=staff_user,
            department='Support',
            position='Support Staff',
            employee_id='EMP002',
            access_level='standard',
            preferences={'theme': 'light', 'notifications': True}
        )

        print(f"Created staff user: {staff_user.email}")

    # Create regular users
    roles = ['user', 'user', 'user', 'staff']  # More weight to regular users

    for i in range(num_users):
        username = f"user{i+1}"

        if not User.objects.filter(username=username).exists():
            role = random.choice(roles)
            is_staff = role == 'staff'

            user = User.objects.create_user(
                username=username,
                email=f"{username}@example.com",
                password=f"{username}123",
                first_name=f"First{i+1}",
                last_name=f"Last{i+1}",
                role=role,
                is_staff=is_staff,
                email_verified=True
            )

            # Create user profile
            UserProfile.objects.create(
                user=user,
                bio=f"Bio for {username}",
                date_of_birth=datetime.now() - timedelta(days=random.randint(7000, 20000)),
                address_line1=f"{random.randint(1, 999)} Main St",
                city=random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']),
                state=random.choice(['NY', 'CA', 'IL', 'TX', 'AZ']),
                country='USA',
                postal_code=f"{random.randint(10000, 99999)}",
                preferences={'theme': random.choice(['light', 'dark']), 'notifications': random.choice([True, False])}
            )

            # Create admin profile for staff users
            if is_staff:
                AdminProfile.objects.create(
                    user=user,
                    department=random.choice(['HR', 'Finance', 'Marketing', 'Operations']),
                    position=random.choice(['Manager', 'Coordinator', 'Specialist', 'Analyst']),
                    employee_id=f"EMP{i+100}",
                    access_level=random.choice(['limited', 'standard']),
                    preferences={'theme': random.choice(['light', 'dark']), 'notifications': random.choice([True, False])}
                )

            print(f"Created user: {user.email} (Role: {role})")

    print(f"Total users: {User.objects.count()}")

def create_organizations(num_orgs=5):
    """Create sample organizations"""
    print(f"Creating {num_orgs} sample organizations...")

    org_types = ['healthcare', 'education', 'research', 'government', 'nonprofit', 'corporate', 'other']
    admin_user = User.objects.filter(role__in=['admin', 'staff']).first()

    for i in range(num_orgs):
        name = f"Organization {i+1}"

        if not Organization.objects.filter(name=name).exists():
            org = Organization.objects.create(
                name=name,
                description=f"Description for {name}",
                type=random.choice(org_types),
                website=f"https://www.{name.lower().replace(' ', '')}.com",
                email=f"info@{name.lower().replace(' ', '')}.com",
                phone=f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                address=f"{random.randint(1, 999)} Main St, {random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'])}",
                created_by=admin_user
            )

            # Add members to organization
            admin_users = User.objects.filter(role__in=['admin', 'staff'])
            regular_users = User.objects.filter(role='user')

            # Add admin users as admins
            for user in admin_users:
                OrganizationMember.objects.create(
                    organization=org,
                    user=user,
                    role='admin'
                )

            # Add some regular users as members
            for user in random.sample(list(regular_users), min(3, regular_users.count())):
                OrganizationMember.objects.create(
                    organization=org,
                    user=user,
                    role='staff'
                )

            print(f"Created organization: {org.name} with {org.members.count()} members")

    print(f"Total organizations: {Organization.objects.count()}")

def create_questionnaires(num_questionnaires=5):
    """Create sample questionnaires"""
    print(f"Creating {num_questionnaires} sample questionnaires...")

    categories = ['anxiety', 'depression', 'stress', 'general', 'mental_health', 'physical_health', 'education', 'custom']
    types = ['standard', 'assessment', 'screening', 'feedback', 'survey']
    status_choices = ['draft', 'active', 'archived']

    admin_users = User.objects.filter(role__in=['admin', 'staff'])
    organizations = Organization.objects.all()

    for i in range(num_questionnaires):
        title = f"Questionnaire {i+1}"

        if not Questionnaire.objects.filter(title=title).exists():
            questionnaire = Questionnaire.objects.create(
                title=title,
                description=f"Description for {title}",
                instructions=f"Instructions for completing the {title}",
                category=random.choice(categories),
                type=random.choice(types),
                status=random.choice(status_choices),
                is_active=True,
                is_public=random.choice([True, False]),
                is_template=False,
                is_adaptive=False,
                is_qr_enabled=True,
                allow_anonymous=True,
                requires_auth=False,
                version=1,
                estimated_time=random.randint(5, 30),
                language='en',
                tags=['sample', 'test', title.lower().replace(' ', '-')],
                created_by=random.choice(admin_users),
                organization=random.choice(organizations) if organizations.exists() else None
            )

            # Create questions for this questionnaire
            num_questions = random.randint(5, 15)
            for j in range(num_questions):
                question_type = random.choice(['text', 'textarea', 'number', 'single_choice', 'multiple_choice', 'scale', 'date', 'time'])
                question = Question.objects.create(
                    survey=questionnaire,
                    text=f"Question {j+1} for {title}",
                    description=f"Description for question {j+1}",
                    question_type=question_type,
                    required=random.choice([True, False]),
                    order=j+1,
                    options={
                        'min_length': 0 if question_type == 'text' else None,
                        'max_length': 500 if question_type == 'text' else None,
                        'min_value': 1 if question_type in ['number', 'scale'] else None,
                        'max_value': 5 if question_type in ['number', 'scale'] else None
                    },
                    is_scored=True,
                    scoring_weight=1.0,
                    max_score=5.0
                )

                # Create choices for choice questions
                if question_type in ['multiple_choice', 'single_choice']:
                    num_choices = random.randint(3, 6)
                    for k in range(num_choices):
                        QuestionChoice.objects.create(
                            question=question,
                            text=f"Choice {k+1} for Question {j+1}",
                            order=k+1,
                            score=random.randint(0, 5)
                        )

            # Create QR code for this questionnaire
            QRCode.objects.create(
                survey=questionnaire,
                name=f"QR Code for {title}",
                description=f"QR Code to access {title}",
                url=f"http://localhost:8000/questionnaires/{questionnaire.slug}/",
                is_active=True,
                created_by=questionnaire.created_by
            )

            # Create scoring config for this questionnaire
            ScoringConfig.objects.create(
                survey=questionnaire,
                name=f"Scoring for {title}",
                description=f"Scoring configuration for {title}",
                is_active=True,
                is_default=True,
                scoring_method=random.choice(['sum', 'average', 'weighted_sum']),
                max_score=100,
                passing_score=70,
                rules=[
                    {'min': 0, 'max': 30, 'label': 'Low', 'color': '#00FF00', 'description': 'Low risk'},
                    {'min': 31, 'max': 70, 'label': 'Medium', 'color': '#FFFF00', 'description': 'Medium risk'},
                    {'min': 71, 'max': 100, 'label': 'High', 'color': '#FF0000', 'description': 'High risk'}
                ],
                created_by=questionnaire.created_by
            )

            print(f"Created questionnaire: {questionnaire.title} with {num_questions} questions")

    print(f"Total questionnaires: {Questionnaire.objects.count()}")

def create_responses(num_responses=20):
    """Create sample responses"""
    print(f"Creating {num_responses} sample responses...")

    users = User.objects.all()
    questionnaires = Questionnaire.objects.all()
    organizations = Organization.objects.all()

    if not questionnaires.exists():
        print("No questionnaires found. Please create questionnaires first.")
        return

    for i in range(num_responses):
        questionnaire = random.choice(questionnaires)
        user = random.choice(users)

        # Create response
        response = Response.objects.create(
            survey=questionnaire,
            user=user,
            organization=random.choice(organizations) if organizations.exists() else None,
            patient_identifier=f"PAT{random.randint(1000, 9999)}",
            patient_email=f"patient{i+1}@example.com",
            patient_name=f"Patient {i+1}",
            patient_age=random.randint(18, 80),
            patient_gender=random.choice(['male', 'female', 'non-binary', 'prefer_not_to_say']),
            status='completed',
            score=random.randint(0, 100),
            risk_level=random.choice(['low', 'medium', 'high']),
            flagged_for_review=random.choice([True, False]),
            completion_time=random.randint(60, 600),
            ip_address=f"192.168.1.{random.randint(1, 255)}",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            metadata={
                'browser': 'Chrome',
                'device': 'Desktop',
                'os': 'Windows'
            },
            completed_at=datetime.now() - timedelta(days=random.randint(0, 30))
        )

        # Create answers for this response
        questions = Question.objects.filter(survey=questionnaire)

        for question in questions:
            # Create answer
            answer = Answer.objects.create(
                response=response,
                question=question
            )

            # Add answer data based on question type
            if question.question_type in ['text', 'textarea']:
                answer.text_answer = f"Text answer for question {question.id}"
            elif question.question_type in ['number', 'scale']:
                answer.numeric_value = random.randint(1, 5)
            elif question.question_type == 'date':
                answer.date_value = datetime.now() - timedelta(days=random.randint(1, 365))
            elif question.question_type == 'time':
                answer.time_value = datetime.now().time()
            elif question.question_type in ['multiple_choice', 'single_choice']:
                choices = QuestionChoice.objects.filter(question=question)

                if choices.exists():
                    if question.question_type == 'single_choice':
                        answer.selected_choice = random.choice(choices)
                    else:  # multiple_choice
                        selected_choices = random.sample(list(choices), min(random.randint(1, 3), choices.count()))
                        answer.multiple_choices.set(selected_choices)

            # Set a random score
            answer.score = random.randint(0, 5)
            answer.save()

        # Create AI analysis for this response
        AIAnalysis.objects.create(
            response=response,
            summary=f"AI analysis summary for response {response.id}",
            detailed_analysis=f"Detailed analysis for response {response.id}. This is a more in-depth analysis of the patient's responses.",
            recommendations=f"Based on the analysis, we recommend the following actions for patient {response.patient_name}...",
            insights={
                'sentiment': random.choice(['positive', 'neutral', 'negative']),
                'keywords': ['keyword1', 'keyword2', 'keyword3'],
                'risk_factors': ['factor1', 'factor2']
            },
            model_used='GPT-4',
            confidence_score=random.uniform(0.7, 0.99),
            created_by=random.choice(User.objects.filter(role__in=['admin', 'staff'])),
            raw_data={
                'model': 'GPT-4',
                'version': '1.0',
                'processing_time': random.uniform(0.5, 2.0)
            }
        )

        print(f"Created response {i+1} for questionnaire: {questionnaire.title}")

    print(f"Total responses: {Response.objects.count()}")

def create_email_templates(num_templates=5):
    """Create sample email templates"""
    print(f"Creating {num_templates} sample email templates...")

    categories = ['general', 'welcome', 'password_reset', 'verification', 'response', 'analysis', 'notification', 'reminder']
    organizations = Organization.objects.all()
    admin_users = User.objects.filter(role__in=['admin', 'staff']).first()

    for i in range(num_templates):
        category = random.choice(categories)
        name = f"{category.title()} Email Template {i+1}"

        if not EmailTemplate.objects.filter(name=name).exists():
            template = EmailTemplate.objects.create(
                name=name,
                description=f"Description for {name}",
                subject=f"Subject for {name}",
                message=f"This is the plain text message for {name}.\n\nThank you for your participation!",
                html_content=f"<p>This is the <strong>HTML</strong> content for {name}.</p><p>Thank you for your participation!</p>",
                category=category,
                is_active=True,
                is_default=i == 0,  # Make the first one default
                organization=random.choice(organizations) if organizations.exists() else None,
                created_by=admin_users,
                variables={
                    'user_name': 'User name',
                    'questionnaire_title': 'Questionnaire title',
                    'completion_date': 'Completion date'
                }
            )

            print(f"Created email template: {template.name}")

    print(f"Total email templates: {EmailTemplate.objects.count()}")

def create_login_history(num_entries=50):
    """Create sample login history"""
    print(f"Creating {num_entries} sample login history entries...")

    users = User.objects.all()

    for i in range(num_entries):
        user = random.choice(users)
        login_time = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        success = random.random() > 0.1  # 90% success rate

        if user.role in ['admin', 'staff']:
            # Create admin login history
            AdminLoginHistory.objects.create(
                user=user,
                login_time=login_time,
                ip_address=f"192.168.1.{random.randint(1, 255)}",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                session_id=str(uuid.uuid4()) if success else None,
                success=success,
                failure_reason=None if success else random.choice(['Invalid password', 'Account locked', 'Session expired'])
            )
        else:
            # Create client login history
            ClientLoginHistory.objects.create(
                user=user,
                login_time=login_time,
                ip_address=f"192.168.1.{random.randint(1, 255)}",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                device_info={'browser': 'Chrome', 'device': 'Desktop', 'os': 'Windows'},
                session_id=str(uuid.uuid4()) if success else None,
                success=success,
                failure_reason=None if success else random.choice(['Invalid password', 'Account locked', 'Session expired'])
            )

    print(f"Created {AdminLoginHistory.objects.count()} admin login history entries")
    print(f"Created {ClientLoginHistory.objects.count()} client login history entries")

def main():
    """Main function to generate sample data"""
    try:
        # Create sample data
        create_users(10)
        create_organizations(5)
        create_questionnaires(10)
        create_email_templates(5)
        create_responses(30)
        create_login_history(50)

        print("\nSample data generation completed successfully!")
    except Exception as e:
        print(f"Error generating sample data: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
