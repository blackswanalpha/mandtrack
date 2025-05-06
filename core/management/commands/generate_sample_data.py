import random
import datetime
import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from surveys.models import Questionnaire, Question, QuestionChoice, QuestionType
from feedback.models import Response, Answer
from groups.models import Organization, OrganizationMember

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate sample data for the dashboard'

    def add_arguments(self, parser):
        parser.add_argument('--questionnaires', type=int, default=5, help='Number of questionnaires to create')
        parser.add_argument('--responses', type=int, default=50, help='Number of responses to create')
        parser.add_argument('--organizations', type=int, default=3, help='Number of organizations to create')

    def handle(self, *args, **options):
        num_questionnaires = options['questionnaires']
        num_responses = options['responses']
        num_organizations = options['organizations']

        self.stdout.write(self.style.SUCCESS(f'Creating {num_organizations} organizations...'))
        organizations = self.create_organizations(num_organizations)

        self.stdout.write(self.style.SUCCESS(f'Creating {num_questionnaires} questionnaires...'))
        questionnaires = self.create_questionnaires(num_questionnaires, organizations)

        self.stdout.write(self.style.SUCCESS(f'Creating {num_responses} responses...'))
        self.create_responses(num_responses, questionnaires)

        self.stdout.write(self.style.SUCCESS('Sample data generation complete!'))

    def create_organizations(self, count):
        organizations = []
        for i in range(count):
            org_name = f"Organization {i+1}"
            org, created = Organization.objects.get_or_create(
                name=org_name,
                defaults={
                    'description': f"Description for {org_name}",
                    'website': f"https://www.org{i+1}.com",
                    'type': random.choice(['healthcare', 'education', 'research', 'government', 'nonprofit', 'corporate', 'other'])
                }
            )
            organizations.append(org)
            self.stdout.write(f"Created organization: {org.name}")

            # Add some members to the organization
            admin_users = User.objects.filter(is_staff=True)
            for user in admin_users:
                OrganizationMember.objects.get_or_create(
                    organization=org,
                    user=user,
                    defaults={
                        'role': 'admin',
                        'is_active': True
                    }
                )
        return organizations

    def create_questionnaires(self, count, organizations):
        questionnaires = []

        # Get or create question types
        try:
            # Try to get existing question types
            multiple_choice_type = QuestionType.objects.get(code='multiple_choice')
            text_type = QuestionType.objects.get(code='text')
            scale_type = QuestionType.objects.get(code='scale')
        except QuestionType.DoesNotExist:
            # Create default question types if they don't exist
            for type_data in QuestionType.get_default_types():
                QuestionType.objects.create(**type_data)

            # Now get the types we need
            multiple_choice_type = QuestionType.objects.get(code='multiple_choice')
            text_type = QuestionType.objects.get(code='text')
            scale_type = QuestionType.objects.get(code='scale')

        question_types = [multiple_choice_type, text_type, scale_type]

        # Create questionnaires
        for i in range(count):
            title = f"Sample Questionnaire {i+1}"
            description = f"This is a sample questionnaire {i+1} for testing purposes."

            # Randomly assign to an organization or None
            organization = random.choice(organizations) if organizations and random.choice([True, False]) else None

            # Get a random admin user
            admin_user = User.objects.filter(is_staff=True).first()

            questionnaire = Questionnaire.objects.create(
                title=title,
                description=description,
                organization=organization,
                created_by=admin_user,
                status=random.choice(['draft', 'active', 'archived']),
                access_code=f"CODE{i+1}{uuid.uuid4().hex[:6]}",
                is_public=random.choice([True, False]),
                allow_anonymous=True
            )

            # Create questions for this questionnaire
            self.create_questions(questionnaire, question_types)

            questionnaires.append(questionnaire)
            self.stdout.write(f"Created questionnaire: {questionnaire.title}")

        return questionnaires

    def create_questions(self, questionnaire, question_types):
        # Create 5-10 questions per questionnaire
        num_questions = random.randint(5, 10)

        for i in range(num_questions):
            question_type = random.choice(question_types)

            question = Question.objects.create(
                survey=questionnaire,  # Using 'survey' field as mentioned in the project overview
                text=f"Question {i+1} for {questionnaire.title}?",
                description=f"Description for question {i+1}",
                question_type=question_type.code,
                question_type_obj=question_type,
                required=random.choice([True, False]),
                order=i+1
            )

            # If multiple choice, create choices
            if question_type.name == "Multiple Choice":
                num_choices = random.randint(3, 5)
                for j in range(num_choices):
                    QuestionChoice.objects.create(
                        question=question,
                        text=f"Choice {j+1} for question {i+1}",
                        order=j+1
                    )

            self.stdout.write(f"  Created question: {question.text}")

    def create_responses(self, count, questionnaires):
        if not questionnaires:
            self.stdout.write(self.style.WARNING('No questionnaires available to create responses for.'))
            return

        # Create responses
        for i in range(count):
            questionnaire = random.choice(questionnaires)

            # Create response
            response = Response.objects.create(
                survey=questionnaire,  # Using 'survey' field as mentioned in the project overview
                status=random.choice(['completed', 'in_progress', 'abandoned']),
                patient_email=f"patient{i+1}@example.com",
                patient_gender=random.choice(['male', 'female', 'non-binary', 'prefer_not_to_say']),
                patient_age=random.randint(18, 80),
                score=random.randint(0, 100) if random.choice([True, False]) else None,
                completion_time=random.randint(60, 1800) if random.choice([True, False]) else None,
                created_at=timezone.now() - datetime.timedelta(days=random.randint(0, 30)),
                completed_at=timezone.now() - datetime.timedelta(days=random.randint(0, 29)) if random.choice([True, False]) else None,
                metadata={
                    'device': random.choice(['desktop', 'mobile', 'tablet']),
                    'browser': random.choice(['chrome', 'firefox', 'safari', 'edge']),
                    'os': random.choice(['windows', 'macos', 'linux', 'ios', 'android']),
                    'ip_address': f"192.168.1.{random.randint(1, 255)}"
                },
                risk_level=random.choice(['low', 'medium', 'high', 'critical'])
            )

            # Create answers for this response
            questions = Question.objects.filter(survey=questionnaire)
            for question in questions:
                if random.choice([True, False, True]):  # 2/3 chance of answering
                    if question.question_type == "multiple_choice":
                        choices = QuestionChoice.objects.filter(question=question)
                        if choices.exists():
                            answer = Answer.objects.create(
                                response=response,
                                question=question,
                                text_answer=""
                            )
                            # Add random choices (1 or more)
                            num_choices = random.randint(1, min(3, choices.count()))
                            selected_choices = random.sample(list(choices), num_choices)
                            answer.multiple_choices.add(*selected_choices)
                    elif question.question_type == "scale":
                        Answer.objects.create(
                            response=response,
                            question=question,
                            text_answer=str(random.randint(1, 10))
                        )
                    else:  # Text
                        Answer.objects.create(
                            response=response,
                            question=question,
                            text_answer=f"Sample answer for question {question.id}"
                        )

            self.stdout.write(f"Created response {i+1} for {questionnaire.title}")
