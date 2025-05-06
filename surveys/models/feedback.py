"""
Models for storing user feedback on enhanced scoring.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

class EnhancedScoringFeedback(models.Model):
    """
    Model for storing user feedback on enhanced scoring
    """
    ACCURACY_CHOICES = [
        (1, 'Not accurate'),
        (2, 'Somewhat accurate'),
        (3, 'Moderately accurate'),
        (4, 'Very accurate'),
        (5, 'Extremely accurate'),
    ]
    
    USEFULNESS_CHOICES = [
        (1, 'Not useful'),
        (2, 'Somewhat useful'),
        (3, 'Moderately useful'),
        (4, 'Very useful'),
        (5, 'Extremely useful'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    # Use string reference to avoid circular imports
    response = models.ForeignKey('feedback.Response', on_delete=models.CASCADE, related_name='scoring_feedback')
    scoring_system = models.ForeignKey('surveys.ScoringSystem', on_delete=models.CASCADE, related_name='user_feedback')
    accuracy_rating = models.PositiveSmallIntegerField(choices=ACCURACY_CHOICES)
    usefulness_rating = models.PositiveSmallIntegerField(choices=USEFULNESS_CHOICES)
    preferred_features = models.JSONField(default=list)
    feedback_text = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Enhanced Scoring Feedback'
        verbose_name_plural = 'Enhanced Scoring Feedback'
        unique_together = ('response', 'scoring_system')
        indexes = [
            models.Index(fields=['response']),
            models.Index(fields=['scoring_system']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Feedback for response {self.response_id} on {self.scoring_system}"
