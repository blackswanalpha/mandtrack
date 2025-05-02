"""
Script to generate realistic data for the admin dashboard.
This script creates sample data for questionnaires, responses, users, and organizations
with realistic distributions and trends for visualization purposes.
"""
import os
import django
import sys
import random
from datetime import datetime, timedelta
import uuid
import json
import numpy as np

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Import models after Django setup
from django.contrib.auth import get_user_model
from django.utils import timezone
from surveys.models import Questionnaire, Question, QuestionChoice, QRCode, ScoringConfig
from feedback.models import Response, Answer, AIAnalysis
from groups.models import Organization, OrganizationMember
from analytics.models import AIModel, AIAnalysisResult, AIInsight

User = get_user_model()

def create_organizations(num_organizations=5):
    """Create sample organizations with realistic data"""
    print(f"Creating {num_organizations} sample organizations...")

    # Get or create admin user
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

    org_types = ['Hospital', 'Clinic', 'Research Center', 'University', 'Corporate']
    org_names = [
        'Mindful Health Center', 'Serenity Wellness Clinic', 'Harmony Mental Health',
        'Tranquil Mind Institute', 'Balanced Life Center', 'Clarity Psychological Services',
        'Resilience Mental Health', 'Wellness Horizon Center', 'Mindscape Therapy',
        'Peaceful Mind Clinic'
    ]

    organizations = []
    for i in range(num_organizations):
        name = random.choice(org_names) if i < len(org_names) else f"Organization {i+1}"
        org_names.remove(name) if name in org_names else None

        org = Organization.objects.create(
            name=name,
            description=f"A leading provider of mental health services specializing in {random.choice(['anxiety', 'depression', 'stress management', 'general wellness'])}",
            type=random.choice(org_types),
            website=f"https://www.{name.lower().replace(' ', '')}.com",
            email=f"info@{name.lower().replace(' ', '')}.com",
            phone=f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            address=f"{random.randint(1, 999)} {random.choice(['Main St', 'Broadway', 'Park Ave', 'Oak Lane'])}, {random.choice(['New York', 'Los Angeles', 'Chicago', 'Boston', 'San Francisco'])}",
            created_by=admin_user
        )
        organizations.append(org)
        print(f"Created organization: {org.name}")

    return organizations

def create_users(num_users=50, organizations=None):
    """Create sample users with realistic data"""
    print(f"Creating {num_users} sample users...")

    # Ensure admin exists
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print(f"Created admin user: {admin_user.email}")

    # Create regular users with realistic data
    first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth',
                  'David', 'Susan', 'Richard', 'Jessica', 'Joseph', 'Sarah', 'Thomas', 'Karen', 'Charles', 'Nancy']
    last_names = ['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore', 'Taylor',
                 'Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin', 'Thompson', 'Garcia', 'Martinez', 'Robinson']

    roles = ['user'] * 8 + ['staff'] * 2  # 80% regular users, 20% staff

    users = []
    for i in range(num_users):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}"
        email = f"{username}@example.com"

        if User.objects.filter(username=username).exists():
            username = f"{username}{random.randint(1000, 9999)}"
            email = f"{username}@example.com"

        role = random.choice(roles)
        is_staff = role == 'staff'

        user = User.objects.create_user(
            username=username,
            email=email,
            password=f"password{i+1}",
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_staff=is_staff,
            email_verified=True,
            date_joined=timezone.now() - timedelta(days=random.randint(1, 365))
        )

        # Assign to organization if available
        if organizations and random.random() < 0.8:  # 80% of users belong to an organization
            org = random.choice(organizations)
            OrganizationMember.objects.create(
                organization=org,
                user=user,
                role=random.choice(['member', 'admin', 'viewer']),
                is_active=True
            )

        users.append(user)

    print(f"Created {len(users)} users")
    return users

