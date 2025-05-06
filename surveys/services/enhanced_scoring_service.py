"""
Enhanced Scoring Service

This module provides advanced scoring functionality including:
- Z-score calculation
- Percentile calculation
- Conditional logic processing
- Category and subscale scoring
"""
import math
import json
import logging
from django.db.models import Avg, StdDev
from django.utils import timezone
from django.apps import apps
from surveys.models.scoring import (
    ScoringSystem, ScoreRule, ScoreRange, ResponseScore, OptionScore
)

# Get model references with fallbacks to actual database model names
def get_model(app_label, model_name):
    """Get a model from the app registry"""
    try:
        return apps.get_model(app_label, model_name)
    except Exception:
        return None

# Define model getters with fallbacks
def get_question_model():
    """Get the Question model with fallbacks"""
    for model_name in ['Question', 'question', 'SurveysQuestion']:
        model = get_model('surveys', model_name)
        if model is not None:
            return model
    return None

def get_question_choice_model():
    """Get the QuestionChoice model with fallbacks"""
    for model_name in ['QuestionChoice', 'questionchoice', 'SurveysQuestionchoice']:
        model = get_model('surveys', model_name)
        if model is not None:
            return model
    return None

def get_response_model():
    """Get the Response model with fallbacks"""
    for model_name in ['Response', 'response', 'FeedbackResponse']:
        model = get_model('feedback', model_name)
        if model is not None:
            return model
    return None

def get_answer_model():
    """Get the Answer model with fallbacks"""
    for model_name in ['Answer', 'answer', 'FeedbackAnswer']:
        model = get_model('feedback', model_name)
        if model is not None:
            return model
    return None

# Get model references
Question = get_question_model()
QuestionChoice = get_question_choice_model()
Response = get_response_model()
Answer = get_answer_model()

logger = logging.getLogger(__name__)

