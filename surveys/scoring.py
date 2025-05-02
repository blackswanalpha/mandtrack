from django.db import models
from django.conf import settings
from .models import Questionnaire, Question, Response, Answer

class ScoringSystem(models.Model):
    """
    Model for scoring systems that can be applied to questionnaires
    """
    SCORING_TYPE_CHOICES = [
        ('simple_sum', 'Simple Sum'),
        ('weighted', 'Weighted Scoring'),
        ('range_based', 'Range-Based Scoring'),
        ('custom', 'Custom Formula'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='scoring_systems')
    scoring_type = models.CharField(max_length=20, choices=SCORING_TYPE_CHOICES, default='simple_sum')
    formula = models.TextField(blank=True, help_text="For custom scoring, enter a formula or description of the scoring logic")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_scoring_systems')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['questionnaire', 'name']
        verbose_name = 'Scoring System'
        verbose_name_plural = 'Scoring Systems'
        unique_together = ['questionnaire', 'name']

    def __str__(self):
        return f"{self.name} for {self.questionnaire.title}"

    def calculate_score(self, response):
        """
        Calculate the score for a response based on the scoring system
        """
        if not isinstance(response, Response):
            raise ValueError("Response must be a Response instance")

        if response.survey != self.questionnaire:
            raise ValueError("Response is not for the questionnaire associated with this scoring system")

        # Get all answers for this response
        answers = Answer.objects.filter(response=response)

        if self.scoring_type == 'simple_sum':
            return self._calculate_simple_sum(answers)
        elif self.scoring_type == 'weighted':
            return self._calculate_weighted_score(answers)
        elif self.scoring_type == 'range_based':
            return self._calculate_range_based_score(answers)
        elif self.scoring_type == 'custom':
            return self._calculate_custom_score(answers)
        else:
            raise ValueError(f"Unsupported scoring type: {self.scoring_type}")

    def _calculate_simple_sum(self, answers):
        """
        Calculate a simple sum of all answer values
        """
        total = 0
        for answer in answers:
            # Get the score rule for this question
            try:
                score_rule = ScoreRule.objects.get(
                    scoring_system=self,
                    question=answer.question
                )

                # Get the option score for this answer
                if answer.selected_option:
                    option_score = OptionScore.objects.get(
                        score_rule=score_rule,
                        option=answer.selected_option
                    )
                    total += option_score.score
                elif answer.text_value and score_rule.text_score_enabled:
                    # For text answers, use the text_score if enabled
                    total += score_rule.text_score
            except (ScoreRule.DoesNotExist, OptionScore.DoesNotExist):
                # Skip questions without scoring rules or options without scores
                continue

        return total

    def _calculate_weighted_score(self, answers):
        """
        Calculate a weighted score based on question weights
        """
        total = 0
        for answer in answers:
            try:
                score_rule = ScoreRule.objects.get(
                    scoring_system=self,
                    question=answer.question
                )

                if answer.selected_option:
                    option_score = OptionScore.objects.get(
                        score_rule=score_rule,
                        option=answer.selected_option
                    )
                    total += option_score.score * score_rule.weight
                elif answer.text_value and score_rule.text_score_enabled:
                    total += score_rule.text_score * score_rule.weight
            except (ScoreRule.DoesNotExist, OptionScore.DoesNotExist):
                continue

        return total

    def _calculate_range_based_score(self, answers):
        """
        Calculate a score and determine which range it falls into
        """
        # First calculate the raw score (using weighted scoring)
        raw_score = self._calculate_weighted_score(answers)

        # Find which score range this falls into
        try:
            score_range = ScoreRange.objects.filter(
                scoring_system=self,
                min_score__lte=raw_score,
                max_score__gte=raw_score
            ).first()

            if score_range:
                return {
                    'raw_score': raw_score,
                    'range_name': score_range.name,
                    'range_description': score_range.description,
                    'interpretation': score_range.interpretation
                }
            else:
                return {
                    'raw_score': raw_score,
                    'range_name': 'Unknown',
                    'range_description': 'Score does not fall within any defined range',
                    'interpretation': None
                }
        except Exception as e:
            return {
                'raw_score': raw_score,
                'error': str(e)
            }

    def _calculate_custom_score(self, answers):
        """
        Calculate a custom score based on the formula
        """
        # This would typically call a custom scoring function or evaluate a formula
        # For now, we'll just return a placeholder
        return {
            'raw_score': 0,
            'note': 'Custom scoring requires implementation specific to the formula'
        }


class ScoreRule(models.Model):
    """
    Model for scoring rules for individual questions
    """
    scoring_system = models.ForeignKey(ScoringSystem, on_delete=models.CASCADE, related_name='score_rules')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='score_rules')
    weight = models.FloatField(default=1.0, help_text="Weight to apply to this question's score")
    text_score_enabled = models.BooleanField(default=False, help_text="Enable scoring for text answers")
    text_score = models.FloatField(default=0.0, help_text="Score to apply to text answers if enabled")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['scoring_system', 'question__order']
        verbose_name = 'Score Rule'
        verbose_name_plural = 'Score Rules'
        unique_together = ['scoring_system', 'question']

    def __str__(self):
        return f"Scoring for {self.question.text} in {self.scoring_system.name}"


class OptionScore(models.Model):
    """
    Model for scores assigned to individual answer options
    """
    score_rule = models.ForeignKey(ScoreRule, on_delete=models.CASCADE, related_name='option_scores')
    option = models.ForeignKey('QuestionOption', on_delete=models.CASCADE, related_name='scores')
    score = models.FloatField(default=0.0)

    class Meta:
        ordering = ['score_rule', 'option__order']
        verbose_name = 'Option Score'
        verbose_name_plural = 'Option Scores'
        unique_together = ['score_rule', 'option']

    def __str__(self):
        return f"Score for '{self.option.text}': {self.score}"


class ScoreRange(models.Model):
    """
    Model for defining score ranges and their interpretations
    """
    scoring_system = models.ForeignKey(ScoringSystem, on_delete=models.CASCADE, related_name='score_ranges')
    name = models.CharField(max_length=100)
    min_score = models.FloatField()
    max_score = models.FloatField()
    description = models.TextField(blank=True)
    interpretation = models.TextField(blank=True, help_text="Clinical interpretation or meaning of this score range")
    color = models.CharField(max_length=20, default='gray', help_text="Color code for visual representation (e.g., 'red', 'yellow', 'green')")

    class Meta:
        ordering = ['scoring_system', 'min_score']
        verbose_name = 'Score Range'
        verbose_name_plural = 'Score Ranges'

    def __str__(self):
        return f"{self.name}: {self.min_score} to {self.max_score}"


class ResponseScore(models.Model):
    """
    Model for storing calculated scores for responses
    """
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='scores')
    scoring_system = models.ForeignKey(ScoringSystem, on_delete=models.CASCADE, related_name='response_scores')
    raw_score = models.FloatField()
    score_range = models.ForeignKey(ScoreRange, on_delete=models.SET_NULL, null=True, blank=True, related_name='responses')
    calculated_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-calculated_at']
        verbose_name = 'Response Score'
        verbose_name_plural = 'Response Scores'
        unique_together = ['response', 'scoring_system']

    def __str__(self):
        return f"Score for {self.response}: {self.raw_score}"
