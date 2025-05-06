"""
Models for the email system app.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
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
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='email_system_templates')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='email_system_templates')
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
    response = models.ForeignKey('feedback.Response', on_delete=models.SET_NULL, null=True, blank=True, related_name='email_system_emails')
    analysis = models.ForeignKey('feedback.AIAnalysis', on_delete=models.SET_NULL, null=True, blank=True, related_name='email_system_emails')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='email_system_sent_emails')
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


class ScheduledEmail(models.Model):
    """
    Model for scheduling emails to be sent at a later time
    """
    FREQUENCY_CHOICES = [
        ('once', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('error', 'Error'),
    ]

    WEEKDAY_CHOICES = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]

    # Basic information
    name = models.CharField(max_length=255, help_text="Name of the scheduled email")
    description = models.TextField(blank=True, help_text="Description of the scheduled email")

    # Email content
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name='scheduled_emails')
    subject_override = models.CharField(max_length=255, blank=True, help_text="Override the template subject (optional)")
    message_override = models.TextField(blank=True, help_text="Override the template message (optional)")
    html_content_override = models.TextField(blank=True, help_text="Override the template HTML content (optional)")

    # Recipients
    to_email = models.EmailField(help_text="Primary recipient email")
    cc_emails = models.TextField(blank=True, help_text="Comma-separated list of CC emails")
    bcc_emails = models.TextField(blank=True, help_text="Comma-separated list of BCC emails")

    # Scheduling
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='once')
    scheduled_time = models.DateTimeField(help_text="When to send the email")
    end_date = models.DateTimeField(null=True, blank=True, help_text="When to stop sending recurring emails (optional)")

    # Recurring options
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, null=True, blank=True, help_text="Day of the week for weekly emails")
    day_of_month = models.IntegerField(null=True, blank=True, help_text="Day of the month for monthly emails (1-31)")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    last_sent = models.DateTimeField(null=True, blank=True, help_text="When the email was last sent")
    next_scheduled = models.DateTimeField(null=True, blank=True, help_text="When the next email is scheduled to be sent")
    error_message = models.TextField(blank=True, help_text="Error message if the email failed to send")

    # Related objects
    response = models.ForeignKey('feedback.Response', on_delete=models.SET_NULL, null=True, blank=True, related_name='scheduled_emails')
    analysis = models.ForeignKey('feedback.AIAnalysis', on_delete=models.SET_NULL, null=True, blank=True, related_name='scheduled_emails')

    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_scheduled_emails')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Context data
    context_data = models.JSONField(default=dict, blank=True, help_text="Additional context data for template rendering")

    class Meta:
        ordering = ['scheduled_time', 'name']
        verbose_name = 'Scheduled Email'
        verbose_name_plural = 'Scheduled Emails'
        indexes = [
            models.Index(fields=['status', 'next_scheduled']),
            models.Index(fields=['frequency']),
        ]

    def __str__(self):
        return f"{self.name} - {self.to_email} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Set next_scheduled based on scheduled_time for new records
        if not self.pk and not self.next_scheduled:
            self.next_scheduled = self.scheduled_time

        super().save(*args, **kwargs)

    def cancel(self):
        """
        Cancel the scheduled email
        """
        self.status = 'cancelled'
        self.save(update_fields=['status'])

    def mark_as_completed(self):
        """
        Mark the scheduled email as completed
        """
        self.status = 'completed'
        self.last_sent = timezone.now()
        self.save(update_fields=['status', 'last_sent'])

    def mark_as_error(self, error_message):
        """
        Mark the scheduled email as error
        """
        self.status = 'error'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])

    def calculate_next_scheduled(self):
        """
        Calculate the next scheduled time based on frequency
        """
        if self.frequency == 'once':
            return None

        now = timezone.now()
        last_sent = self.last_sent or now

        if self.frequency == 'daily':
            next_scheduled = last_sent + timezone.timedelta(days=1)
        elif self.frequency == 'weekly':
            next_scheduled = last_sent + timezone.timedelta(weeks=1)
        elif self.frequency == 'monthly':
            # Add one month (approximately)
            if last_sent.month == 12:
                next_month = 1
                next_year = last_sent.year + 1
            else:
                next_month = last_sent.month + 1
                next_year = last_sent.year

            # Handle day of month (e.g., 31st of month)
            day = min(last_sent.day, [31, 29 if (next_year % 4 == 0 and (next_year % 100 != 0 or next_year % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][next_month - 1])

            next_scheduled = last_sent.replace(year=next_year, month=next_month, day=day)
        elif self.frequency == 'quarterly':
            # Add three months
            month = last_sent.month
            year = last_sent.year

            month += 3
            if month > 12:
                month -= 12
                year += 1

            # Handle day of month
            day = min(last_sent.day, [31, 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])

            next_scheduled = last_sent.replace(year=year, month=month, day=day)
        elif self.frequency == 'yearly':
            next_scheduled = last_sent.replace(year=last_sent.year + 1)
        else:
            return None

        # Check if we've passed the end date
        if self.end_date and next_scheduled > self.end_date:
            return None

        return next_scheduled

    def update_next_scheduled(self):
        """
        Update the next scheduled time
        """
        next_scheduled = self.calculate_next_scheduled()

        if next_scheduled:
            self.next_scheduled = next_scheduled
            self.save(update_fields=['next_scheduled'])
        else:
            self.status = 'completed'
            self.save(update_fields=['status', 'next_scheduled'])

        return next_scheduled
