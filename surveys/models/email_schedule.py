from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import json

User = get_user_model()

class EmailTemplate(models.Model):
    """
    Model for email templates
    """
    CATEGORY_CHOICES = (
        ('notification', 'Notification'),
        ('reminder', 'Reminder'),
        ('report', 'Report'),
        ('welcome', 'Welcome'),
        ('confirmation', 'Confirmation'),
        ('invitation', 'Invitation'),
        ('other', 'Other'),
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='notification')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    html_content = models.TextField(blank=True)
    variables = models.JSONField(default=list, blank=True,
                               help_text="List of available template variables")

    # Configuration
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    # Ownership
    organization = models.ForeignKey('groups.Organization', on_delete=models.CASCADE,
                                   related_name='email_templates', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_email_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'

    def __str__(self):
        return self.name

class EmailSchedule(models.Model):
    """
    Model for scheduling emails
    """
    FREQUENCY_CHOICES = (
        ('one_time', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('custom', 'Custom'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    # Email details
    template = models.ForeignKey('surveys.EmailTemplate', on_delete=models.CASCADE, related_name='schedules')
    subject_override = models.CharField(max_length=255, blank=True, null=True,
                                       help_text="Override the template subject (optional)")
    recipient_email = models.EmailField(blank=True, null=True, help_text="Email address of the recipient (for single recipient)")
    recipient_name = models.CharField(max_length=255, blank=True, null=True,
                                     help_text="Name of the recipient (optional)")

    # Bulk email options
    is_bulk = models.BooleanField(default=False, help_text="Whether this is a bulk email to multiple recipients")
    email_type = models.CharField(max_length=20, blank=True, null=True, choices=(
        ('high_risk', 'High Risk Notification'),
        ('report', 'Member Reports'),
        ('summary', 'Organization Summary'),
    ), help_text="Type of bulk email to send")
    organization = models.ForeignKey('groups.Organization', on_delete=models.CASCADE,
                                    related_name='email_schedules', null=True, blank=True,
                                    help_text="Organization for bulk emails")

    # Schedule details
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='one_time')
    scheduled_time = models.DateTimeField(help_text="When to send the email")
    end_date = models.DateTimeField(blank=True, null=True,
                                   help_text="End date for recurring emails (optional)")

    # For recurring emails with custom frequency
    custom_days = models.CharField(max_length=100, blank=True, null=True,
                                  help_text="JSON list of days for custom frequency (e.g., [0,3,6] for Sunday, Wednesday, Saturday)")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    last_sent = models.DateTimeField(blank=True, null=True)
    next_send = models.DateTimeField(blank=True, null=True)

    # Related object (optional)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    # Context variables
    context_data = models.JSONField(default=dict, blank=True,
                                   help_text="JSON data for template variables")

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_schedules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_time']
        verbose_name = 'Email Schedule'
        verbose_name_plural = 'Email Schedules'

    def __str__(self):
        return f"Email to {self.recipient_email} ({self.get_frequency_display()}) - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Set next_send based on frequency and scheduled_time
        if not self.next_send or self.next_send < timezone.now():
            self.next_send = self.scheduled_time

        super().save(*args, **kwargs)

    def get_custom_days(self):
        """
        Get custom days as a list of integers
        """
        if not self.custom_days:
            return []

        try:
            return json.loads(self.custom_days)
        except json.JSONDecodeError:
            return []

    def set_custom_days(self, days_list):
        """
        Set custom days from a list of integers
        """
        self.custom_days = json.dumps(days_list)

    def calculate_next_send(self):
        """
        Calculate the next send time based on frequency
        """
        if self.status != 'pending':
            return None

        now = timezone.now()

        if self.frequency == 'one_time':
            # For one-time emails, next_send is the scheduled_time
            if self.scheduled_time > now:
                return self.scheduled_time
            return None

        # For recurring emails
        if self.end_date and now > self.end_date:
            # If end date has passed, no more emails
            return None

        # Start from last sent or scheduled time
        base_time = self.last_sent or self.scheduled_time

        if self.frequency == 'daily':
            next_time = base_time + timezone.timedelta(days=1)
        elif self.frequency == 'weekly':
            next_time = base_time + timezone.timedelta(weeks=1)
        elif self.frequency == 'monthly':
            # Add one month (approximately)
            next_month = base_time.month + 1
            next_year = base_time.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            next_time = base_time.replace(year=next_year, month=next_month)
        elif self.frequency == 'quarterly':
            # Add three months (approximately)
            next_month = base_time.month + 3
            next_year = base_time.year
            if next_month > 12:
                next_month = next_month - 12
                next_year += 1
            next_time = base_time.replace(year=next_year, month=next_month)
        elif self.frequency == 'custom':
            # Custom frequency based on specific days of the week
            custom_days = self.get_custom_days()
            if not custom_days:
                return None

            # Find the next day in the custom days list
            current_day = base_time.weekday()
            next_day = None

            # Convert to Python's weekday format (0-6, Monday-Sunday)
            custom_days = [(d - 1) % 7 for d in custom_days]  # Convert from Sunday=0 to Monday=0

            for day in sorted(custom_days):
                if day > current_day:
                    next_day = day
                    break

            if next_day is None and custom_days:
                # If no day found, use the first day in the next week
                next_day = custom_days[0]
                days_ahead = 7 - current_day + next_day
            else:
                days_ahead = next_day - current_day

            next_time = base_time + timezone.timedelta(days=days_ahead)
        else:
            return None

        # Ensure next_time is in the future
        if next_time <= now:
            return self.calculate_next_send()

        # Check if next_time is after end_date
        if self.end_date and next_time > self.end_date:
            return None

        return next_time

    def mark_as_sent(self):
        """
        Mark the email as sent and calculate the next send time
        """
        self.status = 'sent' if self.frequency == 'one_time' else 'pending'
        self.last_sent = timezone.now()
        self.next_send = self.calculate_next_send()

        if not self.next_send:
            self.status = 'sent'

        self.save()

    def cancel(self):
        """
        Cancel the email schedule
        """
        self.status = 'cancelled'
        self.next_send = None
        self.save()


class EmailLog(models.Model):
    """
    Model for tracking email sending
    """
    template = models.ForeignKey('surveys.EmailTemplate', on_delete=models.CASCADE, related_name='logs')
    recipient_email = models.EmailField(null=True, blank=True)  # Made nullable
    subject = models.CharField(max_length=255)
    sent_at = models.DateTimeField()

    # Email content and context
    content = models.TextField(blank=True, null=True)
    context = models.JSONField(default=dict, blank=True)

    # Tracking data
    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(blank=True, null=True)
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(blank=True, null=True)

    # Related schedule (optional)
    schedule = models.ForeignKey(EmailSchedule, on_delete=models.SET_NULL, blank=True, null=True, related_name='logs')

    # Related object (optional)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    # Status and error information
    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    error_message = models.TextField(blank=True, null=True)

    # Tracking ID
    tracking_id = models.CharField(max_length=100, blank=True, null=True, unique=True)

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'

    def __str__(self):
        return f"Email to {self.recipient_email} - {self.sent_at}"

    def mark_as_opened(self):
        """
        Mark the email as opened
        """
        self.opened = True
        if not self.opened_at:
            self.opened_at = timezone.now()
        self.save()

    def mark_as_clicked(self):
        """
        Mark the email as clicked
        """
        self.clicked = True
        if not self.clicked_at:
            self.clicked_at = timezone.now()
        self.save()