def create_questionnaires(num_questionnaires=20, users=None, organizations=None):
    """Create sample questionnaires with realistic data"""
    print(f"Creating {num_questionnaires} sample questionnaires...")

    if not users:
        users = User.objects.filter(is_staff=True)
        if not users:
            print("No staff users found. Creating one...")
            users = [User.objects.create_user(
                username="staff_user",
                email="staff@example.com",
                password="staffpass",
                is_staff=True
            )]

    # Define realistic questionnaire data
    categories = [
        ('anxiety', 'Anxiety Assessment'),
        ('depression', 'Depression Screening'),
        ('stress', 'Stress Evaluation'),
        ('general', 'General Mental Health'),
        ('mental_health', 'Comprehensive Mental Health'),
        ('physical_health', 'Physical Health Assessment'),
        ('education', 'Educational Assessment'),
        ('customer_satisfaction', 'Customer Satisfaction'),
        ('employee_feedback', 'Employee Feedback'),
        ('clinical_assessment', 'Clinical Assessment')
    ]

    status_choices = ['active', 'draft', 'archived']
    status_weights = [0.7, 0.2, 0.1]  # 70% active, 20% draft, 10% archived

    questionnaires = []
    for i in range(num_questionnaires):
        category, title_base = random.choice(categories)
        title = f"{title_base} {i+1}"
        status = random.choices(status_choices, weights=status_weights)[0]
        created_by = random.choice(users)
        organization = random.choice(organizations) if organizations else None

        # Create with realistic creation dates (more recent ones are more likely to be active)
        days_ago = random.randint(1, 180)  # Up to 6 months old
        created_at = timezone.now() - timedelta(days=days_ago)

        questionnaire = Questionnaire.objects.create(
            title=title,
            description=f"A comprehensive assessment tool for {category.replace('_', ' ')}",
            instructions=f"Please answer all questions honestly. Your responses will help us provide better support.",
            category=category,
            status=status,
            is_active=status == 'active',
            is_public=random.choice([True, False]),
            is_template=False,
            is_adaptive=random.choice([True, False]),
            is_qr_enabled=True,
            allow_anonymous=True,
            requires_auth=False,
            version=1,
            estimated_time=random.randint(5, 30),
            language='en',
            tags=[category, 'assessment', 'mental health'],
            created_by=created_by,
            organization=organization,
            created_at=created_at
        )

        # Create questions for this questionnaire
        num_questions = random.randint(5, 15)
        for j in range(num_questions):
            question_type = random.choice(['text', 'textarea', 'number', 'single_choice', 'multiple_choice', 'scale'])

            question = Question.objects.create(
                survey=questionnaire,
                text=f"Question {j+1} for {questionnaire.title}",
                description=f"Additional information about question {j+1}",
                question_type=question_type,
                required=True,
                order=j+1
            )

            # Create choices for choice-based questions
            if question_type in ['single_choice', 'multiple_choice', 'scale']:
                num_choices = 5 if question_type == 'scale' else random.randint(3, 6)
                for k in range(num_choices):
                    score = k+1 if question_type == 'scale' else random.randint(0, 5)
                    QuestionChoice.objects.create(
                        question=question,
                        text=f"Choice {k+1}" if question_type != 'scale' else f"{k+1}",
                        order=k+1,
                        score=score
                    )

        # Create scoring config for the questionnaire
        ScoringConfig.objects.create(
            survey=questionnaire,
            name=f"Scoring for {questionnaire.title}",
            description=f"Default scoring configuration for {questionnaire.title}",
            scoring_method='sum',
            max_score=100,
            passing_score=70,
            is_active=True,
            is_default=True,
            rules=[
                {'min': 0, 'max': 25, 'label': 'Low Risk', 'color': '#4CAF50'},
                {'min': 26, 'max': 50, 'label': 'Moderate Risk', 'color': '#FFC107'},
                {'min': 51, 'max': 75, 'label': 'High Risk', 'color': '#FF9800'},
                {'min': 76, 'max': 100, 'label': 'Critical Risk', 'color': '#F44336'}
            ],
            created_by=created_by
        )

        questionnaires.append(questionnaire)
        print(f"Created questionnaire: {questionnaire.title} with {num_questions} questions")

    return questionnaires

