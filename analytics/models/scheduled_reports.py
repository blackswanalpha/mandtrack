"""
Models for scheduled reports.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class ScheduledReport(models.Model):
    """
    Model for scheduled reports
    """
    REPORT_TYPE_CHOICES = (
        ('clinical', 'Clinical Report'),
        ('dashboard', 'Dashboard Report'),
        ('batch', 'Batch Report'),
        ('comparative', 'Comparative Report'),
    )
    
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    )
    
    DAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    parameters = models.JSONField(default=dict, help_text="Parameters for the report")
    schedule = models.JSONField(default=dict, help_text="Schedule information (frequency, day, time)")
    recipient_email = models.EmailField()
    is_active = models.BooleanField(default=True)
    last_sent = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Scheduled Report"
        verbose_name_plural = "Scheduled Reports"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.recipient_email}"
    
    def is_due(self):
        """
        Check if the report is due to be sent
        """
        if not self.is_active:
            return False
        
        # If never sent, it's due
        if not self.last_sent:
            return True
        
        now = timezone.now()
        frequency = self.schedule.get('frequency', 'daily')
        
        if frequency == 'daily':
            # Check if it's been at least 24 hours since last sent
            return (now - self.last_sent).days >= 1
        
        elif frequency == 'weekly':
            # Check if it's been at least 7 days since last sent and it's the right day of the week
            if (now - self.last_sent).days < 7:
                return False
            
            day = self.schedule.get('day', 0)  # Default to Monday
            return now.weekday() == day
        
        elif frequency == 'monthly':
            # Check if it's been at least 28 days since last sent and it's the right day of the month
            if (now - self.last_sent).days < 28:
                return False
            
            day = self.schedule.get('day', 1)  # Default to 1st of the month
            return now.day == day
        
        return False
    
    def mark_as_sent(self):
        """
        Mark the report as sent
        """
        self.last_sent = timezone.now()
        self.save(update_fields=['last_sent'])
    
    def get_next_run_time(self):
        """
        Get the next time the report will run
        """
        if not self.is_active:
            return None
        
        now = timezone.now()
        frequency = self.schedule.get('frequency', 'daily')
        time_str = self.schedule.get('time', '08:00')
        
        # Parse time
        try:
            hour, minute = map(int, time_str.split(':'))
        except (ValueError, TypeError):
            hour, minute = 8, 0
        
        if frequency == 'daily':
            # Next run is today at the specified time, or tomorrow if that time has passed
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run = next_run + timezone.timedelta(days=1)
        
        elif frequency == 'weekly':
            # Next run is on the specified day of the week at the specified time
            day = self.schedule.get('day', 0)  # Default to Monday
            days_ahead = day - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timezone.timedelta(days=days_ahead)
        
        elif frequency == 'monthly':
            # Next run is on the specified day of the month at the specified time
            day = self.schedule.get('day', 1)  # Default to 1st of the month
            
            # Calculate next month's date
            if now.day < day:
                # Target day is later this month
                next_run = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
            else:
                # Target day has passed this month, go to next month
                if now.month == 12:
                    next_run = now.replace(year=now.year+1, month=1, day=day, hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    next_run = now.replace(month=now.month+1, day=day, hour=hour, minute=minute, second=0, microsecond=0)
        
        else:
            return None
        
        return next_run
