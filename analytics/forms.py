from django import forms
from .models import Dashboard, Widget, Report

class DashboardForm(forms.ModelForm):
    class Meta:
        model = Dashboard
        fields = ['title', 'description', 'layout', 'is_public', 'organization']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class WidgetForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ['title', 'description', 'widget_type', 'data_source', 'position_x', 'position_y', 'width', 'height', 'config']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'config': forms.Textarea(attrs={'rows': 5, 'class': 'json-editor'}),
        }

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['title', 'description', 'report_format', 'surveys', 'responses', 'organization', 'filters']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'filters': forms.Textarea(attrs={'rows': 5, 'class': 'json-editor'}),
        }
