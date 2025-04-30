from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import JsonResponse
from surveys.models import Questionnaire
from feedback.models import Response
from .models import Notification

@login_required
def user_dashboard(request):
    """
    Main user dashboard
    """
    try:
        # Get questionnaires created by the user or in their organizations
        user_questionnaires = Questionnaire.objects.filter(created_by=request.user)

        # Get questionnaires from organizations the user is a member of
        # Use a try-except block to handle the case where the user is not a member of any organization
        try:
            org_questionnaires = Questionnaire.objects.filter(organization__members__user=request.user)
            # Combine and remove duplicates
            questionnaires = (user_questionnaires | org_questionnaires).distinct()
        except:
            questionnaires = user_questionnaires

        # Get recent responses
        responses = Response.objects.filter(questionnaire__in=questionnaires).order_by('-created_at')[:5]

        context = {
            'total_questionnaires': questionnaires.count(),
            'total_responses': Response.objects.filter(questionnaire__in=questionnaires).count(),
            'recent_responses': responses,
            'questionnaires': questionnaires[:5],
        }

        # If user is staff, redirect to admin dashboard
        if request.user.is_staff and request.path == '/dashboard/':
            return redirect('dashboard:admin_dashboard')

        return render(request, 'dashboard/user_dashboard.html', context)

    except Exception as e:
        # Handle any errors gracefully
        context = {
            'total_questionnaires': 0,
            'total_responses': 0,
            'recent_responses': [],
            'questionnaires': [],
            'error_message': str(e)
        }
        return render(request, 'dashboard/user_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """
    Admin dashboard
    """
    # Check if user is admin
    if not request.user.is_staff:
        return redirect('dashboard:user_dashboard')

    try:
        # Get all questionnaires
        questionnaires = Questionnaire.objects.all()

        # Count questionnaires by status
        active_questionnaires = questionnaires.filter(status='active').count()
        draft_questionnaires = questionnaires.filter(status='draft').count()
        archived_questionnaires = questionnaires.filter(status='archived').count()

        # Get all responses
        responses = Response.objects.all().order_by('-created_at')[:10]

        # Get total users and organizations
        User = get_user_model()
        total_users = User.objects.count()

        # Try to get Organization model if it exists
        try:
            from groups.models import Organization
            total_organizations = Organization.objects.count()
        except (ImportError, ModuleNotFoundError):
            total_organizations = 0

        context = {
            'total_questionnaires': questionnaires.count(),
            'total_responses': Response.objects.count(),
            'recent_responses': responses,
            'questionnaires': questionnaires[:5],
            'active_questionnaires': active_questionnaires,
            'draft_questionnaires': draft_questionnaires,
            'archived_questionnaires': archived_questionnaires,
            'total_users': total_users,
            'total_organizations': total_organizations,
        }

        return render(request, 'admin_portal/dashboard.html', context)

    except Exception as e:
        # Handle any errors gracefully
        context = {
            'total_questionnaires': 0,
            'total_responses': 0,
            'recent_responses': [],
            'questionnaires': [],
            'active_questionnaires': 0,
            'draft_questionnaires': 0,
            'archived_questionnaires': 0,
            'total_users': 0,
            'total_organizations': 0,
            'error_message': str(e)
        }
        return render(request, 'admin_portal/dashboard.html', context)


@login_required
def search(request):
    """
    Search functionality for the admin portal
    """
    query = request.GET.get('q', '')

    if not query or len(query) < 2:
        return JsonResponse({'results': []})

    # Search in questionnaires
    questionnaires = Questionnaire.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(access_code__icontains=query)
    )[:5]

    # Search in users
    User = get_user_model()
    users = User.objects.filter(
        Q(email__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )[:5]

    # Search in responses
    responses = Response.objects.filter(
        Q(respondent_name__icontains=query) |
        Q(respondent_email__icontains=query) |
        Q(questionnaire__title__icontains=query)
    )[:5]

    # Format results
    results = []

    # Add questionnaire results
    for q in questionnaires:
        results.append({
            'type': 'questionnaire',
            'title': q.title,
            'description': q.description[:100] if q.description else '',
            'url': f'/surveys/{q.pk}/',
            'icon': 'clipboard-list'
        })

    # Add user results
    for u in users:
        results.append({
            'type': 'user',
            'title': u.get_full_name() or u.email,
            'description': f'Email: {u.email}',
            'url': '#',  # Replace with actual user profile URL
            'icon': 'user'
        })

    # Add response results
    for r in responses:
        results.append({
            'type': 'response',
            'title': f'Response from {r.respondent_name or "Anonymous"}',
            'description': f'For: {r.questionnaire.title}',
            'url': f'/responses/{r.pk}/',
            'icon': 'comment'
        })

    return JsonResponse({'results': results})


@login_required
def get_notifications(request):
    """
    Get user notifications
    """
    notifications = Notification.objects.filter(user=request.user)[:10]

    # Format notifications
    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%b %d, %Y %H:%M'),
            'url': notification.url or '#',
        })

    # Get unread count
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return JsonResponse({
        'notifications': notification_data,
        'unread_count': unread_count
    })


@login_required
def mark_notification_read(request, notification_id):
    """
    Mark notification as read
    """
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()

    return JsonResponse({'success': True})


@login_required
def mark_all_notifications_read(request):
    """
    Mark all notifications as read
    """
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    return JsonResponse({'success': True})


@login_required
def user_management(request):
    """
    User management page
    """
    if not request.user.is_staff:
        return redirect('dashboard:user_dashboard')

    # Get all users
    User = get_user_model()
    users = User.objects.all().order_by('-date_joined')

    context = {
        'users': users
    }

    return render(request, 'admin_portal/user_management.html', context)