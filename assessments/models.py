from django.db import models
from django.conf import settings
from feedback.models import Response
import uuid

class Assessment(models.Model):
    """
    Model for patient assessments based on questionnaire responses
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    CONSULTATION_CHOICES = [
        ('not_required', 'Not Required'),
        ('recommended', 'Recommended'),
        ('required', 'Required'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response = models.OneToOneField(Response, on_delete=models.CASCADE, related_name='assessment')
    assessor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='conducted_assessments')
    assessment_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Assessment details
    notes = models.TextField(blank=True)
    risk_factors = models.JSONField(default=dict, blank=True)
    strengths = models.TextField(blank=True)
    concerns = models.TextField(blank=True)

    # Consultation recommendation
    consultation_recommended = models.CharField(max_length=20, choices=CONSULTATION_CHOICES, default='not_required')
    consultation_notes = models.TextField(blank=True)
    consultation_urgency = models.PositiveSmallIntegerField(default=0, help_text="1-10 scale, 10 being most urgent")

    # Follow-up
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-assessment_date']
        verbose_name = 'Assessment'
        verbose_name_plural = 'Assessments'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['consultation_recommended']),
            models.Index(fields=['assessment_date']),
        ]

    def __str__(self):
        return f"Assessment for {self.response.patient_identifier or 'Anonymous'} ({self.id})"

    def get_risk_level(self):
        """Get the risk level from the associated response"""
        return self.response.risk_level if self.response else 'unknown'

    def needs_consultation(self):
        """Check if consultation is recommended or required"""
        return self.consultation_recommended in ['recommended', 'required']

    def is_high_risk(self):
        """Check if this is a high-risk assessment"""
        return self.get_risk_level() in ['high', 'critical']


class Consultation(models.Model):
    """
    Model for consultations scheduled based on assessments
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='consultations')
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='consultations')
    scheduled_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    outcome = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date']
        verbose_name = 'Consultation'
        verbose_name_plural = 'Consultations'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_date']),
        ]

    def __str__(self):
        return f"Consultation for {self.assessment.response.patient_identifier or 'Anonymous'} on {self.scheduled_date.strftime('%Y-%m-%d')}"
