from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from .models import User, UserProfile

class ClientAuthenticationForm(AuthenticationForm):
    """
    Form for client login
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
        if user.is_admin_user() and not user.is_client_user():
            raise forms.ValidationError(
                "Admin users should use the admin login page.",
                code='admin_user',
            )

class ClientUserForm(forms.ModelForm):
    """
    Form for clients to edit their basic information
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

class ClientProfileForm(forms.ModelForm):
    """
    Form for clients to edit their profile details
    """
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'date_of_birth',
            'address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'health_conditions', 'medications', 'allergies'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control'}),
            'health_conditions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'medications': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class ClientRegistrationForm(UserCreationForm):
    """
    Form for client registration
    """
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email'
    }))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm Password'
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'user'

        if commit:
            user.save()
            # Create client profile
            UserProfile.objects.create(user=user)

        return user

class ClientPasswordChangeForm(PasswordChangeForm):
    """
    Form for clients to change their password
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

# Keep this form for admin use in the admin panel
class UserEditForm(forms.ModelForm):
    """
    Form for admins to edit user details (kept for admin panel use)
    """
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'profile_image',
                 'phone_number', 'role', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'profile_image': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email field required
        self.fields['email'].required = True
