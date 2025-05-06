#!/usr/bin/env python
"""
Generate comprehensive test data for the enhanced scoring functionality.

This script creates:
1. Sample questionnaires with different question types
2. Sample responses with varied answer patterns
3. Sample scoring systems with different scoring types
4. Sample score rules with conditional logic
5. Sample response scores with enhanced metrics
"""
import os
import sys
import random
import json
import django
from django.utils import timezone
from datetime import timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Import models
from django.contrib.auth import get_user_model
from surveys.models import Survey, Question, QuestionChoice
from surveys.models.scoring import ScoringSystem, ScoreRule, ScoreRange, ResponseScore, OptionScore
from feedback.models import Response, Answer
from groups.models import Organization
from surveys.services import EnhancedScoringService

# Use Survey as Questionnaire
Questionnaire = Survey

User = get_user_model()

def create_sample_questionnaires(count=3):
    """Create sample questionnaires with different question types"""
    print(f"Creating {count} sample questionnaires...")

    # Get or create a test user
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'username': 'testuser',
            'is_staff': True
        }
    )
    if created:
        user.set_password('password123')
        user.save()

    # Get or create a test organization
    org, created = Organization.objects.get_or_create(
        name='Test Organization',
        defaults={
            'description': 'Organization for testing',
            'created_by': user
        }
    )

    questionnaires = []

    # Create questionnaires
    for i in range(count):
        title = f"Test Questionnaire {i+1}"
        description = f"A sample questionnaire for testing enhanced scoring - Type {i+1}"

        questionnaire, created = Questionnaire.objects.get_or_create(
            title=title,
            defaults={
                'description': description,
                'created_by': user,
                'organization': org,
                'status': 'published',
                'is_template': False,
                'allow_anonymous': True,
                'show_progress': True,
                'show_numbers': True,
                'category': random.choice(['health', 'education', 'psychology', 'general'])
            }
        )

        if created:
            print(f"  Created questionnaire: {title}")

            # Create questions for this questionnaire
            create_sample_questions(questionnaire)
        else:
            print(f"  Using existing questionnaire: {title}")

        questionnaires.append(questionnaire)

    return questionnaires

def create_sample_questions(questionnaire, count=10):
    """Create sample questions for a questionnaire"""
    print(f"  Creating {count} sample questions for {questionnaire.title}...")

    question_types = [
        ('single_choice', 'Single Choice Question'),
        ('multiple_choice', 'Multiple Choice Question'),
        ('text', 'Text Question'),
        ('textarea', 'Long Text Question'),
        ('number', 'Numeric Question'),
        ('scale', 'Scale Question')
    ]

    categories = ['emotional', 'physical', 'cognitive', 'behavioral', 'social', 'general']

    for i in range(count):
        question_type, type_name = random.choice(question_types)
        category = random.choice(categories)

        question_text = f"{type_name} {i+1} - {category.capitalize()} Assessment"
        description = f"This is a {category} assessment question of type {question_type}"

        question, created = Question.objects.get_or_create(
            survey=questionnaire,
            text=question_text,
            defaults={
                'description': description,
                'question_type': question_type,
                'required': random.choice([True, False]),
                'order': i + 1,
                'category': category
            }
        )

        if created:
            # Create choices for choice-based questions
            if question_type in ['single_choice', 'multiple_choice']:
                create_sample_choices(question)

    return questionnaire

def create_sample_choices(question, count=5):
    """Create sample choices for a question"""
    for i in range(count):
        choice_text = f"Option {i+1}"

        QuestionChoice.objects.get_or_create(
            question=question,
            text=choice_text,
            defaults={
                'order': i + 1,
                'score': random.randint(0, 10)
            }
        )