def create_responses_with_trend(num_responses=500, questionnaires=None, users=None, days_range=90):
    """Create sample responses with realistic trends over time"""
    print(f"Creating {num_responses} sample responses with trends over {days_range} days...")

    if not questionnaires:
        questionnaires = Questionnaire.objects.filter(status='active')
        if not questionnaires:
            print("No active questionnaires found. Please create questionnaires first.")
            return []

    if not users:
        users = User.objects.all()
        if not users:
            print("No users found. Please create users first.")
            return []

    # Create responses with time distribution
    now = timezone.now()
    start_date = now - timedelta(days=days_range)

    # Create a realistic time distribution with trends
    # More responses in recent days, with weekly patterns (fewer on weekends)
    # Also create seasonal trends with some random variation

    dates = []

    # Base distribution - more recent dates have more responses
    for i in range(days_range):
        day = start_date + timedelta(days=i)
        day_of_week = day.weekday()  # 0-6 (Monday to Sunday)

        # Weight more recent days higher (linear increase)
        recency_weight = 0.5 + (i / days_range) * 1.5  # Weight increases from 0.5 to 2.0

        # Weekly pattern - fewer responses on weekends
        weekday_weight = 1.0 if day_of_week < 5 else 0.4  # 60% fewer on weekends

        # Monthly pattern - more responses at beginning of month
        day_of_month = day.day
        monthly_weight = 1.2 if day_of_month < 5 else 1.0

        # Combine weights
        combined_weight = recency_weight * weekday_weight * monthly_weight

        # Calculate number of responses for this day
        num_on_this_day = max(1, int(num_responses * (combined_weight / (days_range * 1.5))))

        # Add some randomness
        num_on_this_day = int(num_on_this_day * random.uniform(0.8, 1.2))

        # Add this day to the dates list multiple times based on weight
        dates.extend([day] * num_on_this_day)

    # Shuffle and trim to desired count
    random.shuffle(dates)
    dates = dates[:num_responses]

    # Sort dates to make processing easier
    dates.sort()

    # Create responses
    responses = []
    gender_choices = ['male', 'female', 'non-binary', 'prefer_not_to_say']
    gender_weights = [0.48, 0.48, 0.02, 0.02]  # Realistic gender distribution

    for i, date in enumerate(dates):
        # Add random hours/minutes to distribute throughout the day
        hour = random.randint(8, 22)  # Between 8 AM and 10 PM
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        response_time = date.replace(hour=hour, minute=minute, second=second)

        # Select questionnaire - weight active ones higher
        active_questionnaires = [q for q in questionnaires if q.status == 'active']
        if not active_questionnaires:
            active_questionnaires = questionnaires

        questionnaire = random.choice(active_questionnaires)

        # Determine if this is an anonymous response
        is_anonymous = random.random() < 0.3  # 30% anonymous

        user = None if is_anonymous else random.choice(users)

        # Create response with realistic data
        response = Response.objects.create(
            survey=questionnaire,
            user=user,
            patient_identifier=f"PAT{random.randint(10000, 99999)}" if not is_anonymous else None,
            patient_email=user.email if user else f"anonymous{i+1}@example.com",
            patient_age=random.randint(18, 80),
            patient_gender=random.choices(gender_choices, weights=gender_weights)[0],
            score=random.randint(0, 100),
            risk_level=random.choices(['low', 'medium', 'high', 'critical'], weights=[0.5, 0.3, 0.15, 0.05])[0],
            flagged_for_review=random.random() < 0.1,  # 10% flagged
            completion_time=random.randint(120, 900),  # 2-15 minutes in seconds
            ip_address=f"192.168.1.{random.randint(1, 255)}",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            status='completed',
            created_at=response_time,
            completed_at=response_time + timedelta(minutes=random.randint(5, 30)),
            updated_at=response_time,
            metadata={
                'device': random.choice(['desktop', 'mobile', 'tablet']),
                'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge']),
                'os': random.choice(['Windows', 'MacOS', 'iOS', 'Android']),
                'location': random.choice(['Home', 'Office', 'Clinic', 'Other']),
            }
        )

        # Create answers for this response
        questions = Question.objects.filter(survey=questionnaire)
        for question in questions:
            # For choice questions, select a random choice
            if question.question_type in ['single_choice', 'multiple_choice', 'scale']:
                choices = QuestionChoice.objects.filter(question=question)
                if choices.exists():
                    choice = random.choice(choices)

                    Answer.objects.create(
                        response=response,
                        question=question,
                        text_answer=choice.text,
                        numeric_value=choice.score,
                        selected_choice=choice,
                        score=choice.score,
                        created_at=response_time
                    )
            else:
                # For text/number questions, generate random answers
                if question.question_type == 'text':
                    answer_text = random.choice([
                        "Yes, frequently", "Sometimes", "Rarely", "No, never",
                        "I'm not sure", "This happens often", "Only when stressed"
                    ])
                elif question.question_type == 'textarea':
                    answer_text = random.choice([
                        "I've been feeling this way for several weeks now.",
                        "This only happens when I'm under significant stress.",
                        "I've noticed this pattern for a long time but it's gotten worse recently.",
                        "This is a new experience for me and I'm not sure how to handle it.",
                        "I've tried various coping mechanisms but nothing seems to help consistently."
                    ])
                elif question.question_type == 'number':
                    answer_text = str(random.randint(1, 10))
                else:
                    answer_text = "Sample answer"

                # For text/number questions, generate random answers
                if question.question_type == 'text':
                    Answer.objects.create(
                        response=response,
                        question=question,
                        text_answer=answer_text,
                        created_at=response_time
                    )
                elif question.question_type == 'textarea':
                    Answer.objects.create(
                        response=response,
                        question=question,
                        text_answer=answer_text,
                        created_at=response_time
                    )
                elif question.question_type == 'number':
                    numeric_value = random.randint(1, 5)
                    Answer.objects.create(
                        response=response,
                        question=question,
                        text_answer=answer_text,
                        numeric_value=numeric_value,
                        score=numeric_value,
                        created_at=response_time
                    )
                else:
                    Answer.objects.create(
                        response=response,
                        question=question,
                        text_answer=answer_text,
                        created_at=response_time
                    )

        # Create AI analysis for some responses
        if random.random() < 0.7:  # 70% of responses have AI analysis
            sentiment_scores = {
                'positive': random.uniform(0.1, 0.9),
                'negative': random.uniform(0.1, 0.9),
                'neutral': random.uniform(0.1, 0.9)
            }

            # Normalize sentiment scores to sum to 1
            total = sum(sentiment_scores.values())
            for key in sentiment_scores:
                sentiment_scores[key] /= total

            # Generate random keywords with frequencies
            keywords = [
                ('anxiety', random.randint(1, 10)),
                ('stress', random.randint(1, 10)),
                ('sleep', random.randint(1, 10)),
                ('mood', random.randint(1, 10)),
                ('energy', random.randint(1, 10)),
                ('concentration', random.randint(1, 10)),
                ('worry', random.randint(1, 10)),
                ('depression', random.randint(1, 10))
            ]

            # Create AI analysis
            AIAnalysis.objects.create(
                response=response,
                summary=f"Analysis of responses for {questionnaire.title}",
                detailed_analysis=f"The respondent shows signs of {random.choice(['mild', 'moderate', 'severe'])} {questionnaire.category}. " +
                                 f"Key indicators include {random.choice(['sleep disturbances', 'mood changes', 'anxiety symptoms', 'stress reactions'])}.",
                recommendations=f"Recommended actions: {random.choice(['Follow up with a healthcare provider', 'Continue monitoring symptoms', 'Consider therapy options', 'Practice self-care techniques'])}",
                insights={
                    'sentiment_analysis': sentiment_scores,
                    'keywords': dict(keywords),
                    'risk_factors': random.sample(['stress', 'family history', 'recent life changes', 'work pressure', 'relationship issues'], k=random.randint(1, 3)),
                    'protective_factors': random.sample(['social support', 'exercise', 'healthy diet', 'meditation', 'therapy'], k=random.randint(1, 3))
                },
                model_used='GPT-4',
                confidence_score=random.uniform(0.7, 0.99),
                created_at=response_time + timedelta(minutes=random.randint(1, 5))
            )

        responses.append(response)

        # Print progress
        if (i+1) % 50 == 0:
            print(f"Created {i+1} responses...")

    print(f"Created {len(responses)} responses with realistic trends")
    return responses

