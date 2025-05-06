from django.db import models
from django.conf import settings
import uuid

class EmailLog(models.Model):
    """
    Model for logging emails sent by the system
    """
    EMAIL_TYPE_CHOICES = [
        ('high_risk', 'High Risk Notification'),
        ('report', 'Response Report'),
        ('bulk', 'Bulk Notification'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPE_CHOICES)
    subject = models.CharField(max_length=255)
    recipient_email = models.EmailField(null=True, blank=True)  # Make this field nullable
    sender_email = models.EmailField(default=settings.DEFAULT_FROM_EMAIL)
    template = models.CharField(max_length=255, null=True, blank=True)  # Make this field nullable
    context = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    response = models.ForeignKey('feedback.Response', on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    organization = models.ForeignKey('groups.Organization', on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_emails')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
        indexes = [
            models.Index(fields=['email_type'], name='fb_email_type_idx1'),
            models.Index(fields=['status'], name='fb_email_status_idx1'),
            models.Index(fields=['recipient_email'], name='fb_email_recipient_idx1'),
            models.Index(fields=['response'], name='fb_email_response_idx1'),
            models.Index(fields=['organization'], name='fb_email_org_idx1'),
            models.Index(fields=['created_at'], name='fb_email_created_at_idx1'),
        ]

    def __str__(self):
        return f"{self.get_email_type_display()} to {self.recipient_email} ({self.status})"



