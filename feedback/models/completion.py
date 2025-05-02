from django.db import models
from django.conf import settings
from django.utils import timezone

from surveys.models import Questionnaire
# Import directly from base to avoid circular imports
from feedback.models.base import Response

class CompletionTracker(models.Model):
    """
    Model for tracking completion of questionnaires
    """
    response = models.OneToOneField(Response, on_delete=models.CASCADE, related_name='completion_tracker')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    time_spent = models.DurationField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.FloatField(default=0)
    answers_required = models.PositiveIntegerField(default=0)
    answers_provided = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Completion Tracker'
        verbose_name_plural = 'Completion Trackers'

    def __str__(self):
        return f"Completion for {self.response}"

    def update_completion(self):
        """
        Update the completion percentage and status
        """
        # Count required questions
        required_questions = self.response.survey.questions.filter(required=True).count()
        self.answers_required = required_questions

        # Count provided answers
        self.answers_provided = self.response.answers.count()

        # Calculate completion percentage
        if self.answers_required > 0:
            self.completion_percentage = (self.answers_provided / self.answers_required) * 100
        else:
            self.completion_percentage = 100

        # Check if completed
        if self.completion_percentage >= 100 and not self.is_completed:
            self.mark_completed()

        self.save()

    def mark_completed(self):
        """
        Mark the response as completed
        """
        self.is_completed = True
        self.completed_at = timezone.now()

        # Calculate time spent
        if self.started_at:
            self.time_spent = self.completed_at - self.started_at

        # Also update the response
        self.response.completed_at = self.completed_at
        self.response.save(update_fields=['completed_at'])

        self.save()


class CompletionEvent(models.Model):
    """
    Model for tracking completion events
    """
    EVENT_TYPE_CHOICES = [
        ('start', 'Started'),
        ('answer', 'Answered Question'),
        ('navigation', 'Navigation'),
        ('timeout', 'Timeout'),
        ('completion', 'Completed'),
        ('abandonment', 'Abandoned'),
    ]

    tracker = models.ForeignKey(CompletionTracker, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    question = models.ForeignKey('surveys.Question', on_delete=models.SET_NULL, null=True, blank=True, related_name='completion_events')
    answer = models.ForeignKey('feedback.Answer', on_delete=models.SET_NULL, null=True, blank=True, related_name='completion_events')
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Completion Event'
        verbose_name_plural = 'Completion Events'

    def __str__(self):
        return f"{self.get_event_type_display()} at {self.timestamp}"
