from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.forms import PasswordChangeForm

from users.models import User
from .models import AdminProfile, AdminLoginHistory
from .forms import (
    AdminAuthenticationForm, AdminProfileForm, AdminUserForm,
    AdminPasswordChangeForm, AdminUserCreationForm
)

def admin_login(request):
    """
    Admin login view
    """
    # Redirect if already logged in as admin
    if request.user.is_authenticated and request.user.is_admin_user():
        return redirect('admin_dashboard')

    # Handle login form
    if request.method == 'POST':
        form = AdminAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Record login
            AdminLoginHistory.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                session_id=request.session.session_key,
                success=True
            )

            # Update admin profile
            if hasattr(user, 'admin_profile'):
                user.admin_profile.last_login_ip = request.META.get('REMOTE_ADDR')
                user.admin_profile.save(update_fields=['last_login_ip', 'updated_at'])
            else:
                # Create admin profile if it doesn't exist
                AdminProfile.objects.create(
                    user=user,
                    last_login_ip=request.META.get('REMOTE_ADDR')
                )

            # Redirect to next URL or dashboard/admin
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('admin_dashboard')
        else:
            # Add error message for toast notification
            messages.error(request, 'Invalid username or password. Please try again.')

            # Record failed login attempt
            if 'username' in request.POST:
                try:
                    user = User.objects.get(username=request.POST['username'])
                    AdminLoginHistory.objects.create(
                        user=user,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT'),
                        success=False,
                        failure_reason='Invalid credentials'
                    )
                except User.DoesNotExist:
                    pass
    else:
        form = AdminAuthenticationForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'title': 'Admin Login'
    })

@login_required
def admin_logout(request):
    """
    Admin logout view
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('admin_login')

@login_required
def admin_dashboard(request):
    """
    Admin dashboard view
    """
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access the admin dashboard.')
        return redirect('client_dashboard')

    # Get admin profile
    admin_profile = request.user.get_admin_profile()
    if not admin_profile:
        # Create admin profile if it doesn't exist
        admin_profile = AdminProfile.objects.create(user=request.user)

    # Get recent login history
    login_history = AdminLoginHistory.objects.filter(
        user=request.user
    ).order_by('-login_time')[:5]

    # Get questionnaires count
    try:
        from surveys.models import Questionnaire
        questionnaires_count = Questionnaire.objects.count()
    except:
        questionnaires_count = 0

    # Get responses count
    try:
        from feedback.models import Response
        responses_count = Response.objects.count()
    except:
        responses_count = 0

    # Get users count
    from users.models import User
    admin_users_count = User.objects.filter(role__in=['admin', 'staff']).count()
    client_users_count = User.objects.filter(role='client').count()

    return render(request, 'dashboard/admin_dashboard.html', {
        'admin_profile': admin_profile,
        'login_history': login_history,
        'questionnaires_count': questionnaires_count,
        'responses_count': responses_count,
        'admin_users_count': admin_users_count,
        'client_users_count': client_users_count,
    })

@login_required
def admin_profile(request):
    """
    Admin profile view
    """
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('client_profile')

    # Get admin profile
    admin_profile = request.user.get_admin_profile()
    if not admin_profile:
        # Create admin profile if it doesn't exist
        admin_profile = AdminProfile.objects.create(user=request.user)

    # Handle form submission
    if request.method == 'POST':
        user_form = AdminUserForm(request.POST, request.FILES, instance=request.user)
        profile_form = AdminProfileForm(request.POST, instance=admin_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('admin_profile')
    else:
        user_form = AdminUserForm(instance=request.user)
        profile_form = AdminProfileForm(instance=admin_profile)

    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'admin_profile': admin_profile,
    })

@login_required
def admin_change_password(request):
    """
    Admin change password view
    """
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('client_change_password')

    # Handle form submission
    if request.method == 'POST':
        form = AdminPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, 'Your password has been updated successfully.')
            return redirect('admin_profile')
    else:
        form = AdminPasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {
        'form': form,
    })

@login_required
def admin_users(request):
    """
    Admin users management view
    """
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('client_dashboard')

    # Get all admin users
    admin_users = User.objects.filter(
        role__in=['admin', 'staff']
    ).order_by('-date_joined')

    return render(request, 'accounts/users.html', {
        'admin_users': admin_users,
    })

@login_required
def admin_create_user(request):
    """
    Create new admin user view
    """
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('client_dashboard')

    # Handle form submission
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Admin user {user.username} has been created successfully.')
            return redirect('admin_users')
    else:
        form = AdminUserCreationForm()

    return render(request, 'accounts/create_user.html', {
        'form': form,
    })

@login_required
def admin_edit_user(request, user_id):
    """
    Edit admin user view
    """
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('client_dashboard')

    # Get user
    user = get_object_or_404(User, id=user_id)

    # Check if user is admin
    if not user.is_admin_user():
        messages.error(request, 'This user is not an admin user.')
        return redirect('admin_users')

    # Get admin profile
    admin_profile = user.get_admin_profile()
    if not admin_profile:
        # Create admin profile if it doesn't exist
        admin_profile = AdminProfile.objects.create(user=user)

    # Handle form submission
    if request.method == 'POST':
        user_form = AdminUserForm(request.POST, request.FILES, instance=user)
        profile_form = AdminProfileForm(request.POST, instance=admin_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, f'User {user.username} has been updated successfully.')
            return redirect('admin_users')
    else:
        user_form = AdminUserForm(instance=user)
        profile_form = AdminProfileForm(instance=admin_profile)

    return render(request, 'accounts/edit_user.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'admin_user': user,
    })
