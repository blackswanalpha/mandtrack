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
    Admin dashboard view with sample data
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

    # Generate sample data for dashboard
    import json
    import random
    from datetime import datetime, timedelta

    # Sample data for charts
    trend_data = {
        'labels': [],
        'data': [],
        'colors': []
    }

    # Generate sample trend data for the last 30 days
    today = datetime.now().date()
    for i in range(30):
        date = today - timedelta(days=30-i)
        trend_data['labels'].append(date.strftime('%b %d'))
        trend_data['data'].append(random.randint(5, 25))
        trend_data['colors'].append('rgba(54, 162, 235, 0.7)')

    # Sample gender distribution data
    gender_data = {
        'labels': ['Male', 'Female', 'Non-binary', 'Prefer Not To Say'],
        'data': [40, 45, 10, 5],
        'colors': [
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 99, 132, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)'
        ]
    }

    # Sample age distribution data
    age_data = {
        'labels': ['Under 18', '18-24', '25-34', '35-44', '45-54', '55-64', '65+'],
        'data': [5, 15, 25, 20, 15, 12, 8],
        'colors': ['rgba(54, 162, 235, 0.7)'] * 7
    }

    # Sample device distribution data
    device_data = {
        'labels': ['Desktop', 'Mobile', 'Tablet'],
        'data': [40, 45, 15],
        'colors': [
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 99, 132, 0.7)',
            'rgba(255, 206, 86, 0.7)'
        ]
    }

    # Sample risk distribution data
    risk_data = {
        'labels': ['Low', 'Medium', 'High', 'Critical'],
        'data': [45, 30, 15, 10],
        'colors': [
            'rgba(75, 192, 192, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(255, 159, 64, 0.7)',
            'rgba(255, 99, 132, 0.7)'
        ]
    }

    # Sample top questionnaires data
    top_questionnaires_data = {
        'labels': ['Mental Health Assessment', 'Physical Health Check', 'Customer Satisfaction', 'Employee Feedback', 'Product Feedback'],
        'data': [35, 25, 20, 15, 5],
        'colors': [
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 99, 132, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(153, 102, 255, 0.7)'
        ]
    }

    # Sample category comparison data (for radar chart)
    category_comparison_data = {
        'labels': ['Completion Rate', 'Avg Score', 'Response Time', 'User Satisfaction', 'Engagement'],
        'datasets': [
            {
                'label': 'Mental Health',
                'data': [85, 70, 60, 80, 75],
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgba(54, 162, 235, 1)',
            },
            {
                'label': 'Physical Health',
                'data': [70, 65, 70, 75, 80],
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'borderColor': 'rgba(255, 99, 132, 1)',
            }
        ]
    }

    # Sample response time heatmap data
    response_time_heatmap_data = {
        'labels': {
            'x': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'y': ['Morning', 'Afternoon', 'Evening', 'Night']
        },
        'data': [
            [15, 12, 8, 9, 7, 5, 6],    # Morning
            [10, 15, 13, 12, 9, 6, 5],  # Afternoon
            [8, 9, 10, 11, 14, 12, 10], # Evening
            [5, 6, 7, 8, 9, 10, 8]      # Night
        ]
    }

    # Sample completion time data
    completion_time_data = {
        'average': 180,  # 3 minutes
        'min': 60,       # 1 minute
        'max': 600,      # 10 minutes
        'average_display': '3m 0s',
        'min_display': '1m 0s',
        'max_display': '10m 0s'
    }

    return render(request, 'dashboard/admin_dashboard.html', {
        'admin_profile': admin_profile,
        'login_history': login_history,
        'total_questionnaires': questionnaires_count or 125,
        'total_responses': responses_count or 1250,
        'active_questionnaires': 75,
        'draft_questionnaires': 35,
        'archived_questionnaires': 15,
        'total_users': admin_users_count + client_users_count or 250,
        'total_organizations': 15,
        'completion_rate': 85,
        'avg_score': 7.5,
        'completion_time_data': completion_time_data,
        'trend_data': json.dumps(trend_data),
        'gender_distribution': json.dumps(gender_data),
        'age_distribution': json.dumps(age_data),
        'device_data': json.dumps(device_data),
        'risk_data': json.dumps(risk_data),
        'top_questionnaires_data': json.dumps(top_questionnaires_data),
        'category_comparison_data': json.dumps(category_comparison_data),
        'response_time_heatmap_data': json.dumps(response_time_heatmap_data),
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
