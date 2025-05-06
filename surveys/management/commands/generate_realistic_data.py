import random
import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from surveys.models import Questionnaire, Question, Option
from feedback.models import Response, Answer
from groups.models import Organization

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate realistic sample data for the application'

    def add_arguments(self, parser):
        parser.add_argument('--questionnaires', type=int, default=10, help='Number of questionnaires to create')
        parser.add_argument('--responses', type=int, default=100, help='Number of responses to create')
        parser.add_argument('--organizations', type=int, default=5, help='Number of organizations to create')
        parser.add_argument('--users', type=int, default=20, help='Number of users to create')

    def handle(self, *args, **options):
        num_questionnaires = options['questionnaires']
        num_responses = options['responses']
        num_organizations = options['organizations']
        num_users = options['users']

        self.stdout.write(self.style.SUCCESS(f'Generating {num_organizations} organizations...'))
        organizations = self.create_organizations(num_organizations)

        self.stdout.write(self.style.SUCCESS(f'Generating {num_users} users...'))
        users = self.create_users(num_users, organizations)

        self.stdout.write(self.style.SUCCESS(f'Generating {num_questionnaires} questionnaires...'))
        questionnaires = self.create_questionnaires(num_questionnaires, users, organizations)

        self.stdout.write(self.style.SUCCESS(f'Generating {num_responses} responses...'))
        self.create_responses(num_responses, questionnaires)

        self.stdout.write(self.style.SUCCESS('Sample data generation complete!'))

    def create_organizations(self, count):
        organizations = []
        
        org_types = ['Healthcare', 'Education', 'Corporate', 'Non-profit', 'Government']
        org_names = [
            'Harmony Health', 'Wellness Center', 'MindCare Clinic', 'Serenity Medical', 'Healing Horizons',
            'Bright Minds Academy', 'Knowledge Quest', 'Learning Excellence', 'Wisdom Institute', 'Scholars Haven',
            'Innovative Solutions', 'Global Enterprises', 'Strategic Partners', 'Vision Corp', 'Future Tech',
            'Community Outreach', 'Hope Foundation', 'Better Tomorrow', 'Helping Hands', 'Care Coalition',
            'Public Services', 'Civic Department', 'Municipal Authority', 'Regional Office', 'National Agency'
        ]
        
        for i in range(count):
            org_type = random.choice(org_types)
            org_name = f"{random.choice(org_names)} {org_type}"
            
            organization = Organization.objects.create(
                name=org_name,
                description=f"A {org_type.lower()} organization focused on improving mental health and wellbeing.",
                website=f"https://www.{org_name.lower().replace(' ', '')}.com",
                email=f"contact@{org_name.lower().replace(' ', '')}.com",
                phone=f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                address=f"{random.randint(100, 9999)} Main St, Suite {random.randint(100, 999)}, City, State, ZIP"
            )
            
            organizations.append(organization)
            self.stdout.write(f"Created organization: {organization.name}")
        
        return organizations

    def create_users(self, count, organizations):
        users = []
        
        first_names = [
            'James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles',
            'Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica', 'Sarah', 'Karen'
        ]
        
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore', 'Taylor',
            'Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin', 'Thompson', 'Garcia', 'Martinez', 'Robinson'
        ]
        
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com"
            
            user = User.objects.create_user(
                email=email,
                password='password123',
                first_name=first_name,
                last_name=last_name,
                is_staff=random.random() < 0.2  # 20% chance of being staff
            )
            
            # Assign user to random organization
            if organizations:
                org = random.choice(organizations)
                org.add_member(user)
            
            users.append(user)
            self.stdout.write(f"Created user: {user.email}")
        
        return users

    def create_questionnaires(self, count, users, organizations):
        questionnaires = []
        
        questionnaire_types = [
            {
                'type': 'mental_health',
                'titles': [
                    'Depression Screening', 'Anxiety Assessment', 'Stress Level Evaluation',
                    'Mental Wellbeing Check', 'Mood Disorder Screening', 'PTSD Assessment',
                    'Burnout Evaluation', 'Emotional Health Check'
                ],
                'descriptions': [
                    'Assess symptoms of depression and determine severity.',
                    'Evaluate anxiety levels and identify potential anxiety disorders.',
                    'Measure current stress levels and identify stressors.',
                    'Comprehensive assessment of overall mental wellbeing.',
                    'Screen for mood disorders including depression and bipolar disorder.',
                    'Assess symptoms related to post-traumatic stress disorder.',
                    'Evaluate professional burnout and work-related stress.',
                    'Check emotional health status and identify areas for improvement.'
                ]
            },
            {
                'type': 'physical_health',
                'titles': [
                    'General Health Assessment', 'Physical Activity Evaluation', 'Sleep Quality Check',
                    'Nutrition Habits Survey', 'Pain Assessment', 'Chronic Condition Management'
                ],
                'descriptions': [
                    'Comprehensive assessment of overall physical health status.',
                    'Evaluate current physical activity levels and exercise habits.',
                    'Assess sleep quality, duration, and sleep-related issues.',
                    'Evaluate nutrition habits and dietary patterns.',
                    'Assess pain levels, locations, and impact on daily activities.',
                    'Evaluate management of existing chronic health conditions.'
                ]
            },
            {
                'type': 'customer_satisfaction',
                'titles': [
                    'Service Satisfaction Survey', 'Product Feedback Form', 'Customer Experience Assessment',
                    'Client Satisfaction Evaluation', 'Service Quality Feedback'
                ],
                'descriptions': [
                    'Gather feedback on service satisfaction and identify areas for improvement.',
                    'Collect feedback on product quality, features, and usability.',
                    'Assess overall customer experience and satisfaction levels.',
                    'Evaluate client satisfaction with services provided.',
                    'Gather feedback on service quality and staff performance.'
                ]
            },
            {
                'type': 'employee_feedback',
                'titles': [
                    'Employee Satisfaction Survey', 'Workplace Environment Assessment', 'Team Collaboration Evaluation',
                    'Management Feedback Form', 'Work-Life Balance Survey'
                ],
                'descriptions': [
                    'Assess employee satisfaction and identify areas for improvement.',
                    'Evaluate the workplace environment and company culture.',
                    'Assess team collaboration and communication effectiveness.',
                    'Gather feedback on management performance and leadership.',
                    'Evaluate work-life balance and identify potential issues.'
                ]
            }
        ]
        
        question_templates = {
            'mental_health': [
                {
                    'text': 'How often have you felt down, depressed, or hopeless in the past two weeks?',
                    'type': 'multiple_choice',
                    'options': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
                    'scores': [0, 1, 2, 3]
                },
                {
                    'text': 'How often have you had little interest or pleasure in doing things you usually enjoy?',
                    'type': 'multiple_choice',
                    'options': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
                    'scores': [0, 1, 2, 3]
                },
                {
                    'text': 'How would you rate your overall stress level in the past month?',
                    'type': 'multiple_choice',
                    'options': ['Very low', 'Low', 'Moderate', 'High', 'Very high'],
                    'scores': [0, 1, 2, 3, 4]
                },
                {
                    'text': 'How often have you felt nervous, anxious, or on edge?',
                    'type': 'multiple_choice',
                    'options': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
                    'scores': [0, 1, 2, 3]
                },
                {
                    'text': 'How often have you had trouble falling or staying asleep?',
                    'type': 'multiple_choice',
                    'options': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
                    'scores': [0, 1, 2, 3]
                },
                {
                    'text': 'How often have you felt tired or had little energy?',
                    'type': 'multiple_choice',
                    'options': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
                    'scores': [0, 1, 2, 3]
                },
                {
                    'text': 'How often have you had poor appetite or overeaten?',
                    'type': 'multiple_choice',
                    'options': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
                    'scores': [0, 1, 2, 3]
                },
                {
                    'text': 'How often have you had trouble concentrating?',
                    'type': 'multiple_choice',
                    'options': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
                    'scores': [0, 1, 2, 3]
                },
                {
                    'text': 'How often have you had thoughts that you would be better off dead or of hurting yourself?',
                    'type': 'multiple_choice',
                    'options': ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
                    'scores': [0, 1, 2, 3]
                },
                {
                    'text': 'How difficult have these problems made it for you to do your work, take care of things at home, or get along with other people?',
                    'type': 'multiple_choice',
                    'options': ['Not difficult at all', 'Somewhat difficult', 'Very difficult', 'Extremely difficult'],
                    'scores': [0, 1, 2, 3]
                }
            ],
            'physical_health': [
                {
                    'text': 'How would you rate your overall physical health?',
                    'type': 'multiple_choice',
                    'options': ['Excellent', 'Very good', 'Good', 'Fair', 'Poor'],
                    'scores': [4, 3, 2, 1, 0]
                },
                {
                    'text': 'How many days per week do you engage in moderate to vigorous physical activity?',
                    'type': 'multiple_choice',
                    'options': ['0 days', '1-2 days', '3-4 days', '5-7 days'],
                    'scores': [0, 1, 2, 3]
                },
                {
                    'text': 'How many hours of sleep do you typically get per night?',
                    'type': 'multiple_choice',
                    'options': ['Less than 5 hours', '5-6 hours', '7-8 hours', 'More than 8 hours'],
                    'scores': [0, 1, 3, 2]
                },
                {
                    'text': 'How often do you eat fruits and vegetables?',
                    'type': 'multiple_choice',
                    'options': ['Rarely or never', '1-2 times per week', '3-4 times per week', 'Daily'],
                    'scores': [0, 1, 2, 3]
                },
                {
                    'text': 'Do you currently smoke or use tobacco products?',
                    'type': 'multiple_choice',
                    'options': ['Yes, regularly', 'Yes, occasionally', 'No, but I used to', 'No, never'],
                    'scores': [0, 1, 2, 3]
                },
                {
                    'text': 'How often do you consume alcoholic beverages?',
                    'type': 'multiple_choice',
                    'options': ['Daily', 'Several times per week', 'Once per week', 'Rarely', 'Never'],
                    'scores': [0, 1, 2, 3, 3]
                },
                {
                    'text': 'How would you rate your energy level on most days?',
                    'type': 'multiple_choice',
                    'options': ['Very low', 'Low', 'Moderate', 'High', 'Very high'],
                    'scores': [0, 1, 2, 3, 4]
                },
                {
                    'text': 'Do you have any chronic health conditions?',
                    'type': 'multiple_choice',
                    'options': ['Yes, multiple', 'Yes, one', 'No, but I have risk factors', 'No'],
                    'scores': [0, 1, 2, 3]
                }
            ],
            'customer_satisfaction': [
                {
                    'text': 'How satisfied are you with our service/product?',
                    'type': 'multiple_choice',
                    'options': ['Very dissatisfied', 'Dissatisfied', 'Neutral', 'Satisfied', 'Very satisfied'],
                    'scores': [0, 1, 2, 3, 4]
                },
                {
                    'text': 'How likely are you to recommend our service/product to others?',
                    'type': 'multiple_choice',
                    'options': ['Not at all likely', 'Slightly likely', 'Moderately likely', 'Very likely', 'Extremely likely'],
                    'scores': [0, 1, 2, 3, 4]
                },
                {
                    'text': 'How would you rate the quality of our service/product?',
                    'type': 'multiple_choice',
                    'options': ['Poor', 'Fair', 'Good', 'Very good', 'Excellent'],
                    'scores': [0, 1, 2, 3, 4]
                },
                {
                    'text': 'How would you rate the value for money of our service/product?',
                    'type': 'multiple_choice',
                    'options': ['Poor', 'Fair', 'Good', 'Very good', 'Excellent'],
                    'scores': [0, 1, 2, 3, 4]
                },
                {
                    'text': 'How satisfied are you with our customer service?',
                    'type': 'multiple_choice',
                    'options': ['Very dissatisfied', 'Dissatisfied', 'Neutral', 'Satisfied', 'Very satisfied'],
                    'scores': [0, 1, 2, 3, 4]
                },
                {
                    'text': 'How easy was it to use our service/product?',
                    'type': 'multiple_choice',
                    'options': ['Very difficult', 'Difficult', 'Neutral', 'Easy', 'Very easy'],
                    'scores': [0, 1, 2, 3, 4]
                }
            ],
            'employee_feedback': [
                {
                    'text': 'How satisfied are you with your job?',
                    'type': 'multiple_choice',
                    'options': ['Very dissatisfied', 'Dissatisfied', 'Neutral', 'Satisfied', 'Very satisfied'],
                    'scores': [0, 1, 2, 3, 4]
                },
                {
                    'text': 'How would you rate the work environment?',
                    'type': 'multiple_choice',
                    'options': ['Poor', 'Fair', 'Good', 'Very good', 'Excellent'],
                    'scores': [0, 1, 2, 3, 4]
                },
                {
                    'text': 'How satisfied are you with the recognition you receive for your work?',
                    'type': 'multiple_choice',
                    'options': ['Very dissatisfied', 'Dissatisfied', 'Neutral', 'Satisfied', 'Very satisfied'],
                    'scores': [0, 1, 2, 3, 4]
                },
                {
                    'text': 'How would you rate the communication within your team?',
                    'type': 'multiple_choice',
                    'options': ['Poor', 'Fair', 'Good', 'Very good', 'Excellent'],
                    'scores': [0, 1, 2, 3, 4]
                },
                {
                    'text': 'How satisfied are you with your work-life balance?',
                    'type': 'multiple_choice',
                    'options': ['Very dissatisfied', 'Dissatisfied', 'Neutral', 'Satisfied', 'Very satisfied'],
                    'scores': [0, 1, 2, 3, 4]
                },
                {
                    'text': 'How would you rate your relationship with your manager?',
                    'type': 'multiple_choice',
                    'options': ['Poor', 'Fair', 'Good', 'Very good', 'Excellent'],
                    'scores': [0, 1, 2, 3, 4]
                },
                {
                    'text': 'How satisfied are you with opportunities for professional growth?',
                    'type': 'multiple_choice',
                    'options': ['Very dissatisfied', 'Dissatisfied', 'Neutral', 'Satisfied', 'Very satisfied'],
                    'scores': [0, 1, 2, 3, 4]
                }
            ]
        }
        
        for i in range(count):
            # Select random questionnaire type
            questionnaire_type = random.choice(questionnaire_types)
            q_type = questionnaire_type['type']
            
            # Select random title and description
            title_index = random.randint(0, len(questionnaire_type['titles']) - 1)
            title = questionnaire_type['titles'][title_index]
            description = questionnaire_type['descriptions'][title_index]
            
            # Select random creator and organization
            creator = random.choice(users)
            organization = random.choice(organizations) if organizations else None
            
            # Create questionnaire
            questionnaire = Questionnaire.objects.create(
                title=title,
                description=description,
                created_by=creator,
                organization=organization,
                status=random.choice(['draft', 'active', 'archived']),
                access_code=str(uuid.uuid4())[:8],
                type=q_type
            )
            
            # Add questions
            question_templates_for_type = question_templates.get(q_type, question_templates['mental_health'])
            selected_questions = random.sample(question_templates_for_type, min(len(question_templates_for_type), random.randint(5, 10)))
            
            for j, question_template in enumerate(selected_questions):
                question = Question.objects.create(
                    questionnaire=questionnaire,
                    text=question_template['text'],
                    type=question_template['type'],
                    order=j + 1,
                    required=random.random() < 0.8  # 80% chance of being required
                )
                
                # Add options
                for k, option_text in enumerate(question_template['options']):
                    Option.objects.create(
                        question=question,
                        text=option_text,
                        order=k + 1,
                        score=question_template['scores'][k] if 'scores' in question_template else 0
                    )
            
            questionnaires.append(questionnaire)
            self.stdout.write(f"Created questionnaire: {questionnaire.title} ({q_type})")
        
        return questionnaires

    def create_responses(self, count, questionnaires):
        if not questionnaires:
            self.stdout.write(self.style.WARNING('No questionnaires available to create responses for.'))
            return
        
        genders = ['male', 'female', 'non-binary', 'prefer_not_to_say']
        devices = ['desktop', 'mobile', 'tablet']
        
        for i in range(count):
            # Select random questionnaire
            questionnaire = random.choice(questionnaires)
            
            # Generate random patient data
            patient_age = random.randint(18, 80)
            patient_gender = random.choice(genders)
            patient_email = f"patient{random.randint(1000, 9999)}@example.com"
            
            # Generate random completion time (between 2 and 15 minutes)
            completion_time = random.randint(120, 900)
            
            # Generate random created_at time (within the last 30 days)
            created_at = timezone.now() - timedelta(days=random.randint(0, 30), 
                                                   hours=random.randint(0, 23), 
                                                   minutes=random.randint(0, 59))
            
            # Create response
            response = Response.objects.create(
                survey=questionnaire,
                patient_age=patient_age,
                patient_gender=patient_gender,
                patient_email=patient_email,
                completion_time=completion_time,
                status='completed',
                created_at=created_at,
                metadata={
                    'device': random.choice(devices),
                    'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge']),
                    'os': random.choice(['Windows', 'MacOS', 'iOS', 'Android', 'Linux']),
                    'ip_address': f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
                }
            )
            
            # Create answers for each question
            total_score = 0
            questions = Question.objects.filter(questionnaire=questionnaire)
            
            for question in questions:
                options = Option.objects.filter(question=question)
                if options.exists():
                    # Select random option
                    selected_option = random.choice(options)
                    
                    # Create answer
                    Answer.objects.create(
                        response=response,
                        question=question,
                        selected_option=selected_option,
                        text_answer=''
                    )
                    
                    # Add to total score
                    total_score += selected_option.score
            
            # Update response score
            response.score = total_score
            
            # Determine risk level based on score and questionnaire type
            max_possible_score = sum([o.score for q in questions for o in Option.objects.filter(question=q).order_by('-score')[:1]])
            score_percentage = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0
            
            if questionnaire.type == 'mental_health':
                # For mental health, higher score means higher risk
                if score_percentage >= 75:
                    risk_level = 'critical'
                elif score_percentage >= 50:
                    risk_level = 'high'
                elif score_percentage >= 25:
                    risk_level = 'medium'
                else:
                    risk_level = 'low'
            else:
                # For other types, lower score means higher risk
                if score_percentage <= 25:
                    risk_level = 'critical'
                elif score_percentage <= 50:
                    risk_level = 'high'
                elif score_percentage <= 75:
                    risk_level = 'medium'
                else:
                    risk_level = 'low'
            
            response.risk_level = risk_level
            response.save()
            
            self.stdout.write(f"Created response for {questionnaire.title}: Score={total_score}, Risk={risk_level}")
