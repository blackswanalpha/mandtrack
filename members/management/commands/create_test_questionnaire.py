from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from groups.models import Organization
from surveys.models import Questionnaire, Question, QuestionChoice
from members.models import Member, MemberAccess

class Command(BaseCommand):
    help = 'Creates a test questionnaire with questions and member access'

    def handle(self, *args, **options):
        # Check if there are any organizations
        if not Organization.objects.exists():
            self.stdout.write(self.style.ERROR('No organizations found. Please create an organization first.'))
            return

        # Get the first organization
        organization = Organization.objects.first()

        # Create a test questionnaire
        questionnaire, created = Questionnaire.objects.get_or_create(
            title='Mental Health Assessment',
            defaults={
                'description': 'A brief assessment of mental health and well-being',
                'category': 'mental_health',
                'estimated_time': 10,
                'is_active': True,
                'is_adaptive': False,
                'is_qr_enabled': True,
                'is_template': False,
                'is_public': True,
                'allow_anonymous': True,
                'requires_auth': False,
                'version': 1,
                'tags': ['mental_health', 'assessment', 'well-being'],
                'language': 'en',
                'organization': organization,
                'created_by': organization.created_by,
                'access_code': 'MENTAL123'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created test questionnaire: {questionnaire.title}'))
        else:
            self.stdout.write(self.style.WARNING(f'Test questionnaire already exists: {questionnaire.title}'))
            # Delete existing questions to avoid duplicates
            Question.objects.filter(survey=questionnaire).delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted existing questions for {questionnaire.title}'))

        # Create test questions
        questions_data = [
            {
                'text': 'How would you rate your overall mental health?',
                'description': 'Consider your emotional, psychological, and social well-being',
                'question_type': 'single_choice',
                'required': True,
                'order': 1,
                'choices': [
                    {'text': 'Excellent', 'score': 5},
                    {'text': 'Good', 'score': 4},
                    {'text': 'Fair', 'score': 3},
                    {'text': 'Poor', 'score': 2},
                    {'text': 'Very poor', 'score': 1}
                ]
            },
            {
                'text': 'How often do you feel stressed?',
                'description': 'Consider your stress levels over the past month',
                'question_type': 'single_choice',
                'required': True,
                'order': 2,
                'choices': [
                    {'text': 'Never', 'score': 5},
                    {'text': 'Rarely', 'score': 4},
                    {'text': 'Sometimes', 'score': 3},
                    {'text': 'Often', 'score': 2},
                    {'text': 'Always', 'score': 1}
                ]
            },
            {
                'text': 'How would you rate your sleep quality?',
                'description': 'Consider your sleep over the past month',
                'question_type': 'single_choice',
                'required': True,
                'order': 3,
                'choices': [
                    {'text': 'Excellent', 'score': 5},
                    {'text': 'Good', 'score': 4},
                    {'text': 'Fair', 'score': 3},
                    {'text': 'Poor', 'score': 2},
                    {'text': 'Very poor', 'score': 1}
                ]
            },
            {
                'text': 'Which of the following symptoms have you experienced in the past two weeks?',
                'description': 'Select all that apply',
                'question_type': 'multiple_choice',
                'required': False,
                'order': 4,
                'choices': [
                    {'text': 'Feeling down or depressed', 'score': 1},
                    {'text': 'Little interest or pleasure in activities', 'score': 1},
                    {'text': 'Trouble falling or staying asleep', 'score': 1},
                    {'text': 'Feeling tired or having little energy', 'score': 1},
                    {'text': 'Poor appetite or overeating', 'score': 1},
                    {'text': 'Trouble concentrating', 'score': 1},
                    {'text': 'None of the above', 'score': 0}
                ]
            },
            {
                'text': 'On a scale of 1-10, how would you rate your anxiety level?',
                'description': '1 being no anxiety, 10 being severe anxiety',
                'question_type': 'number',
                'required': True,
                'order': 5,
                'min_value': 1,
                'max_value': 10
            },
            {
                'text': 'What activities do you find helpful for managing stress?',
                'description': 'Please describe briefly',
                'question_type': 'textarea',
                'required': False,
                'order': 6
            }
        ]

        for question_data in questions_data:
            # Create the question
            question = Question.objects.create(
                survey=questionnaire,
                text=question_data['text'],
                description=question_data.get('description', ''),
                question_type=question_data['question_type'],
                required=question_data.get('required', False),
                order=question_data.get('order', 1)
            )

            # Store min_value and max_value in metadata if needed
            if 'min_value' in question_data or 'max_value' in question_data:
                metadata = {}
                if 'min_value' in question_data:
                    metadata['min_value'] = question_data['min_value']
                if 'max_value' in question_data:
                    metadata['max_value'] = question_data['max_value']

                # Check if the Question model has a metadata field
                if hasattr(question, 'metadata'):
                    question.metadata = metadata
                    question.save()

            # Create choices if applicable
            if 'choices' in question_data:
                for i, choice_data in enumerate(question_data['choices']):
                    QuestionChoice.objects.create(
                        question=question,
                        text=choice_data['text'],
                        score=choice_data.get('score'),
                        order=i + 1
                    )

            self.stdout.write(self.style.SUCCESS(f'Created question: {question.text}'))

        # Create or update member
        member, created = Member.objects.get_or_create(
            member_number='TEST001',
            defaults={
                'name': 'Test Member',
                'email': 'test@example.com',
                'phone': '1234567890',
                'organization': organization,
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created test member: {member}'))
        else:
            self.stdout.write(self.style.WARNING(f'Test member already exists: {member}'))

        # Create a test member access
        access_code = 'ACCESS123'
        member_access, created = MemberAccess.objects.get_or_create(
            member=member,
            questionnaire=questionnaire,
            defaults={
                'access_code': access_code,
                'is_used': False,
                'expires_at': timezone.now() + timedelta(days=30)
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created test member access with code: {access_code}'))
        else:
            # Update the existing access
            member_access.access_code = access_code
            member_access.is_used = False
            member_access.expires_at = timezone.now() + timedelta(days=30)
            member_access.save()
            self.stdout.write(self.style.WARNING(f'Updated test member access with code: {access_code}'))

        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))
        self.stdout.write(self.style.SUCCESS(f'Member Number: TEST001'))
        self.stdout.write(self.style.SUCCESS(f'Access Code: ACCESS123'))