def create_ai_insights(questionnaires=None, num_insights=30):
    """Create sample AI insights for questionnaires"""
    print(f"Creating {num_insights} AI insights...")

    if not questionnaires:
        questionnaires = Questionnaire.objects.filter(status='active')
        if not questionnaires:
            print("No active questionnaires found. Please create questionnaires first.")
            return []

    insights = []
    insight_types = ['trend', 'anomaly', 'correlation', 'recommendation', 'summary']

    for i in range(num_insights):
        questionnaire = random.choice(questionnaires)
        insight_type = random.choice(insight_types)

        # Create with dates spread over the last 30 days
        days_ago = random.randint(0, 30)
        created_at = timezone.now() - timedelta(days=days_ago)

        if insight_type == 'trend':
            title = f"Trend detected in {questionnaire.title}"
            content = f"There has been a {random.choice(['significant increase', 'notable decrease', 'steady trend'])} " + \
                     f"in {random.choice(['risk scores', 'response rates', 'completion times'])} over the past {random.randint(7, 28)} days."
        elif insight_type == 'anomaly':
            title = f"Anomaly detected in {questionnaire.title}"
            content = f"An unusual pattern has been detected in responses to question {random.randint(1, 5)}. " + \
                     f"This may indicate {random.choice(['data collection issues', 'changing respondent demographics', 'seasonal factors'])}."
        elif insight_type == 'correlation':
            title = f"Correlation found in {questionnaire.title}"
            content = f"A strong correlation has been found between {random.choice(['age', 'gender', 'location'])} " + \
                     f"and {random.choice(['risk level', 'response patterns', 'completion time'])}."
        elif insight_type == 'recommendation':
            title = f"Recommendation for {questionnaire.title}"
            content = f"Based on response patterns, consider {random.choice(['adding follow-up questions', 'simplifying question wording', 'providing additional resources for high-risk respondents'])}."
        else:  # summary
            title = f"Summary insights for {questionnaire.title}"
            content = f"Overall, responses indicate {random.choice(['positive outcomes', 'areas of concern', 'stable patterns', 'improving trends'])}. " + \
                     f"The most common feedback relates to {random.choice(['question clarity', 'assessment length', 'topic relevance'])}."

        insight = AIInsight.objects.create(
            questionnaire=questionnaire,
            title=title,
            content=content,
            insight_type=insight_type,
            confidence=random.uniform(0.7, 0.98),
            is_archived=random.random() < 0.1,  # 10% archived
            created_at=created_at
        )

        insights.append(insight)

    print(f"Created {len(insights)} AI insights")
    return insights

def main():
    """Main function to generate dashboard data"""
    try:
        # Create sample data
        organizations = create_organizations(5)
        users = create_users(50, organizations)
        questionnaires = create_questionnaires(20, users, organizations)
        responses = create_responses_with_trend(500, questionnaires, users, 90)
        insights = create_ai_insights(questionnaires, 30)

        print("\nDashboard data generation completed successfully!")
        print(f"Created {len(organizations)} organizations")
        print(f"Created {len(users)} users")
        print(f"Created {len(questionnaires)} questionnaires")
        print(f"Created {len(responses)} responses")
        print(f"Created {len(insights)} AI insights")
    except Exception as e:
        print(f"Error generating dashboard data: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
