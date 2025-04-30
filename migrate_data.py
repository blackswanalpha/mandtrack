"""
Data migration script to transfer data from old models to new models.
"""
import os
import django
import uuid

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from surveys.models import Questionnaire, Question, QuestionChoice, QRCode, ScoringConfig, EmailTemplate
from feedback.models import Response, Answer, AIAnalysis
from users.models import User, UserProfile

def migrate_users():
    """Create admin user if it doesn't exist"""
    print("Creating admin user if it doesn't exist...")

    # Check if admin user exists
    if not User.objects.filter(username='admin').exists():
        # Create admin user
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin',
            email_verified=True
        )

        # Create user profile
        UserProfile.objects.create(
            user=admin_user,
            bio="Admin user",
            preferences={}
        )

        print(f"Created admin user: {admin_user.username}")
    else:
        print("Admin user already exists. Skipping...")

    # Create a regular user if it doesn't exist
    if not User.objects.filter(username='user').exists():
        # Create regular user
        user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='user123',
            role='user',
            email_verified=True
        )

        # Create user profile
        UserProfile.objects.create(
            user=user,
            bio="Regular user",
            preferences={}
        )

        print(f"Created regular user: {user.username}")
    else:
        print("Regular user already exists. Skipping...")

    print(f"Total users: {User.objects.count()}")

def migrate_surveys_to_questionnaires():
    """Migrate surveys to questionnaires"""
    from django.apps import apps

    print("Migrating surveys to questionnaires...")

    # Check if Survey model exists
    try:
        Survey = apps.get_model('surveys', 'Survey')
    except LookupError:
        print("Survey model not found. Skipping survey migration.")
        return

    # Get all surveys
    surveys = Survey.objects.all()

    # Create new questionnaires
    for survey in surveys:
        try:
            # Create new questionnaire
            questionnaire = Questionnaire(
                id=uuid.uuid4(),
                title=survey.title,
                slug=survey.slug,
                description=survey.description,
                instructions=survey.instructions,
                category=survey.category,
                status=survey.status,
                is_template=survey.is_template,
                requires_auth=survey.requires_auth,
                allow_anonymous=survey.allow_anonymous,
                created_by=User.objects.first(),  # Assign to first user (update later)
                organization=None,  # Will update later if needed
                created_at=survey.created_at,
                updated_at=survey.updated_at,
                qr_code=survey.qr_code,
                access_code=survey.access_code,
                is_active=True,
                is_public=True,
                type='standard',
                estimated_time=10,
                tags=[],
                language='en',
            )
            questionnaire.save()

            # Migrate questions
            for question in survey.questions.all():
                new_question = Question(
                    id=uuid.uuid4(),
                    questionnaire=questionnaire,
                    text=question.text,
                    description=question.description,
                    type=map_question_type(question.question_type),
                    required=question.required,
                    order=question.order,
                    is_scored=False,
                    is_visible=True,
                    scoring_weight=1.0,
                    max_score=0,
                )
                new_question.save()

                # Migrate choices
                for choice in question.choices.all():
                    QuestionChoice.objects.create(
                        id=uuid.uuid4(),
                        question=new_question,
                        text=choice.text,
                        order=choice.order,
                        score=float(choice.score),
                        is_correct=False,
                    )

            # Migrate QR codes
            for qr_code in survey.qr_codes.all():
                QRCode.objects.create(
                    id=uuid.uuid4(),
                    questionnaire=questionnaire,
                    name=qr_code.name,
                    description=qr_code.description,
                    image=qr_code.image,
                    url=qr_code.url.replace('/surveys/', '/questionnaires/'),
                    access_count=qr_code.access_count,
                    is_active=qr_code.is_active,
                    expires_at=qr_code.expires_at,
                    created_by=User.objects.first(),  # Assign to first user
                )

            print(f"Migrated survey: {survey.title}")
        except Exception as e:
            print(f"Error migrating survey {survey.title}: {e}")

    print(f"Migrated {Questionnaire.objects.count()} questionnaires")

def map_question_type(old_type):
    """Map old question types to new question types"""
    mapping = {
        'text': 'text',
        'textarea': 'textarea',
        'radio': 'single_choice',
        'checkbox': 'multiple_choice',
        'dropdown': 'single_choice',
        'scale': 'scale',
        'date': 'date',
        'time': 'time',
        'file': 'file',
    }
    return mapping.get(old_type, 'text')

