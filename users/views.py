from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib import messages
from django.utils import timezone
from .models import User, UserProfile, ClientLoginHistory
from .forms import (
    ClientAuthenticationForm, ClientUserForm, ClientProfileForm,
    ClientRegistrationForm, ClientPasswordChangeForm, UserEditForm
)

def client_login(request):
    """
    Client login view
    """
    # Redirect if already logged in as client
    if request.user.is_authenticated and request.user.is_client_user():
        return redirect('client_dashboard')

    # Handle login form
    if request.method == 'POST':
        form = ClientAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Record login
            ClientLoginHistory.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                device_info={},
                session_id=request.session.session_key,
                success=True
            )

            # Update client profile
            if hasattr(user, 'profile'):
                user.profile.update_last_activity()
            else:
                # Create client profile if it doesn't exist
                profile = UserProfile.objects.create(user=user)
                profile.update_last_activity()

            # Redirect to next URL or dashboard
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('client_dashboard')
        else:
            # Record failed login attempt
            if 'username' in request.POST:
                try:
                    user = User.objects.get(username=request.POST['username'])
                    ClientLoginHistory.objects.create(
                        user=user,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT'),
                        device_info={},
                        success=False,
                        failure_reason='Invalid credentials'
                    )
                except User.DoesNotExist:
                    pass
    else:
        form = ClientAuthenticationForm()

    return render(request, 'users/login.html', {
        'form': form,
        'title': 'Client Login'
    })

def client_register(request):
    """
    Client registration view
    """
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('client_dashboard')

    # Handle registration form
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Log the user in
            login(request, user)

            # Record login
            ClientLoginHistory.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                device_info={},
                session_id=request.session.session_key,
                success=True
            )

            messages.success(request, 'Your account has been created successfully. Welcome!')
            return redirect('client_dashboard')
    else:
        form = ClientRegistrationForm()

    return render(request, 'users/register.html', {
        'form': form,
        'title': 'Client Registration'
    })

@login_required
def client_logout(request):
    """
    Client logout view
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('client_login')

@login_required
def client_dashboard(request):
    """
    Client dashboard view
    """
    # Check if user is client
    if request.user.is_admin_user() and not request.user.is_client_user():
        messages.error(request, 'Admin users should use the admin dashboard.')
        return redirect('admin_dashboard')

    # Get client profile
    client_profile = request.user.get_client_profile()
    if not client_profile:
        # Create client profile if it doesn't exist
        client_profile = UserProfile.objects.create(user=request.user)

    # Update last activity
    client_profile.update_last_activity()

    # Get recent login history
    login_history = ClientLoginHistory.objects.filter(
        user=request.user
    ).order_by('-login_time')[:5]

    return render(request, 'users/dashboard.html', {
        'client_profile': client_profile,
        'login_history': login_history,
    })

@login_required
def client_profile(request):
    """
    Client profile view
    """
    # Check if user is client
    if request.user.is_admin_user() and not request.user.is_client_user():
        messages.error(request, 'Admin users should use the admin profile page.')
        return redirect('admin_profile')

    # Get client profile
    client_profile = request.user.get_client_profile()
    if not client_profile:
        # Create client profile if it doesn't exist
        client_profile = UserProfile.objects.create(user=request.user)

    return render(request, 'users/profile.html', {
        'user': request.user,
        'profile': client_profile
    })

@login_required
def client_profile_edit(request):
    """
    Edit client profile
    """
    # Check if user is client
    if request.user.is_admin_user() and not request.user.is_client_user():
        messages.error(request, 'Admin users should use the admin profile page.')
        return redirect('admin_profile')

    # Get client profile
    client_profile = request.user.get_client_profile()
    if not client_profile:
        # Create client profile if it doesn't exist
        client_profile = UserProfile.objects.create(user=request.user)

    # Handle form submission
    if request.method == 'POST':
        user_form = ClientUserForm(request.POST, request.FILES, instance=request.user)
        profile_form = ClientProfileForm(request.POST, instance=client_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('client_profile')
    else:
        user_form = ClientUserForm(instance=request.user)
        profile_form = ClientProfileForm(instance=client_profile)

    return render(request, 'users/profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def client_change_password(request):
    """
    Change client password
    """
    # Check if user is client
    if request.user.is_admin_user() and not request.user.is_client_user():
        messages.error(request, 'Admin users should use the admin change password page.')
        return redirect('admin_change_password')

    # Handle form submission
    if request.method == 'POST':
        form = ClientPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update the session to prevent the user from being logged out
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('client_profile')
    else:
        form = ClientPasswordChangeForm(request.user)

    return render(request, 'users/change_password.html', {
        'form': form
    })

# Admin-related views (moved to accounts app)
# These are kept for backward compatibility but redirect to the new admin views

@login_required
def user_list(request):
    """
    Redirect to admin users view
    """
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, "You don't have permission to view this page.")
        return redirect('client_dashboard')

    messages.info(request, "This page has moved to the admin section.")
    return redirect('admin_users')

@login_required
def user_detail(request, pk):
    """
    Redirect to admin user edit view
    """
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, "You don't have permission to view this page.")
        return redirect('client_dashboard')

    messages.info(request, "This page has moved to the admin section.")
    return redirect('admin_edit_user', user_id=pk)

@login_required
def user_edit(request, pk):
    """
    Redirect to admin user edit view
    """
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, "You don't have permission to view this page.")
        return redirect('client_dashboard')

    messages.info(request, "This page has moved to the admin section.")
    return redirect('admin_edit_user', user_id=pk)
