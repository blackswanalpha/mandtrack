"""
Models for the scoring system.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class ScoringSystem(models.Model):
    """
    Model for scoring systems
    """
    SCORING_TYPE_CHOICES = [
        ('simple_sum', 'Simple Sum'),
        ('weighted', 'Weighted Scoring'),
        ('range_based', 'Range-Based Scoring'),
        ('z_score', 'Z-Score Normalization'),
        ('percentile', 'Percentile Ranking'),
        ('conditional', 'Conditional Scoring'),
        ('custom', 'Custom Formula'),
    ]

    id = models.BigAutoField(primary_key=True)
    # Use the correct model reference with the actual database model name
    questionnaire = models.ForeignKey('surveys.SurveysQuestionnaire', on_delete=models.CASCADE, related_name='scoring_systems')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    scoring_type = models.CharField(max_length=20, choices=SCORING_TYPE_CHOICES, default='simple_sum')
    formula = models.TextField(blank=True, help_text="Custom formula for scoring (used with custom scoring type)")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_scoring_systems', null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def get_questionnaire(self):
        """Get the questionnaire object, resolving the string reference if needed"""
        if isinstance(self.questionnaire, str):
            from django.apps import apps
            # Try all possible model names
            for model_name in ['Questionnaire', 'Survey', 'questionnaire', 'survey', 'SurveysQuestionnaire']:
                try:
                    Questionnaire = apps.get_model('surveys', model_name)
                    return Questionnaire.objects.get(pk=self.questionnaire)
                except Exception:
                    continue
        return self.questionnaire

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Scoring System'
        verbose_name_plural = 'Scoring Systems'
        indexes = [
            models.Index(fields=['questionnaire'], name='scoring_system_quest_idx'),
            models.Index(fields=['is_active'], name='scoring_system_active_idx'),
            models.Index(fields=['is_default'], name='scoring_system_default_idx'),
        ]

    def __str__(self):
        try:
            questionnaire = self.get_questionnaire()
            return f"{self.name} for {questionnaire.title if questionnaire else 'Unknown'}"
        except Exception:
            return f"{self.name} for questionnaire {self.questionnaire}"

    def calculate_score(self, response):
        """
        Calculate score for a response based on the scoring type
        """
        if self.scoring_type == 'simple_sum':
            return self._calculate_simple_sum(response)
        elif self.scoring_type == 'weighted':
            return self._calculate_weighted_score(response)
        elif self.scoring_type == 'range_based':
            return self._calculate_range_based_score(response)
        elif self.scoring_type == 'z_score':
            return self._calculate_z_score(response)
        elif self.scoring_type == 'percentile':
            return self._calculate_percentile(response)
        elif self.scoring_type == 'conditional':
            return self._calculate_conditional_score(response)
        elif self.scoring_type == 'custom':
            return self._calculate_custom_score(response)
        return 0

    def _calculate_simple_sum(self, response):
        """Calculate simple sum of all answer scores"""
        total = 0
        for answer in response.answers.all():
            # Get the score rule for this question
            rule = ScoreRule.objects.filter(scoring_system=self, question=answer.question).first()
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
                    total += option_score.score

            elif answer.question.question_type == 'multiple_choice':
                # Sum scores for all selected choices
                for choice in answer.multiple_choices.all():
                    option_score = OptionScore.objects.filter(
                        score_rule=rule,
                        option=choice
                    ).first()
                    if option_score:
                        total += option_score.score

            elif answer.question.question_type in ['number', 'scale']:
                # Use the numeric value directly
                if answer.value and isinstance(answer.value, (int, float)):
                    total += float(answer.value)

            elif answer.question.question_type in ['text', 'textarea'] and rule.text_score_enabled:
                # Use the text score if enabled
                total += rule.text_score

        return total

    def _calculate_weighted_score(self, response):
        """Calculate weighted score based on question weights"""
        total = 0
        total_weight = 0

        for answer in response.answers.all():
            # Get the score rule for this question
            rule = ScoreRule.objects.filter(scoring_system=self, question=answer.question).first()
            if not rule:
                continue

            # Get the weight for this question
            weight = rule.weight if rule else 1.0
            total_weight += weight

            # Calculate score based on answer type
            answer_score = 0

            if answer.question.question_type == 'single_choice' and answer.selected_choice:
                # Get option score for this choice
                option_score = OptionScore.objects.filter(
                    score_rule=rule,
                    option=answer.selected_choice
                ).first()
                if option_score:
                    answer_score = option_score.score

            elif answer.question.question_type == 'multiple_choice':
                # Sum scores for all selected choices
                for choice in answer.multiple_choices.all():
                    option_score = OptionScore.objects.filter(
                        score_rule=rule,
                        option=choice
                    ).first()
                    if option_score:
                        answer_score += option_score.score

            elif answer.question.question_type in ['number', 'scale']:
                # Use the numeric value directly
                if answer.value and isinstance(answer.value, (int, float)):
                    answer_score = float(answer.value)

            elif answer.question.question_type in ['text', 'textarea'] and rule.text_score_enabled:
                # Use the text score if enabled
                answer_score = rule.text_score

            # Add weighted score to total
            total += answer_score * weight

        # Return weighted average if there are weights
        if total_weight > 0:
            return total / total_weight
        return 0

    def _calculate_range_based_score(self, response):
        """Calculate score and determine the range it falls into"""
        # First calculate the raw score using simple sum or weighted method
        if self.scoring_type == 'range_based':
            raw_score = self._calculate_simple_sum(response)
        else:
            raw_score = self._calculate_weighted_score(response)

        # Find the range this score falls into
        score_range = ScoreRange.objects.filter(
            scoring_system=self,
            min_score__lte=raw_score,
            max_score__gte=raw_score
        ).first()

        return {
            'raw_score': raw_score,
            'range': score_range
        }

    def _calculate_z_score(self, response):
        """
        Calculate Z-score normalization
        Z-score = (raw_score - mean) / standard_deviation
        """
        # First calculate the raw score using simple sum
        raw_score = self._calculate_simple_sum(response)

        # Get all scores for this scoring system to calculate mean and std dev
        from django.db.models import Avg, StdDev

        # Get statistics from existing scores
        stats = ResponseScore.objects.filter(
            scoring_system=self
        ).aggregate(
            mean=Avg('raw_score'),
            stddev=StdDev('raw_score')
        )

        mean = stats['mean'] or 0
        stddev = stats['stddev'] or 1  # Avoid division by zero

        # If there's no standard deviation (e.g., all scores are the same), return 0
        if stddev == 0:
            return 0

        # Calculate Z-score
        z_score = (raw_score - mean) / stddev

        return {
            'raw_score': raw_score,
            'z_score': z_score,
            'mean': mean,
            'stddev': stddev
        }

    def _calculate_percentile(self, response):
        """
        Calculate percentile ranking
        Percentile = (number of scores below this score) / (total number of scores) * 100
        """
        # First calculate the raw score using simple sum
        raw_score = self._calculate_simple_sum(response)

        # Get all scores for this scoring system
        all_scores = ResponseScore.objects.filter(
            scoring_system=self
        ).values_list('raw_score', flat=True)

        # Convert to list for easier manipulation
        all_scores = list(all_scores)

        # If there are no other scores, return 50th percentile
        if not all_scores:
            return {
                'raw_score': raw_score,
                'percentile': 50.0
            }

        # Count scores below this score
        scores_below = sum(1 for score in all_scores if score < raw_score)

        # Calculate percentile
        percentile = (scores_below / len(all_scores)) * 100

        return {
            'raw_score': raw_score,
            'percentile': percentile
        }

    def _calculate_conditional_score(self, response):
        """
        Calculate score based on conditional logic
        This allows for complex scoring rules based on answer patterns
        """
        # Start with a base score
        base_score = self._calculate_simple_sum(response)

        # Get all answers for this response
        answers = response.answers.all().select_related('question')

        # Create a dictionary of question_id -> answer for easier lookup
        answer_map = {str(answer.question.id): answer for answer in answers}

        # Apply conditional rules
        # For now, we'll implement a simple version that looks for specific patterns

        # Get all rules for this scoring system
        rules = ScoreRule.objects.filter(scoring_system=self)

        # Track conditional adjustments
        adjustments = []

        # Check for conditional patterns in the rules
        for rule in rules:
            # Skip rules without conditional logic
            if not hasattr(rule, 'conditional_logic') or not rule.conditional_logic:
                continue

            # Parse conditional logic
            try:
                conditions = rule.conditional_logic.get('conditions', [])
                adjustment = rule.conditional_logic.get('adjustment', 0)

                # Check if all conditions are met
                conditions_met = True

                for condition in conditions:
                    question_id = condition.get('question_id')
                    operator = condition.get('operator', '==')
                    value = condition.get('value')

                    # Skip if any required field is missing
                    if not question_id or not value:
                        conditions_met = False
                        break

                    # Get the answer for this question
                    answer = answer_map.get(question_id)

                    # Skip if question wasn't answered
                    if not answer:
                        conditions_met = False
                        break

                    # Check the condition based on the operator
                    if operator == '==' and answer.value != value:
                        conditions_met = False
                        break
                    elif operator == '!=' and answer.value == value:
                        conditions_met = False
                        break
                    elif operator == '>' and not (answer.value and answer.value > value):
                        conditions_met = False
                        break
                    elif operator == '>=' and not (answer.value and answer.value >= value):
                        conditions_met = False
                        break
                    elif operator == '<' and not (answer.value and answer.value < value):
                        conditions_met = False
                        break
                    elif operator == '<=' and not (answer.value and answer.value <= value):
                        conditions_met = False
                        break

                # If all conditions are met, apply the adjustment
                if conditions_met:
                    base_score += adjustment
                    adjustments.append({
                        'rule_id': rule.id,
                        'adjustment': adjustment,
                        'description': rule.conditional_logic.get('description', '')
                    })

            except Exception as e:
                # Log the error but continue processing
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error processing conditional logic for rule {rule.id}: {str(e)}")

        return {
            'raw_score': base_score,
            'adjustments': adjustments
        }

    def _calculate_custom_score(self, response):
        """
        Calculate score using custom formula
        This allows for complex mathematical formulas to be applied
        """
        # If no formula is provided, fall back to simple sum
        if not self.formula:
            return self._calculate_simple_sum(response)

        try:
            # Get all answers for this response
            answers = response.answers.all().select_related('question')

            # Create a dictionary of question variables
            variables = {}

            # Add basic variables
            variables['response_id'] = str(response.id)
            variables['total_questions'] = response.survey.questions.count()
            variables['answered_questions'] = answers.count()

            # Add answer-specific variables
            for answer in answers:
                # Create a safe variable name from the question ID
                var_name = f"q_{answer.question.id}"

                # Store the answer value
                if answer.question.question_type in ['number', 'scale']:
                    # For numeric questions, store the numeric value
                    try:
                        variables[var_name] = float(answer.value) if answer.value else 0
                    except (ValueError, TypeError):
                        variables[var_name] = 0
                elif answer.question.question_type == 'single_choice' and answer.selected_choice:
                    # For single choice questions, store the choice score
                    rule = ScoreRule.objects.filter(scoring_system=self, question=answer.question).first()
                    if rule:
                        option_score = OptionScore.objects.filter(
                            score_rule=rule,
                            option=answer.selected_choice
                        ).first()
                        variables[var_name] = option_score.score if option_score else 0
                    else:
                        variables[var_name] = 0
                elif answer.question.question_type == 'multiple_choice':
                    # For multiple choice questions, store the sum of choice scores
                    rule = ScoreRule.objects.filter(scoring_system=self, question=answer.question).first()
                    if rule:
                        total = 0
                        for choice in answer.multiple_choices.all():
                            option_score = OptionScore.objects.filter(
                                score_rule=rule,
                                option=choice
                            ).first()
                            if option_score:
                                total += option_score.score
                        variables[var_name] = total
                    else:
                        variables[var_name] = 0
                else:
                    # For other question types, default to 0
                    variables[var_name] = 0

            # Add simple sum as a variable
            variables['simple_sum'] = self._calculate_simple_sum(response)

            # Add weighted sum as a variable
            variables['weighted_sum'] = self._calculate_weighted_score(response)

            # Execute the formula using a safe evaluation method
            # We'll use a simple approach for now, but in production this should be more secure
            import math

            # Add math functions to the variables
            for name in dir(math):
                if not name.startswith('_'):
                    variables[name] = getattr(math, name)

            # Replace variable placeholders in the formula
            formula = self.formula
            for var_name, var_value in variables.items():
                formula = formula.replace(f"{{{var_name}}}", str(var_value))

            # Evaluate the formula
            result = eval(formula, {"__builtins__": {}}, variables)

            return {
                'raw_score': float(result),
                'formula': self.formula,
                'variables': variables
            }

        except Exception as e:
            # Log the error and fall back to simple sum
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error evaluating custom formula: {str(e)}")
            return self._calculate_simple_sum(response)


class ScoreRule(models.Model):
    """
    Model for scoring rules for questions
    """
    id = models.BigAutoField(primary_key=True)
    scoring_system = models.ForeignKey(ScoringSystem, on_delete=models.CASCADE, related_name='score_rules')
    # Use the correct model reference with the actual database model name
    question = models.ForeignKey('surveys.SurveysQuestion', on_delete=models.CASCADE, related_name='score_rules')
    weight = models.FloatField(default=1.0)
    text_score_enabled = models.BooleanField(default=False)
    text_score = models.FloatField(default=0.0)
    conditional_logic = models.JSONField(blank=True, null=True, help_text="JSON configuration for conditional scoring logic")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def get_question(self):
        """Get the question object, resolving the string reference if needed"""
        if isinstance(self.question, str):
            from django.apps import apps
            # Try all possible model names
            for model_name in ['Question', 'question', 'SurveysQuestion']:
                try:
                    Question = apps.get_model('surveys', model_name)
                    return Question.objects.get(pk=self.question)
                except Exception:
                    continue
        return self.question

    class Meta:
        # Fix the ordering issue by removing the reference to question__order
        ordering = ['id']
        verbose_name = 'Score Rule'
        verbose_name_plural = 'Score Rules'
        unique_together = ('scoring_system', 'question')
        indexes = [
            models.Index(fields=['scoring_system'], name='score_rule_system_idx'),
            models.Index(fields=['question'], name='score_rule_question_idx'),
        ]

    def __str__(self):
        try:
            question = self.get_question()
            question_text = question.text[:30] + "..." if question and len(question.text) > 30 else "Unknown"
            return f"Rule for {question_text} in {self.scoring_system.name}"
        except Exception:
            return f"Rule for question {self.question} in {self.scoring_system.name}"


class OptionScore(models.Model):
    """
    Model for scores assigned to question choices
    """
    id = models.BigAutoField(primary_key=True)
    score_rule = models.ForeignKey(ScoreRule, on_delete=models.CASCADE, related_name='option_scores')
    # Use the correct model reference with the actual database model name
    option = models.ForeignKey('surveys.SurveysQuestionchoice', on_delete=models.CASCADE, related_name='option_scores')
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def get_option(self):
        """Get the option object, resolving the string reference if needed"""
        if isinstance(self.option, str):
            from django.apps import apps
            # Try all possible model names
            for model_name in ['QuestionChoice', 'questionchoice', 'SurveysQuestionchoice']:
                try:
                    QuestionChoice = apps.get_model('surveys', model_name)
                    return QuestionChoice.objects.get(pk=self.option)
                except Exception:
                    continue
        return self.option

    class Meta:
        # Fix the ordering issue by removing the reference to option__order
        ordering = ['id']
        verbose_name = 'Option Score'
        verbose_name_plural = 'Option Scores'
        unique_together = ('score_rule', 'option')
        indexes = [
            models.Index(fields=['score_rule'], name='option_score_rule_idx'),
            models.Index(fields=['option'], name='option_score_option_idx'),
        ]

    def __str__(self):
        try:
            option = self.get_option()
            option_text = option.text if option else "Unknown"
            return f"Score for {option_text} in {self.score_rule}"
        except Exception:
            return f"Score for option {self.option} in {self.score_rule}"


class ScoreRange(models.Model):
    """
    Model for score ranges and interpretations
    """
    id = models.BigAutoField(primary_key=True)
    scoring_system = models.ForeignKey(ScoringSystem, on_delete=models.CASCADE, related_name='score_ranges')
    name = models.CharField(max_length=100)
    min_score = models.FloatField()
    max_score = models.FloatField()
    color = models.CharField(max_length=20, default='#3498db')
    description = models.TextField(blank=True)
    interpretation = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['min_score']
        verbose_name = 'Score Range'
        verbose_name_plural = 'Score Ranges'
        indexes = [
            models.Index(fields=['scoring_system'], name='score_range_system_idx'),
            models.Index(fields=['min_score'], name='score_range_min_idx'),
            models.Index(fields=['max_score'], name='score_range_max_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.min_score}-{self.max_score}) in {self.scoring_system.name}"


class ResponseScore(models.Model):
    """
    Model for storing calculated scores for responses
    """
    id = models.BigAutoField(primary_key=True)
    # Use string reference to avoid circular imports
    response = models.ForeignKey('feedback.Response', on_delete=models.CASCADE, related_name='scores')
    scoring_system = models.ForeignKey(ScoringSystem, on_delete=models.CASCADE, related_name='response_scores')
    raw_score = models.FloatField()
    score_range = models.ForeignKey(ScoreRange, on_delete=models.SET_NULL, null=True, blank=True, related_name='response_scores')
    notes = models.TextField(blank=True)

    # Additional scoring data
    z_score = models.FloatField(null=True, blank=True)
    percentile = models.FloatField(null=True, blank=True)
    additional_data = models.JSONField(null=True, blank=True, help_text="Additional scoring data in JSON format")

    calculated_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def get_response(self):
        """Get the response object, resolving the string reference if needed"""
        if isinstance(self.response, str):
            from django.apps import apps
            # Try all possible model names
            for model_name in ['Response', 'response', 'FeedbackResponse']:
                try:
                    Response = apps.get_model('feedback', model_name)
                    return Response.objects.get(pk=self.response)
                except Exception:
                    continue
        return self.response

    class Meta:
        ordering = ['-calculated_at']
        verbose_name = 'Response Score'
        verbose_name_plural = 'Response Scores'
        unique_together = ('response', 'scoring_system')
        indexes = [
            models.Index(fields=['response'], name='resp_score_response_idx'),
            models.Index(fields=['scoring_system'], name='resp_score_system_idx'),
            models.Index(fields=['score_range'], name='resp_score_range_idx'),
            models.Index(fields=['calculated_at'], name='resp_score_calc_at_idx'),
        ]

    def __str__(self):
        try:
            response = self.get_response()
            response_id = response.id if response else "Unknown"
            return f"Score for response {response_id} using {self.scoring_system.name}"
        except Exception:
            return f"Score for response {self.response} using {self.scoring_system.name}"