class EnhancedScoringService:
    """
    Service for enhanced scoring calculations
    """

    def __init__(self, scoring_system):
        """
        Initialize with a scoring system

        Args:
            scoring_system: ScoringSystem instance
        """
        self.scoring_system = scoring_system

    def calculate_score(self, response):
        """
        Calculate score for a response with enhanced metrics

        Args:
            response: Response instance

        Returns:
            ResponseScore instance with enhanced metrics
        """
        # Calculate raw score using the existing method
        result = self.scoring_system.calculate_score(response)

        # Extract raw score from result
        if isinstance(result, dict):
            raw_score = result.get('raw_score', 0)
            score_range = result.get('range')
        else:
            raw_score = result
            # Find the range this score falls into
            score_range = ScoreRange.objects.filter(
                scoring_system=self.scoring_system,
                min_score__lte=raw_score,
                max_score__gte=raw_score
            ).first()

        # Calculate z-score and percentile
        z_score, percentile = self._calculate_statistical_metrics(raw_score)

        # Calculate category scores
        additional_data = self._calculate_additional_data(response)

        # Process conditional logic
        conditional_adjustments = self._process_conditional_logic(response, raw_score)
        if conditional_adjustments:
            additional_data['conditional_adjustments'] = conditional_adjustments

        # Create or update response score
        response_score, created = ResponseScore.objects.update_or_create(
            response=response,
            scoring_system=self.scoring_system,
            defaults={
                'raw_score': raw_score,
                'score_range': score_range,
                'z_score': z_score,
                'percentile': percentile,
                'additional_data': additional_data,
                'calculated_at': timezone.now(),
                'notes': f"Score calculated with enhanced metrics on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        )

        return response_score

    def _calculate_statistical_metrics(self, raw_score):
        """
        Calculate z-score and percentile for a raw score

        Args:
            raw_score: Raw score value

        Returns:
            tuple: (z_score, percentile)
        """
        # Get statistics from existing scores
        stats = ResponseScore.objects.filter(
            scoring_system=self.scoring_system
        ).aggregate(
            mean=Avg('raw_score'),
            stddev=StdDev('raw_score')
        )

        mean = stats['mean'] or 0
        stddev = stats['stddev'] or 1  # Avoid division by zero

        # If there's no standard deviation (e.g., all scores are the same), use default
        if stddev == 0:
            stddev = 1

        # Calculate Z-score
        z_score = (raw_score - mean) / stddev

        # Calculate percentile using the error function
        # This converts z-score to percentile using the cumulative distribution function
        percentile = 100 * (0.5 + 0.5 * math.erf(z_score / math.sqrt(2)))

        # Round to 2 decimal places
        z_score = round(z_score, 2)
        percentile = round(percentile, 2)

        return z_score, percentile

    def _calculate_additional_data(self, response):
        """
        Calculate additional scoring data including category scores and subscales

        Args:
            response: Response instance

        Returns:
            dict: Additional scoring data
        """
        # Initialize additional data
        additional_data = {
            'category_scores': {},
            'subscales': {}
        }

        # Get all answers for this response
        answers = response.answers.all().select_related('question')

        # Group questions by category
        categories = {}
        for answer in answers:
            category = answer.question.category or 'general'
            if category not in categories:
                categories[category] = []
            categories[category].append(answer)

        # Calculate score for each category
        for category, category_answers in categories.items():
            category_score = 0
            for answer in category_answers:
                # Get the score rule for this question
                rule = ScoreRule.objects.filter(
                    scoring_system=self.scoring_system,
                    question=answer.question
                ).first()

                if not rule:
                    continue

                # Calculate score based on answer type
                if answer.question.question_type == 'single_choice' and answer.selected_choice:
                    # Get option score for this choice
                    option_score = OptionScore.objects.filter(
                        score_rule=rule,
                        option=answer.selected_choice
                    ).first()
                    if option_score:
                        category_score += option_score.score

                elif answer.question.question_type == 'multiple_choice':
                    # Sum scores for all selected choices
                    for choice in answer.multiple_choices.all():
                        option_score = OptionScore.objects.filter(
                            score_rule=rule,
                            option=choice
                        ).first()
                        if option_score:
                            category_score += option_score.score

                elif answer.question.question_type in ['number', 'scale']:
                    # Use the numeric value directly
                    if answer.value and isinstance(answer.value, (int, float)):
                        category_score += float(answer.value)

                elif answer.question.question_type in ['text', 'textarea'] and rule.text_score_enabled:
                    # Use the text score if enabled
                    category_score += rule.text_score

            # Add category score to additional data
            additional_data['category_scores'][category] = round(category_score, 2)

        # Define subscales based on question properties
        # This is a simplified example - you would customize this based on your questionnaire structure
        subscales = {
            'cognitive': [],
            'emotional': [],
            'physical': [],
            'behavioral': []
        }

        # Assign questions to subscales based on keywords in the question text
        # This is a simple heuristic approach - you would customize this
        for answer in answers:
            question_text = answer.question.text.lower()

            if any(word in question_text for word in ['think', 'thought', 'memory', 'concentrate', 'decision']):
                subscales['cognitive'].append(answer)

            if any(word in question_text for word in ['feel', 'emotion', 'mood', 'sad', 'happy', 'angry']):
                subscales['emotional'].append(answer)

            if any(word in question_text for word in ['body', 'pain', 'sleep', 'tired', 'energy', 'physical']):
                subscales['physical'].append(answer)

            if any(word in question_text for word in ['do', 'activity', 'behavior', 'action', 'interact']):
                subscales['behavioral'].append(answer)

        # Calculate score for each subscale
        for subscale, subscale_answers in subscales.items():
            if not subscale_answers:
                additional_data['subscales'][subscale] = 0
                continue

            subscale_score = 0
            for answer in subscale_answers:
                # Get the score rule for this question
                rule = ScoreRule.objects.filter(
                    scoring_system=self.scoring_system,
                    question=answer.question
                ).first()

                if not rule:
                    continue

                # Calculate score based on answer type (similar to category scoring)
                if answer.question.question_type == 'single_choice' and answer.selected_choice:
                    option_score = OptionScore.objects.filter(
                        score_rule=rule,
                        option=answer.selected_choice
                    ).first()
                    if option_score:
                        subscale_score += option_score.score

                elif answer.question.question_type == 'multiple_choice':
                    for choice in answer.multiple_choices.all():
                        option_score = OptionScore.objects.filter(
                            score_rule=rule,
                            option=choice
                        ).first()
                        if option_score:
                            subscale_score += option_score.score

                elif answer.question.question_type in ['number', 'scale']:
                    if answer.value and isinstance(answer.value, (int, float)):
                        subscale_score += float(answer.value)

                elif answer.question.question_type in ['text', 'textarea'] and rule.text_score_enabled:
                    subscale_score += rule.text_score

            # Add subscale score to additional data
            additional_data['subscales'][subscale] = round(subscale_score, 2)

        return additional_data

    def _process_conditional_logic(self, response, base_score):
        """
        Process conditional logic rules

        Args:
            response: Response instance
            base_score: Base score before conditional adjustments

        Returns:
            list: Conditional adjustments applied
        """
        # Get all answers for this response
        answers = response.answers.all().select_related('question')

        # Create a dictionary of question_id -> answer for easier lookup
        answer_map = {str(answer.question.id): answer for answer in answers}

        # Get all rules with conditional logic for this scoring system
        rules = ScoreRule.objects.filter(
            scoring_system=self.scoring_system,
            conditional_logic__isnull=False
        )

        # Track conditional adjustments
        adjustments = []

        # Process each rule with conditional logic
        for rule in rules:
            try:
                # Skip if conditional_logic is empty
                if not rule.conditional_logic:
                    continue

                # Process the conditional logic
                result = self._evaluate_condition(rule.conditional_logic, answer_map, rule)

                if result:
                    adjustments.append(result)

            except Exception as e:
                logger.error(f"Error processing conditional logic for rule {rule.id}: {str(e)}")

        return adjustments

    def _evaluate_condition(self, condition, answer_map, rule, depth=0):
        """
        Recursively evaluate a conditional logic expression

        Args:
            condition: Conditional logic dictionary
            answer_map: Dictionary mapping question IDs to answers
            rule: ScoreRule instance
            depth: Current recursion depth (to prevent infinite recursion)

        Returns:
            dict: Result of the condition evaluation, or None if condition not met
        """
        # Prevent infinite recursion
        if depth > 10:
            logger.warning(f"Maximum recursion depth reached for rule {rule.id}")
            return None

        # Handle if-then-else structure
        if 'if' in condition:
            if_condition = condition.get('if', {})
            then_result = condition.get('then', {})
            else_result = condition.get('else', {})

            # Check if the condition is met
            if self._check_condition(if_condition, answer_map):
                # If condition is met, process the 'then' branch
                if isinstance(then_result, dict) and ('if' in then_result):
                    # Nested condition in 'then' branch
                    return self._evaluate_condition(then_result, answer_map, rule, depth + 1)
                else:
                    # Terminal 'then' branch
                    return {
                        'rule_id': rule.id,
                        'question_id': rule.question.id if rule.question else None,
                        'condition': if_condition,
                        'result': then_result,
                        'adjustment': then_result.get('score', 0),
                        'message': then_result.get('message', '')
                    }
            elif else_result:
                # If condition is not met, process the 'else' branch
                if isinstance(else_result, dict) and ('if' in else_result):
                    # Nested condition in 'else' branch
                    return self._evaluate_condition(else_result, answer_map, rule, depth + 1)
                else:
                    # Terminal 'else' branch
                    return {
                        'rule_id': rule.id,
                        'question_id': rule.question.id if rule.question else None,
                        'condition': if_condition,
                        'result': else_result,
                        'adjustment': else_result.get('score', 0),
                        'message': else_result.get('message', '')
                    }

        return None

    def _check_condition(self, condition, answer_map):
        """
        Check if a condition is met based on the answers

        Args:
            condition: Condition dictionary
            answer_map: Dictionary mapping question IDs to answers

        Returns:
            bool: True if condition is met, False otherwise
        """
        # Get the question ID and expected answer
        question_id = condition.get('question_id')
        expected_answer = condition.get('answer')
        operator = condition.get('operator', '==')

        # If question_id is not specified, check the answer directly
        if not question_id and 'answer' in condition:
            return True

        # Get the answer for this question
        answer = answer_map.get(str(question_id))

        # If question wasn't answered, condition is not met
        if not answer:
            return False

        # Get the actual answer value based on question type
        actual_answer = None
        if answer.question.question_type == 'single_choice' and answer.selected_choice:
            actual_answer = answer.selected_choice.text
        elif answer.question.question_type == 'multiple_choice':
            # For multiple choice, check if expected answer is in the selected choices
            selected_texts = [choice.text for choice in answer.multiple_choices.all()]
            return expected_answer in selected_texts
        elif answer.question.question_type in ['number', 'scale']:
            try:
                actual_answer = float(answer.value) if answer.value else None
                expected_answer = float(expected_answer) if expected_answer else None
            except (ValueError, TypeError):
                return False
        else:
            actual_answer = answer.value

        # Check the condition based on the operator
        if operator == '==' and actual_answer == expected_answer:
            return True
        elif operator == '!=' and actual_answer != expected_answer:
            return True
        elif operator == '>' and actual_answer and expected_answer and actual_answer > expected_answer:
            return True
        elif operator == '>=' and actual_answer and expected_answer and actual_answer >= expected_answer:
            return True
        elif operator == '<' and actual_answer and expected_answer and actual_answer < expected_answer:
            return True
        elif operator == '<=' and actual_answer and expected_answer and actual_answer <= expected_answer:
            return True

        return False
