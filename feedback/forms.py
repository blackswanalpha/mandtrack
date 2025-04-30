from django import forms
from .models import SurveyResponse, Answer, AnalysisResult

class SurveyResponseForm(forms.ModelForm):
    class Meta:
        model = SurveyResponse
        fields = ['respondent_name', 'respondent_email']

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text_answer', 'selected_choice', 'numeric_value', 'date_value', 'time_value', 'file_upload']
        widgets = {
            'text_answer': forms.Textarea(attrs={'rows': 3}),
            'date_value': forms.DateInput(attrs={'type': 'date'}),
            'time_value': forms.TimeInput(attrs={'type': 'time'}),
        }

class AnalysisResultForm(forms.ModelForm):
    class Meta:
        model = AnalysisResult
        fields = ['summary', 'detailed_analysis', 'recommendations']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}),
            'detailed_analysis': forms.Textarea(attrs={'rows': 5}),
            'recommendations': forms.Textarea(attrs={'rows': 3}),
        }