def create_sample_scoring_systems(questionnaires):
    """Create sample scoring systems for questionnaires"""
    print("Creating sample scoring systems...")

    scoring_systems = []

    for questionnaire in questionnaires:
        # Create different types of scoring systems for each questionnaire
        scoring_types = ['simple_sum', 'weighted', 'range_based', 'z_score', 'percentile', 'conditional', 'custom']

        for scoring_type in scoring_types:
            name = f"{questionnaire.title} - {scoring_type.replace('_', ' ').title()} Scoring"
            description = f"A {scoring_type} scoring system for {questionnaire.title}"

            scoring_system, created = ScoringSystem.objects.get_or_create(
                questionnaire=questionnaire,
                name=name,
                defaults={
                    'description': description,
                    'scoring_type': scoring_type,
                    'created_by': questionnaire.created_by,
                    'formula': '{simple_sum} * 1.5' if scoring_type == 'custom' else ''
                }
            )

            if created:
                print(f"  Created scoring system: {name}")

                # Create score rules for this scoring system
                create_sample_score_rules(scoring_system, questionnaire)

                # Create score ranges for this scoring system
                create_sample_score_ranges(scoring_system)
            else:
                print(f"  Using existing scoring system: {name}")

            scoring_systems.append(scoring_system)

    return scoring_systems

def create_sample_score_rules(scoring_system, questionnaire):
    """Create sample score rules for a scoring system"""
    print(f"    Creating score rules for {scoring_system.name}...")

    questions = Question.objects.filter(survey=questionnaire)

    for question in questions:
        # Create a score rule for this question
        weight = round(random.uniform(0.5, 2.0), 1)
        text_score_enabled = random.choice([True, False])
        text_score = random.randint(1, 5) if text_score_enabled else 0

        # Create conditional logic for some rules
        conditional_logic = None
        if scoring_system.scoring_type == 'conditional' or random.random() < 0.3:
            if question.question_type in ['single_choice', 'multiple_choice'] and question.choices.exists():
                choice = question.choices.order_by('?').first()
                conditional_logic = {
                    "if": {
                        "question_id": question.id,
                        "answer": choice.text
                    },
                    "then": {
                        "score": random.randint(5, 15),
                        "message": "Full points awarded"
                    },
                    "else": {
                        "if": {
                            "question_id": question.id,
                            "answer": question.choices.exclude(id=choice.id).order_by('?').first().text
                        },
                        "then": {
                            "score": random.randint(1, 4),
                            "message": "Partial points awarded"
                        },
                        "else": {
                            "score": 0,
                            "message": "No points awarded"
                        }
                    }
                }

        score_rule, created = ScoreRule.objects.get_or_create(
            scoring_system=scoring_system,
            question=question,
            defaults={
                'weight': weight,
                'text_score_enabled': text_score_enabled,
                'text_score': text_score,
                'conditional_logic': conditional_logic,
                'notes': f"Score rule for {question.text}"
            }
        )

        if created and question.question_type in ['single_choice', 'multiple_choice']:
            # Create option scores for each choice
            for choice in question.choices.all():
                OptionScore.objects.get_or_create(
                    score_rule=score_rule,
                    option=choice,
                    defaults={
                        'score': random.randint(0, 10)
                    }
                )

def create_sample_score_ranges(scoring_system):
    """Create sample score ranges for a scoring system"""
    print(f"    Creating score ranges for {scoring_system.name}...")

    ranges = [
        {
            'name': 'Low',
            'min_score': 0,
            'max_score': 30,
            'description': 'Low score range',
            'interpretation': 'This score indicates a low level of the measured attribute.',
            'color': 'red'
        },
        {
            'name': 'Medium',
            'min_score': 31,
            'max_score': 70,
            'description': 'Medium score range',
            'interpretation': 'This score indicates a moderate level of the measured attribute.',
            'color': 'yellow'
        },
        {
            'name': 'High',
            'min_score': 71,
            'max_score': 100,
            'description': 'High score range',
            'interpretation': 'This score indicates a high level of the measured attribute.',
            'color': 'green'
        }
    ]

    for range_data in ranges:
        ScoreRange.objects.get_or_create(
            scoring_system=scoring_system,
            name=range_data['name'],
            min_score=range_data['min_score'],
            max_score=range_data['max_score'],
            defaults={
                'description': range_data['description'],
                'interpretation': range_data['interpretation'],
                'color': range_data['color']
            }
        )

