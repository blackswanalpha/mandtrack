from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from surveys.models import Questionnaire, Question
from feedback.models import Response, Answer
from groups.models import Organization
import random
from datetime import timedelta
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate realistic sample data for the admin dashboard'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=50, help='Number of users to generate')
        parser.add_argument('--questionnaires', type=int, default=20, help='Number of questionnaires to generate')
        parser.add_argument('--responses', type=int, default=500, help='Number of responses to generate')
        parser.add_argument('--days', type=int, default=90, help='Number of days in the past to generate data for')

    def handle(self, *args, **options):
        num_users = options['users']
        num_questionnaires = options['questionnaires']
        num_responses = options['responses']
        days_range = options['days']

        try:
            with transaction.atomic():
                self.stdout.write(self.style.SUCCESS('Starting data generation...'))
                
                # Create admin user if it doesn't exist
                admin_user = self._ensure_admin_exists()
                
                # Create organizations
                organizations = self._create_organizations(5)
                
                # Create users
                users = self._create_users(num_users, organizations)
                
                # Create questionnaires
                questionnaires = self._create_questionnaires(num_questionnaires, admin_user, organizations)
                
                # Create responses with time distribution
                responses = self._create_responses(num_responses, questionnaires, users, days_range)
                
                self.stdout.write(self.style.SUCCESS(f'Successfully generated dashboard data:'))
                self.stdout.write(f'- {len(users)} users')
                self.stdout.write(f'- {len(organizations)} organizations')
                self.stdout.write(f'- {len(questionnaires)} questionnaires')
                self.stdout.write(f'- {len(responses)} responses')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating data: {str(e)}'))

    def _ensure_admin_exists(self):
        """Ensure admin user exists"""
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS('Created admin user'))
            return admin
        return User.objects.get(username='admin')

    def _create_organizations(self, count):
        """Create sample organizations"""
        organizations = []
        org_names = [
            'Mental Health Clinic', 'Wellness Center', 'Psychology Institute',
            'Behavioral Health Services', 'Community Mental Health', 'University Counseling',
            'Corporate Wellness Program', 'School District Assessment', 'Research Foundation',
            'Healthcare Network'
        ]
        
        existing_count = Organization.objects.count()
        if existing_count >= count:
            self.stdout.write(f'Using {count} existing organizations')
            return list(Organization.objects.all()[:count])
        
        for i in range(count):
            if i < len(org_names):
                name = org_names[i]
            else:
                name = f'Organization {i+1}'
                
            org, created = Organization.objects.get_or_create(
                name=name,
                defaults={
                    'description': f'Description for {name}',
                    'website': f'https://www.{name.lower().replace(" ", "")}.com',
                    'email': f'contact@{name.lower().replace(" ", "")}.com',
                    'phone': f'555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                    'address': f'{random.randint(100, 999)} Main St, City, State {random.randint(10000, 99999)}',
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(f'Created organization: {name}')
            
            organizations.append(org)
            
        return organizations

    def _create_users(self, count, organizations):
        """Create sample users"""
        users = []
        first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth', 
                      'David', 'Susan', 'Richard', 'Jessica', 'Joseph', 'Sarah', 'Thomas', 'Karen', 'Charles', 'Nancy']
        last_names = ['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore', 'Taylor',
                     'Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin', 'Thompson', 'Garcia', 'Martinez', 'Robinson']
        
        existing_count = User.objects.count()
        if existing_count >= count + 1:  # +1 for admin
            self.stdout.write(f'Using {count} existing users')
            return list(User.objects.all()[:count])
        
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f'{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}'
            email = f'{username}@example.com'
            
            if User.objects.filter(username=username).exists():
                username = f'{username}{random.randint(1000, 9999)}'
                email = f'{username}@example.com'
                
            if User.objects.filter(email=email).exists():
                continue
                
            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                first_name=first_name,
                last_name=last_name,
                is_staff=random.random() < 0.1,  # 10% chance of being staff
            )
            
            # Assign to organization
            if organizations and random.random() < 0.8:  # 80% chance of being in an organization
                org = random.choice(organizations)
                org.add_member(user)
                
            users.append(user)
            
        self.stdout.write(f'Created {len(users)} users')
        return users

    def _create_questionnaires(self, count, admin_user, organizations):
        """Create sample questionnaires"""
        questionnaires = []
        
        # Questionnaire templates
        templates = [
            {
                'title': 'Depression Assessment (PHQ-9)',
                'description': 'The Patient Health Questionnaire (PHQ-9) is a self-administered depression scale.',
                'category': 'depression',
                'questions': [
                    {'text': 'Little interest or pleasure in doing things', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                    {'text': 'Feeling down, depressed, or hopeless', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                    {'text': 'Trouble falling or staying asleep, or sleeping too much', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                    {'text': 'Feeling tired or having little energy', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                    {'text': 'Poor appetite or overeating', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                    {'text': 'Feeling bad about yourself', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                    {'text': 'Trouble concentrating on things', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                    {'text': 'Moving or speaking so slowly that other people could have noticed', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                    {'text': 'Thoughts that you would be better off dead or of hurting yourself', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                ]
            },
            {
                'title': 'Anxiety Screening (GAD-7)',
                'description': 'The Generalized Anxiety Disorder scale (GAD-7) is a self-reported questionnaire for screening and measuring anxiety.',
                'category': 'anxiety',
                'questions': [
                    {'text': 'Feeling nervous, anxious, or on edge', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                    {'text': 'Not being able to stop or control worrying', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                    {'text': 'Worrying too much about different things', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                    {'text': 'Trouble relaxing', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                    {'text': 'Being so restless that it is hard to sit still', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                    {'text': 'Becoming easily annoyed or irritable', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                    {'text': 'Feeling afraid, as if something awful might happen', 'type': 'scale', 'options': {'min': 0, 'max': 3, 'labels': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']}},
                ]
            },
            {
                'title': 'Stress Assessment (PSS)',
                'description': 'The Perceived Stress Scale (PSS) is a psychological instrument for measuring the perception of stress.',
                'category': 'stress',
                'questions': [
                    {'text': 'Been upset because of something that happened unexpectedly?', 'type': 'scale', 'options': {'min': 0, 'max': 4, 'labels': ['Never', 'Almost Never', 'Sometimes', 'Fairly Often', 'Very Often']}},
                    {'text': 'Felt that you were unable to control the important things in your life?', 'type': 'scale', 'options': {'min': 0, 'max': 4, 'labels': ['Never', 'Almost Never', 'Sometimes', 'Fairly Often', 'Very Often']}},
                    {'text': 'Felt nervous and stressed?', 'type': 'scale', 'options': {'min': 0, 'max': 4, 'labels': ['Never', 'Almost Never', 'Sometimes', 'Fairly Often', 'Very Often']}},
                    {'text': 'Felt confident about your ability to handle your personal problems?', 'type': 'scale', 'options': {'min': 0, 'max': 4, 'labels': ['Never', 'Almost Never', 'Sometimes', 'Fairly Often', 'Very Often']}},
                    {'text': 'Felt that things were going your way?', 'type': 'scale', 'options': {'min': 0, 'max': 4, 'labels': ['Never', 'Almost Never', 'Sometimes', 'Fairly Often', 'Very Often']}},
                    {'text': 'Found that you could not cope with all the things that you had to do?', 'type': 'scale', 'options': {'min': 0, 'max': 4, 'labels': ['Never', 'Almost Never', 'Sometimes', 'Fairly Often', 'Very Often']}},
                    {'text': 'Been able to control irritations in your life?', 'type': 'scale', 'options': {'min': 0, 'max': 4, 'labels': ['Never', 'Almost Never', 'Sometimes', 'Fairly Often', 'Very Often']}},
                    {'text': 'Felt that you were on top of things?', 'type': 'scale', 'options': {'min': 0, 'max': 4, 'labels': ['Never', 'Almost Never', 'Sometimes', 'Fairly Often', 'Very Often']}},
                    {'text': 'Been angered because of things that happened that were outside of your control?', 'type': 'scale', 'options': {'min': 0, 'max': 4, 'labels': ['Never', 'Almost Never', 'Sometimes', 'Fairly Often', 'Very Often']}},
                    {'text': 'Felt difficulties were piling up so high that you could not overcome them?', 'type': 'scale', 'options': {'min': 0, 'max': 4, 'labels': ['Never', 'Almost Never', 'Sometimes', 'Fairly Often', 'Very Often']}},
                ]
            },
            {
                'title': 'Well-being Assessment',
                'description': 'A general assessment of mental well-being and life satisfaction.',
                'category': 'general',
                'questions': [
                    {'text': 'How would you rate your overall mental health?', 'type': 'scale', 'options': {'min': 1, 'max': 5, 'labels': ['Poor', 'Fair', 'Good', 'Very Good', 'Excellent']}},
                    {'text': 'How satisfied are you with your life?', 'type': 'scale', 'options': {'min': 1, 'max': 5, 'labels': ['Very Dissatisfied', 'Dissatisfied', 'Neutral', 'Satisfied', 'Very Satisfied']}},
                    {'text': 'How often do you feel happy?', 'type': 'scale', 'options': {'min': 1, 'max': 5, 'labels': ['Never', 'Rarely', 'Sometimes', 'Often', 'Always']}},
                    {'text': 'How would you rate your energy levels?', 'type': 'scale', 'options': {'min': 1, 'max': 5, 'labels': ['Very Low', 'Low', 'Moderate', 'High', 'Very High']}},
                    {'text': 'How would you rate your stress levels?', 'type': 'scale', 'options': {'min': 1, 'max': 5, 'labels': ['Very Low', 'Low', 'Moderate', 'High', 'Very High']}},
                ]
            },
        ]
        
        existing_count = Questionnaire.objects.count()
        if existing_count >= count:
            self.stdout.write(f'Using {count} existing questionnaires')
            return list(Questionnaire.objects.all()[:count])
        
        # Create template questionnaires first
        for template in templates:
            if not Questionnaire.objects.filter(title=template['title']).exists():
                questionnaire = Questionnaire.objects.create(
                    title=template['title'],
                    description=template['description'],
                    category=template['category'],
                    status='active',
                    is_active=True,
                    is_public=True,
                    is_template=True,
                    created_by=admin_user,
                    organization=random.choice(organizations) if organizations else None
                )
                
                # Create questions
                for i, q_data in enumerate(template['questions']):
                    question = Question.objects.create(
                        survey=questionnaire,
                        text=q_data['text'],
                        question_type=q_data['type'],
                        required=True,
                        order=i+1,
                        options=q_data.get('options', {})
                    )
                
                questionnaires.append(questionnaire)
                self.stdout.write(f'Created template questionnaire: {template["title"]}')
        
        # Create additional questionnaires
        categories = ['anxiety', 'depression', 'stress', 'general', 'mental_health', 'physical_health']
        status_choices = ['draft', 'active', 'archived']
        status_weights = [0.2, 0.7, 0.1]  # 20% draft, 70% active, 10% archived
        
        additional_needed = count - len(questionnaires)
        for i in range(additional_needed):
            title = f'Questionnaire {i+1}'
            category = random.choice(categories)
            status = random.choices(status_choices, weights=status_weights)[0]
            
            questionnaire = Questionnaire.objects.create(
                title=title,
                description=f'Description for {title}',
                category=category,
                status=status,
                is_active=status == 'active',
                is_public=random.choice([True, False]),
                is_template=False,
                created_by=admin_user,
                organization=random.choice(organizations) if organizations else None
            )
            
            # Create 5-10 questions
            num_questions = random.randint(5, 10)
            for j in range(num_questions):
                question_type = random.choice(['text', 'textarea', 'number', 'single_choice', 'multiple_choice', 'scale'])
                options = {}
                
                if question_type == 'scale':
                    options = {
                        'min': 1,
                        'max': 5,
                        'labels': ['Very Low', 'Low', 'Moderate', 'High', 'Very High']
                    }
                elif question_type in ['single_choice', 'multiple_choice']:
                    options = {
                        'choices': ['Option 1', 'Option 2', 'Option 3', 'Option 4', 'Option 5']
                    }
                
                question = Question.objects.create(
                    survey=questionnaire,
                    text=f'Question {j+1} for {title}',
                    question_type=question_type,
                    required=True,
                    order=j+1,
                    options=options
                )
            
            questionnaires.append(questionnaire)
            
        self.stdout.write(f'Created {len(questionnaires)} questionnaires')
        return questionnaires

    def _create_responses(self, count, questionnaires, users, days_range):
        """Create sample responses with realistic time distribution"""
        responses = []
        
        # Only use active questionnaires
        active_questionnaires = [q for q in questionnaires if q.status == 'active']
        if not active_questionnaires:
            self.stdout.write(self.style.WARNING('No active questionnaires found'))
            return responses
            
        # Create responses with time distribution
        now = timezone.now()
        start_date = now - timedelta(days=days_range)
        
        # Create a realistic time distribution (more recent dates have more responses)
        dates = []
        for i in range(days_range):
            day = start_date + timedelta(days=i)
            # Weight more recent days higher
            weight = 1 + (i / days_range) * 3  # Weight increases from 1 to 4 as we get closer to today
            num_on_this_day = max(1, int(count * (weight / (days_range * 2.5))))
            dates.extend([day] * num_on_this_day)
        
        # Shuffle and trim to desired count
        random.shuffle(dates)
        dates = dates[:count]
        
        # Create responses
        for i, date in enumerate(dates):
            # Add random hours/minutes to distribute throughout the day
            response_time = date + timedelta(
                hours=random.randint(8, 22),  # Between 8 AM and 10 PM
                minutes=random.randint(0, 59)
            )
            
            questionnaire = random.choice(active_questionnaires)
            user = random.choice(users) if users else None
            
            # Create response
            response = Response.objects.create(
                survey=questionnaire,
                respondent_name=f"{user.first_name} {user.last_name}" if user else f"Anonymous User {i+1}",
                respondent_email=user.email if user else f"anonymous{i+1}@example.com",
                status='completed',
                completion_time=random.randint(120, 900),  # 2-15 minutes in seconds
                created_at=response_time,
                updated_at=response_time,
                ip_address=f"192.168.1.{random.randint(1, 255)}",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                metadata={
                    'device': random.choice(['desktop', 'mobile', 'tablet']),
                    'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge']),
                    'os': random.choice(['Windows', 'MacOS', 'iOS', 'Android']),
                }
            )
            
            # Create answers for each question
            questions = Question.objects.filter(survey=questionnaire)
            for question in questions:
                answer_value = None
                
                if question.question_type == 'scale':
                    options = question.options or {}
                    min_val = options.get('min', 1)
                    max_val = options.get('max', 5)
                    answer_value = random.randint(min_val, max_val)
                elif question.question_type in ['single_choice', 'multiple_choice']:
                    options = question.options or {}
                    choices = options.get('choices', [])
                    if choices:
                        if question.question_type == 'single_choice':
                            answer_value = random.choice(choices)
                        else:
                            # Select 1-3 choices
                            num_selections = random.randint(1, min(3, len(choices)))
                            answer_value = random.sample(choices, num_selections)
                elif question.question_type == 'text':
                    answer_value = f"Text answer for question {question.id}"
                elif question.question_type == 'textarea':
                    answer_value = f"Longer text answer for question {question.id}. This is a more detailed response."
                elif question.question_type == 'number':
                    answer_value = random.randint(1, 100)
                
                if answer_value is not None:
                    Answer.objects.create(
                        response=response,
                        question=question,
                        value=json.dumps(answer_value) if isinstance(answer_value, (list, dict)) else str(answer_value)
                    )
            
            responses.append(response)
            
            # Log progress
            if (i+1) % 100 == 0:
                self.stdout.write(f'Created {i+1} responses...')
        
        self.stdout.write(f'Created {len(responses)} responses')
        return responses
