"""
Models for the core app.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from groups.models import Organization

class EmailTemplate(models.Model):
    """
    Model for storing email templates
    """
    CATEGORY_CHOICES = [
        ('notification', 'Notification'),
        ('report', 'Report'),
        ('reminder', 'Reminder'),
        ('welcome', 'Welcome'),
        ('feedback', 'Feedback'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=255)
    message = models.TextField(help_text="Plain text message")
    html_content = models.TextField(blank=True, help_text="HTML content (optional)")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='notification')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='email_templates')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_email_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    variables = models.JSONField(default=dict, blank=True, help_text="Available variables for this template")

    class Meta:
        ordering = ['-is_default', 'name']
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # If this template is set as default, unset default for other templates in the same category
        if self.is_default:
            EmailTemplate.objects.filter(
                category=self.category,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)

        super().save(*args, **kwargs)


class EmailLog(models.Model):
    """
    Model for logging sent emails
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    subject = models.CharField(max_length=255)
    message = models.TextField()
    html_content = models.TextField(blank=True)
    from_email = models.EmailField()
    to_email = models.EmailField()
    cc_emails = models.TextField(blank=True, help_text="Comma-separated list of CC emails")
    bcc_emails = models.TextField(blank=True, help_text="Comma-separated list of BCC emails")
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_emails')
    response = models.ForeignKey('feedback.Response', on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')
    analysis = models.ForeignKey('feedback.AIAnalysis', on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_emails')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'

    def __str__(self):
        return f"{self.subject} - {self.to_email}"

    def mark_as_sent(self):
        """
        Mark the email as sent
        """
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])

    def mark_as_failed(self, error_message):
        """
        Mark the email as failed
        """
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])