def create_sample_responses(questionnaires, count_per_questionnaire=5):
    """Create sample responses for questionnaires"""
    print(f"Creating {count_per_questionnaire} sample responses per questionnaire...")

    responses = []

    for questionnaire in questionnaires:
        questions = Question.objects.filter(survey=questionnaire).prefetch_related('choices')

        for i in range(count_per_questionnaire):
            # Create a response
            response = Response.objects.create(
                survey=questionnaire,
                status='completed',
                patient_email=f"patient{i+1}@example.com",
                patient_age=random.randint(18, 80),
                patient_gender=random.choice(['male', 'female', 'other']),
                completion_time=random.randint(60, 600),
                created_at=timezone.now() - timedelta(days=random.randint(0, 30)),
                completed_at=timezone.now() - timedelta(days=random.randint(0, 29))
            )

            print(f"  Created response {i+1} for {questionnaire.title}")

            # Create answers for this response
            for question in questions:
                answer = Answer.objects.create(
                    response=response,
                    question=question
                )

                # Fill in the answer based on question type
                if question.question_type == 'single_choice':
                    if question.choices.exists():
                        answer.selected_choice = question.choices.order_by('?').first()
                        answer.save()

                elif question.question_type == 'multiple_choice':
                    if question.choices.exists():
                        # Select 1-3 random choices
                        num_choices = random.randint(1, min(3, question.choices.count()))
                        choices = list(question.choices.order_by('?')[:num_choices])
                        answer.multiple_choices.set(choices)

                elif question.question_type == 'text':
                    answer.text_answer = f"Sample text answer for question {question.id}"
                    answer.save()

                elif question.question_type == 'textarea':
                    answer.text_answer = f"Sample long text answer for question {question.id}.\nThis is a multi-line response."
                    answer.save()

                elif question.question_type == 'number':
                    answer.numeric_value = random.randint(1, 100)
                    answer.save()

                elif question.question_type == 'scale':
                    answer.numeric_value = random.randint(1, 10)
                    answer.save()

            responses.append(response)

    return responses

def calculate_enhanced_scores(responses, scoring_systems):
    """Calculate enhanced scores for responses"""
    print("Calculating enhanced scores for responses...")

    for response in responses:
        # Get scoring systems for this questionnaire
        questionnaire_scoring_systems = [s for s in scoring_systems if s.questionnaire == response.survey]

        for scoring_system in questionnaire_scoring_systems:
            # Create enhanced scoring service
            scoring_service = EnhancedScoringService(scoring_system)

            # Calculate enhanced score
            try:
                response_score = scoring_service.calculate_score(response)
                print(f"  Calculated enhanced score for response {response.id} using {scoring_system.name}")
                print(f"    Raw Score: {response_score.raw_score}")
                print(f"    Z-Score: {response_score.z_score}")
                print(f"    Percentile: {response_score.percentile}")
                if response_score.additional_data:
                    print(f"    Category Scores: {response_score.additional_data.get('category_scores', {})}")
                    print(f"    Subscales: {response_score.additional_data.get('subscales', {})}")
            except Exception as e:
                print(f"  Error calculating score: {str(e)}")

def main():
    """Main function to generate test data"""
    print("Generating comprehensive test data for enhanced scoring...")

    # Create sample questionnaires
    questionnaires = create_sample_questionnaires(count=3)

    # Create sample scoring systems
    scoring_systems = create_sample_scoring_systems(questionnaires)

    # Create sample responses
    responses = create_sample_responses(questionnaires, count_per_questionnaire=5)

    # Calculate enhanced scores
    calculate_enhanced_scores(responses, scoring_systems)

    print("Test data generation complete!")

if __name__ == "__main__":
    main()
