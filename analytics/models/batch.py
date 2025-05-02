from django.db import models
from django.conf import settings
from django.utils import timezone
from feedback.models import Response as SurveyResponse

class BatchAnalysisJob(models.Model):
    """
    Model for batch analysis jobs
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    ANALYSIS_TYPE_CHOICES = [
        ('comprehensive', 'Comprehensive Analysis'),
        ('insights', 'Key Insights'),
        ('sentiment', 'Sentiment Analysis'),
        ('themes', 'Theme Identification'),
        ('patterns', 'Pattern Recognition'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPE_CHOICES, default='comprehensive')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    responses = models.ManyToManyField(SurveyResponse, related_name='batch_jobs')
    total_responses = models.IntegerField(default=0)
    processed_responses = models.IntegerField(default=0)
    skipped_responses = models.IntegerField(default=0)
    error_responses = models.IntegerField(default=0)
    error_details = models.JSONField(default=list)
    aggregate_insights = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_batch_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Batch Analysis Job'
        verbose_name_plural = 'Batch Analysis Jobs'
    
    def __str__(self):
        return self.name
    
    @property
    def progress_percentage(self):
        """
        Calculate the progress percentage
        """
        if self.total_responses == 0:
            return 0
        return int((self.processed_responses / self.total_responses) * 100)
    
    @property
    def duration(self):
        """
        Calculate the duration of the job
        """
        if not self.started_at:
            return None
        
        end_time = self.completed_at or timezone.now()
        duration = end_time - self.started_at
        
        # Format as hours, minutes, seconds
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def cancel(self):
        """
        Cancel the job
        """
        if self.status in ['pending', 'processing']:
            self.status = 'cancelled'
            self.completed_at = timezone.now()
            self.save()
            return True
        return False
