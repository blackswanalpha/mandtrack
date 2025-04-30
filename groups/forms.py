from django import forms
from .models import Organization, OrganizationMember

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'description', 'type', 'website', 'email', 'phone', 'address', 'logo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class OrganizationMemberForm(forms.ModelForm):
    class Meta:
        model = OrganizationMember
        fields = ['user', 'role', 'title', 'department', 'is_active']
