from django import forms
from .models import Assessment, Consultation

class AssessmentForm(forms.ModelForm):
    """
    Form for creating and updating assessments
    """
    class Meta:
        model = Assessment
        fields = [
            'response', 'status', 'notes', 'risk_factors', 
            'strengths', 'concerns', 'consultation_recommended', 
            'consultation_notes', 'consultation_urgency',
            'follow_up_date', 'follow_up_notes'
        ]
        widgets = {
            'risk_factors': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 4}),
            'strengths': forms.Textarea(attrs={'rows': 4}),
            'concerns': forms.Textarea(attrs={'rows': 4}),
            'consultation_notes': forms.Textarea(attrs={'rows': 4}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}),
            'follow_up_notes': forms.Textarea(attrs={'rows': 4}),
        }

class ConsultationForm(forms.ModelForm):
    """
    Form for creating and updating consultations
    """
    class Meta:
        model = Consultation
        fields = [
            'consultant', 'scheduled_date', 'status', 
            'notes', 'outcome', 'follow_up_required'
        ]
        widgets = {
            'scheduled_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
            'outcome': forms.Textarea(attrs={'rows': 4}),
        }
