# Import the base models to avoid circular imports
from feedback.models.base import Response, Answer

# Extend the Response model with additional methods
Response.calculate_score = lambda self: _response_calculate_score(self)
Response.determine_risk_level = lambda self: _response_determine_risk_level(self)
Response.get_answer_count = lambda self: self.answers.count()
Response.mark_as_completed = lambda self: _response_mark_as_completed(self)
Response.flag_for_review = lambda self, flag=True: _response_flag_for_review(self, flag)

def _response_calculate_score(self):
    """Calculate the total score based on answers"""
    # Check if there's a scoring config for this questionnaire
    scoring_configs = self.survey.scoring_configs.filter(is_active=True)
    if scoring_configs.exists():
        # Use the default scoring config if available, otherwise use the first one
        scoring_config = scoring_configs.filter(is_default=True).first() or scoring_configs.first()
        calculated_score = scoring_config.calculate_score(self)
    else:
        # Fallback to simple scoring if no scoring config exists
        calculated_score = 0
        for answer in self.answers.all():
            if hasattr(answer, 'score') and answer.score is not None:
                calculated_score += answer.score
            elif answer.selected_choice:
                calculated_score += answer.selected_choice.score
            elif answer.numeric_value:
                calculated_score += answer.numeric_value

    self.score = calculated_score
    self.save(update_fields=['score'])
    return calculated_score

def _response_determine_risk_level(self):
    """Determine risk level based on score and questionnaire category"""
    if self.score is None:
        self.calculate_score()

    # This is a simplified example - in a real app, you'd have more sophisticated logic
    if self.survey.category in ['anxiety', 'depression', 'stress', 'mental_health']:
        if self.score < 5:
            risk = 'low'
        elif self.score < 10:
            risk = 'medium'
        elif self.score < 15:
            risk = 'high'
        else:
            risk = 'critical'
    elif self.survey.category in ['physical_health', 'clinical_assessment']:
        if self.score < 3:
            risk = 'low'
        elif self.score < 7:
            risk = 'medium'
        elif self.score < 12:
            risk = 'high'
        else:
            risk = 'critical'
    else:
        if self.score < 5:
            risk = 'low'
        elif self.score < 10:
            risk = 'medium'
        else:
            risk = 'high'

    self.risk_level = risk
    self.save(update_fields=['risk_level'])
    return risk

def _response_mark_as_completed(self):
    """Mark the response as completed"""
    from django.utils import timezone
    self.status = 'completed'
    self.completed_at = timezone.now()
    self.save(update_fields=['status', 'completed_at'])

def _response_flag_for_review(self, flag=True):
    """Flag or unflag the response for review"""
    self.flagged_for_review = flag
    self.save(update_fields=['flagged_for_review'])




# Extend the Answer model with additional methods
Answer.get_answer_display = lambda self: _answer_get_answer_display(self)
Answer.calculate_score = lambda self: _answer_calculate_score(self)

def _answer_get_answer_display(self):
    """Return a human-readable representation of the answer"""
    if self.question.question_type == 'text' or self.question.question_type == 'textarea':
        return self.text_answer
    elif self.question.question_type == 'single_choice':
        return self.selected_choice.text if self.selected_choice else None
    elif self.question.question_type == 'multiple_choice':
        return ', '.join([choice.text for choice in self.multiple_choices.all()])
    elif self.question.question_type == 'number' or self.question.question_type == 'scale':
        return str(self.numeric_value)
    elif self.question.question_type == 'date':
        return self.date_value.strftime('%Y-%m-%d') if self.date_value else None
    elif self.question.question_type == 'time':
        return self.time_value.strftime('%H:%M') if self.time_value else None
    elif self.question.question_type == 'file':
        return self.file_upload.name if self.file_upload else None
    return None

def _answer_calculate_score(self):
    """Calculate the score for this answer"""
    if self.question.is_scored:
        if self.selected_choice:
            self.score = self.selected_choice.score
        elif self.multiple_choices.exists():
            # Average the scores of all selected choices
            scores = [choice.score for choice in self.multiple_choices.all()]
            self.score = sum(scores) / len(scores) if scores else 0
        elif self.numeric_value is not None:
            # Scale numeric values based on question's max_score
            self.score = min(self.numeric_value, self.question.max_score)
        else:
            self.score = 0
        self.save(update_fields=['score'])
    return self.score


# AIAnalysis model is now defined in feedback/models/base.py
