# Import the base models to avoid circular imports
from django.db import models
from django.conf import settings
from surveys.models import Questionnaire
from feedback.models import Response
from groups.models import Organization

# Dashboard and Widget models are now defined in analytics/models/dashboard.py


class Report(models.Model):
    """
    Model for analytics reports
    """
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    REPORT_TYPE_CHOICES = [
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Report'),
        ('comparative', 'Comparative Analysis'),
        ('trend', 'Trend Analysis'),
        ('custom', 'Custom Report'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default='summary')
    report_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    questionnaires = models.ManyToManyField(Questionnaire, blank=True, related_name='reports')
    responses = models.ManyToManyField(Response, blank=True, related_name='reports')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    filters = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'

    def __str__(self):
        return self.title
# AI models are now defined in analytics/models/base.py
