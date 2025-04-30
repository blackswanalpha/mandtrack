from django.db import models
from django.conf import settings
from surveys.models import Questionnaire
from feedback.models import Response
from groups.models import Organization

class Dashboard(models.Model):
    """
    Model for custom dashboards
    """
    LAYOUT_CHOICES = [
        ('1_column', 'Single Column'),
        ('2_columns', 'Two Columns'),
        ('3_columns', 'Three Columns'),
        ('2_1', 'Two-One Split'),
        ('1_2', 'One-Two Split'),
        ('custom', 'Custom Layout'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='2_columns')
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboards')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='dashboards', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'

    def __str__(self):
        return self.title

    def get_widget_count(self):
        return self.widgets.count()


class Widget(models.Model):
    """
    Model for dashboard widgets
    """
    TYPE_CHOICES = [
        ('chart_line', 'Line Chart'),
        ('chart_bar', 'Bar Chart'),
        ('chart_pie', 'Pie Chart'),
        ('chart_doughnut', 'Doughnut Chart'),
        ('chart_radar', 'Radar Chart'),
        ('table', 'Table'),
        ('metric', 'Metric'),
        ('text', 'Text'),
        ('map', 'Map'),
        ('heatmap', 'Heatmap'),
    ]

    DATA_SOURCE_CHOICES = [
        ('questionnaire', 'Questionnaire Data'),
        ('response', 'Response Data'),
        ('user', 'User Data'),
        ('organization', 'Organization Data'),
        ('custom', 'Custom Data'),
    ]

    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    widget_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    data_source = models.CharField(max_length=20, choices=DATA_SOURCE_CHOICES)
    data_filter = models.JSONField(default=dict, blank=True)
    position_x = models.PositiveIntegerField(default=0)
    position_y = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=1)
    height = models.PositiveIntegerField(default=1)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['dashboard', 'position_y', 'position_x']
        verbose_name = 'Widget'
        verbose_name_plural = 'Widgets'

    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"


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

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
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