def migrate_responses():
    """Migrate survey responses to new responses"""
    from django.apps import apps

    print("Migrating survey responses...")

    # Check if SurveyResponse model exists
    try:
        SurveyResponse = apps.get_model('feedback', 'SurveyResponse')
    except LookupError:
        print("SurveyResponse model not found. Skipping response migration.")
        return

    # Get all survey responses
    survey_responses = SurveyResponse.objects.all()

    # Create new responses
    for sr in survey_responses:
        try:
            # Find corresponding questionnaire
            try:
                questionnaire = Questionnaire.objects.get(title=sr.survey.title)
            except Questionnaire.DoesNotExist:
                print(f"Questionnaire not found for survey: {sr.survey.title}. Skipping...")
                continue

            # Create new response
            response = Response(
                id=uuid.uuid4(),
                questionnaire=questionnaire,
                user=None,  # Will update later if needed
                patient_name=sr.respondent_name or "",
                patient_email=sr.respondent_email or "",
                score=sr.total_score,
                risk_level=sr.risk_level,
                completion_time=None,
                ip_address=sr.ip_address,
                user_agent=sr.user_agent,
                status=sr.status,
                metadata={},
                notes=sr.notes,
                organization=None,  # Will update later if needed
                created_at=sr.started_at,
                completed_at=sr.completed_at,
            )
            response.save()

            # Migrate answers
            for answer in sr.answers.all():
                # Find corresponding question
                try:
                    question = Question.objects.get(
                        questionnaire=questionnaire,
                        text=answer.question.text
                    )
                except Question.DoesNotExist:
                    print(f"Question not found: {answer.question.text}. Skipping...")
                    continue

                # Create new answer
                new_answer = Answer(
                    id=uuid.uuid4(),
                    response=response,
                    question=question,
                    text_answer=answer.text_answer,
                    numeric_value=float(answer.numeric_value) if answer.numeric_value is not None else None,
                    date_value=answer.date_value,
                    time_value=answer.time_value,
                    file_upload=answer.file_upload,
                )
                new_answer.save()

                # Handle selected choice
                if answer.selected_choice:
                    try:
                        choice = QuestionChoice.objects.get(
                            question=question,
                            text=answer.selected_choice.text
                        )
                        new_answer.selected_choice = choice
                        new_answer.save()
                    except QuestionChoice.DoesNotExist:
                        print(f"Choice not found: {answer.selected_choice.text}. Skipping...")

                # Handle multiple choices
                for choice in answer.multiple_choices.all():
                    try:
                        new_choice = QuestionChoice.objects.get(
                            question=question,
                            text=choice.text
                        )
                        new_answer.multiple_choices.add(new_choice)
                    except QuestionChoice.DoesNotExist:
                        print(f"Choice not found: {choice.text}. Skipping...")

            # Migrate analysis result
            try:
                analysis = sr.analysis
                AIAnalysis.objects.create(
                    id=uuid.uuid4(),
                    response=response,
                    summary=analysis.summary,
                    detailed_analysis=analysis.detailed_analysis,
                    recommendations=analysis.recommendations,
                    raw_data=analysis.raw_data,
                    created_by=User.objects.first(),  # Assign to first user
                )
            except Exception as e:
                print(f"Error migrating analysis for response {sr.pk}: {e}")

            print(f"Migrated response: {sr.pk}")
        except Exception as e:
            print(f"Error migrating response {sr.pk}: {e}")

    print(f"Migrated {Response.objects.count()} responses")

def create_sample_data():
    """Create sample data if no data exists"""
    # Create sample questionnaire if none exist
    if Questionnaire.objects.count() == 0:
        print("Creating sample questionnaire...")

        # Get admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            print("No admin user found. Please run migrate_users() first.")
            return

        # Create questionnaire
        questionnaire = Questionnaire.objects.create(
            title="Mental Health Assessment",
            slug="mental-health-assessment",
            description="A comprehensive mental health assessment questionnaire",
            instructions="Please answer all questions honestly. Your responses will be kept confidential.",
            type="assessment",
            category="mental_health",
            estimated_time=15,
            status="active",
            is_active=True,
            is_public=True,
            created_by=admin_user,
        )

        # Create questions
        questions = [
            {
                "text": "How often do you feel anxious?",
                "type": "single_choice",
                "order": 1,
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "Rarely", "score": 1},
                    {"text": "Sometimes", "score": 2},
                    {"text": "Often", "score": 3},
                    {"text": "Always", "score": 4},
                ]
            },
            {
                "text": "How would you rate your overall mood?",
                "type": "scale",
                "order": 2,
            },
            {
                "text": "What symptoms have you experienced in the past week?",
                "type": "multiple_choice",
                "order": 3,
                "choices": [
                    {"text": "Fatigue", "score": 1},
                    {"text": "Insomnia", "score": 1},
                    {"text": "Loss of appetite", "score": 1},
                    {"text": "Difficulty concentrating", "score": 1},
                    {"text": "Irritability", "score": 1},
                ]
            },
            {
                "text": "Please describe any other concerns you have:",
                "type": "textarea",
                "order": 4,
            }
        ]

        for q_data in questions:
            question = Question.objects.create(
                questionnaire=questionnaire,
                text=q_data["text"],
                type=q_data["type"],
                order=q_data["order"],
                is_scored=True,
                is_visible=True,
                scoring_weight=1.0,
                max_score=4 if q_data["type"] == "scale" else 0,
            )

            # Create choices if applicable
            if "choices" in q_data:
                for i, choice_data in enumerate(q_data["choices"]):
                    QuestionChoice.objects.create(
                        question=question,
                        text=choice_data["text"],
                        order=i + 1,
                        score=choice_data["score"],
                    )

        # Create scoring config
        ScoringConfig.objects.create(
            questionnaire=questionnaire,
            name="Default Scoring",
            description="Default scoring configuration for mental health assessment",
            scoring_method="sum",
            max_score=20,
            passing_score=10,
            is_active=True,
            is_default=True,
            created_by=admin_user,
        )

        # Create QR code
        QRCode.objects.create(
            questionnaire=questionnaire,
            name=f"QR Code for {questionnaire.title}",
            description=f"QR Code for accessing {questionnaire.title}",
            url=f"/questionnaires/{questionnaire.slug}/",
            is_active=True,
            created_by=admin_user,
        )

        print("Sample questionnaire created successfully!")

@transaction.atomic
def run_migration():
    """Run the migration process"""
    print("Starting data migration...")

    # Migrate users
    migrate_users()

    # Migrate surveys to questionnaires
    migrate_surveys_to_questionnaires()

    # Migrate responses
    migrate_responses()

    # Create sample data if needed
    create_sample_data()

    print("Data migration completed successfully!")

if __name__ == "__main__":
    run_migration()
