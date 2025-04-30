from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm
from users.models import User
from .models import AdminProfile

class AdminAuthenticationForm(AuthenticationForm):
    """
    Form for admin login
    """
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email or Username',
        'autocomplete': 'username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password',
        'autocomplete': 'current-password'
    }))
    
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_admin_user():
            raise forms.ValidationError(
                "This account does not have admin access.",
                code='no_admin_access',
            )

class AdminProfileForm(forms.ModelForm):
    """
    Form for admins to edit their profile
    """
    class Meta:
        model = AdminProfile
        fields = ['department', 'position', 'employee_id', 'admin_notes']
        widgets = {
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AdminUserForm(forms.ModelForm):
    """
    Form for admins to edit their user information
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'profile_image', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AdminPasswordChangeForm(PasswordChangeForm):
    """
    Form for admins to change their password
    """
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Current Password'
    }))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'New Password'
    }))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm New Password'
    }))

class AdminUserCreationForm(forms.ModelForm):
    """
    Form for creating new admin users
    """
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm Password'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit role choices to admin and staff
        self.fields['role'].choices = [
            ('admin', 'Administrator'),
            ('staff', 'Staff'),
        ]
        
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_staff = True
        if user.role == 'admin':
            user.is_superuser = True
        
        if commit:
            user.save()
            # Create admin profile
            AdminProfile.objects.create(user=user)
        
        return user
