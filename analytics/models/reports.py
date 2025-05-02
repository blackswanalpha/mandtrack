from django.db import models
from django.conf import settings
from django.utils import timezone

from surveys.models import Questionnaire
from groups.models import Organization

class Report(models.Model):
    """
    Model for storing generated reports
    """
    REPORT_TYPE_CHOICES = [
        ('response_summary', 'Response Summary'),
        ('trend_analysis', 'Trend Analysis'),
        ('ai_insights', 'AI Insights'),
        ('demographic_analysis', 'Demographic Analysis'),
        ('risk_assessment', 'Risk Assessment'),
        ('custom_export', 'Custom Export'),
    ]

    REPORT_FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('html', 'HTML'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    report_format = models.CharField(max_length=20, choices=REPORT_FORMAT_CHOICES)
    parameters = models.JSONField(default=dict, blank=True, help_text="Parameters used to generate the report")
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    pdf_file = models.FileField(upload_to='reports/pdf/', null=True, blank=True, help_text="PDF version of the report")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('analytics:report_detail', kwargs={'pk': self.pk})

    def mark_as_processing(self):
        """
        Mark the report as processing
        """
        self.status = 'processing'
        self.save(update_fields=['status', 'updated_at'])

    def mark_as_completed(self, file=None):
        """
        Mark the report as completed
        """
        self.status = 'completed'
        if file:
            self.file = file
        self.save(update_fields=['status', 'file', 'updated_at'])

    def mark_as_failed(self, error_message):
        """
        Mark the report as failed
        """
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message', 'updated_at'])


class ReportSchedule(models.Model):
    """
    Model for scheduling recurring reports
    """
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=50, choices=Report.REPORT_TYPE_CHOICES)
    report_format = models.CharField(max_length=20, choices=Report.REPORT_FORMAT_CHOICES)
    parameters = models.JSONField(default=dict, blank=True, help_text="Parameters used to generate the report")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    next_run = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.SET_NULL, null=True, blank=True, related_name='report_schedules')
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name='report_schedules')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_report_schedules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_run']
        verbose_name = 'Report Schedule'
        verbose_name_plural = 'Report Schedules'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('analytics:report_schedule_detail', kwargs={'pk': self.pk})

    def update_next_run(self):
        """
        Update the next run time based on the frequency
        """
        now = timezone.now()

        if self.frequency == 'daily':
            self.next_run = now + timezone.timedelta(days=1)
        elif self.frequency == 'weekly':
            self.next_run = now + timezone.timedelta(weeks=1)
        elif self.frequency == 'monthly':
            # Add 30 days as an approximation
            self.next_run = now + timezone.timedelta(days=30)
        elif self.frequency == 'quarterly':
            # Add 90 days as an approximation
            self.next_run = now + timezone.timedelta(days=90)

        self.save(update_fields=['next_run', 'updated_at'])

    def generate_report(self):
        """
        Generate a report based on this schedule
        """
        report = Report.objects.create(
            title=f"{self.name} - {timezone.now().strftime('%Y-%m-%d')}",
            description=self.description,
            report_type=self.report_type,
            report_format=self.report_format,
            parameters=self.parameters,
            questionnaire=self.questionnaire,
            organization=self.organization,
            created_by=self.created_by,
            status='pending'
        )

        # Update the next run time
        self.update_next_run()

        return report
