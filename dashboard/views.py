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
        import json
        from django.db.models import Count, Avg, F, Q
        from django.utils import timezone
        from datetime import timedelta
        import random

        # Get all questionnaires
        questionnaires = Questionnaire.objects.all()

        # Count questionnaires by status
        active_questionnaires = questionnaires.filter(status='active').count()
        draft_questionnaires = questionnaires.filter(status='draft').count()
        archived_questionnaires = questionnaires.filter(status='archived').count()

        # Get all responses
        responses = Response.objects.all().order_by('-created_at')
        recent_responses = responses[:10]

        # Get total users and organizations
        User = get_user_model()
        total_users = User.objects.count()

        # Try to get Organization model if it exists
        try:
            from groups.models import Organization
            total_organizations = Organization.objects.count()
        except (ImportError, ModuleNotFoundError):
            total_organizations = 0

        # Calculate completion rate
        total_responses_count = responses.count()
        completed_responses_count = responses.filter(status='completed').count()
        completion_rate = int((completed_responses_count / total_responses_count) * 100) if total_responses_count > 0 else 0

        # Calculate average score
        avg_score = responses.filter(score__isnull=False).aggregate(avg=Avg('score'))['avg'] or 0
        avg_score = round(avg_score, 1)

        # Calculate completion time statistics
        completion_times = [r.completion_time for r in responses if r.completion_time is not None]
        completion_time_data = {
            'average': sum(completion_times) / len(completion_times) if completion_times else 0,
            'min': min(completion_times) if completion_times else 0,
            'max': max(completion_times) if completion_times else 0,
        }

        # Format completion time for display
        def format_time(seconds):
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            if minutes > 0:
                return f"{minutes}m {remaining_seconds}s"
            else:
                return f"{remaining_seconds}s"

        completion_time_data['average_display'] = format_time(completion_time_data['average'])
        completion_time_data['min_display'] = format_time(completion_time_data['min'])
        completion_time_data['max_display'] = format_time(completion_time_data['max'])

        # Get response trend data (last 30 days)
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)

        # Prepare trend data
        trend_data = {
            'labels': [],
            'data': [],
            'colors': []
        }

        for i in range(30):
            date = thirty_days_ago + timedelta(days=i)
            count = responses.filter(created_at__date=date).count()
            trend_data['labels'].append(date.strftime('%b %d'))
            trend_data['data'].append(count)
            trend_data['colors'].append('rgba(54, 162, 235, 0.7)')

        # Gender distribution data
        gender_counts = responses.values('patient_gender').annotate(count=Count('id'))
        gender_data = {
            'labels': [],
            'data': [],
            'colors': []
        }

        gender_colors = {
            'male': 'rgba(54, 162, 235, 0.7)',
            'female': 'rgba(255, 99, 132, 0.7)',
            'non-binary': 'rgba(255, 206, 86, 0.7)',
            'prefer_not_to_say': 'rgba(75, 192, 192, 0.7)',
            'other': 'rgba(153, 102, 255, 0.7)'
        }

        for item in gender_counts:
            gender = item['patient_gender'] or 'unknown'
            gender_data['labels'].append(gender.replace('_', ' ').title())
            gender_data['data'].append(item['count'])
            gender_data['colors'].append(gender_colors.get(gender, 'rgba(201, 203, 207, 0.7)'))

        # Age distribution data
        age_ranges = [
            {'min': 0, 'max': 17, 'label': 'Under 18'},
            {'min': 18, 'max': 24, 'label': '18-24'},
            {'min': 25, 'max': 34, 'label': '25-34'},
            {'min': 35, 'max': 44, 'label': '35-44'},
            {'min': 45, 'max': 54, 'label': '45-54'},
            {'min': 55, 'max': 64, 'label': '55-64'},
            {'min': 65, 'max': 200, 'label': '65+'}
        ]

        age_data = {
            'labels': [],
            'data': [],
            'colors': []
        }

        for age_range in age_ranges:
            count = responses.filter(
                Q(patient_age__gte=age_range['min']) &
                Q(patient_age__lte=age_range['max'])
            ).count()

            age_data['labels'].append(age_range['label'])
            age_data['data'].append(count)
            age_data['colors'].append('rgba(54, 162, 235, 0.7)')

        # Device distribution data
        device_data = {
            'labels': ['Desktop', 'Mobile', 'Tablet'],
            'data': [0, 0, 0],
            'colors': ['rgba(54, 162, 235, 0.7)', 'rgba(255, 99, 132, 0.7)', 'rgba(255, 206, 86, 0.7)']
        }

        # Count devices from metadata
        for response in responses:
            if hasattr(response, 'metadata') and response.metadata:
                device = response.metadata.get('device', '').lower()
                if device == 'desktop':
                    device_data['data'][0] += 1
                elif device == 'mobile':
                    device_data['data'][1] += 1
                elif device == 'tablet':
                    device_data['data'][2] += 1

        # Risk level distribution
        risk_data = {
            'labels': ['Low', 'Medium', 'High', 'Critical'],
            'data': [0, 0, 0, 0],
            'colors': ['rgba(75, 192, 192, 0.7)', 'rgba(255, 206, 86, 0.7)',
                      'rgba(255, 159, 64, 0.7)', 'rgba(255, 99, 132, 0.7)']
        }

        for response in responses:
            risk_level = getattr(response, 'risk_level', '').lower()
            if risk_level == 'low':
                risk_data['data'][0] += 1
            elif risk_level == 'medium':
                risk_data['data'][1] += 1
            elif risk_level == 'high':
                risk_data['data'][2] += 1
            elif risk_level == 'critical':
                risk_data['data'][3] += 1

        # Top questionnaires data
        top_questionnaires = Questionnaire.objects.annotate(
            response_count=Count('responses')
        ).order_by('-response_count')[:5]

        top_questionnaires_data = {
            'labels': [],
            'data': [],
            'colors': []
        }

        # Generate colors for questionnaires
        questionnaire_colors = [
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 99, 132, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(153, 102, 255, 0.7)'
        ]

        for i, q in enumerate(top_questionnaires):
            top_questionnaires_data['labels'].append(q.title[:20] + '...' if len(q.title) > 20 else q.title)
            top_questionnaires_data['data'].append(q.response_count)
            top_questionnaires_data['colors'].append(questionnaire_colors[i % len(questionnaire_colors)])

        context = {
            'total_questionnaires': questionnaires.count(),
            'total_responses': total_responses_count,
            'recent_responses': recent_responses,
            'questionnaires': questionnaires[:5],
            'active_questionnaires': active_questionnaires,
            'draft_questionnaires': draft_questionnaires,
            'archived_questionnaires': archived_questionnaires,
            'total_users': total_users,
            'total_organizations': total_organizations,
            'completion_rate': completion_rate,
            'avg_score': avg_score,
            'completion_time_data': completion_time_data,
            'trend_data': json.dumps(trend_data),
            'gender_distribution': json.dumps(gender_data),
            'age_distribution': json.dumps(age_data),
            'device_data': json.dumps(device_data),
            'risk_data': json.dumps(risk_data),
            'top_questionnaires_data': json.dumps(top_questionnaires_data),
        }

        return render(request, 'dashboard/admin_dashboard.html', context)

    except Exception as e:
        # Handle any errors gracefully
        import traceback
        print(f"Error in admin_dashboard: {str(e)}")
        print(traceback.format_exc())

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
            'error_message': str(e),
            'completion_rate': 0,
            'avg_score': 0,
            'completion_time_data': {
                'average_display': '0s',
                'min_display': '0s',
                'max_display': '0s'
            },
            'trend_data': json.dumps({'labels': [], 'data': [], 'colors': []}),
            'gender_distribution': json.dumps({'labels': [], 'data': [], 'colors': []}),
            'age_distribution': json.dumps({'labels': [], 'data': [], 'colors': []}),
            'device_data': json.dumps({'labels': [], 'data': [], 'colors': []}),
            'risk_data': json.dumps({'labels': [], 'data': [], 'colors': []}),
            'top_questionnaires_data': json.dumps({'labels': [], 'data': [], 'colors': []}),
        }
        return render(request, 'dashboard/admin_dashboard.html', context)


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


@login_required
def scoring_management(request):
    """
    Scoring management page - lists all questionnaires for scoring
    """
    # Check if user is staff
    is_staff = request.user.is_staff

    # Get questionnaires the user has access to
    if is_staff:
        questionnaires = Questionnaire.objects.all().order_by('-created_at')
    else:
        # Get questionnaires created by the user
        user_questionnaires = Questionnaire.objects.filter(created_by=request.user)

        # Get questionnaires from organizations the user is a member of
        try:
            org_questionnaires = Questionnaire.objects.filter(organization__members__user=request.user)
            # Combine and remove duplicates
            questionnaires = (user_questionnaires | org_questionnaires).distinct().order_by('-created_at')
        except:
            questionnaires = user_questionnaires.order_by('-created_at')

    context = {
        'questionnaires': questionnaires,
        'is_staff': is_staff
    }

    return render(request, 'admin_portal/scoring_management.html', context)


@login_required
def scoring_detail(request, system_id):
    """
    Scoring system detail page
    """
    # Check if user is staff
    is_staff = request.user.is_staff

    try:
        # Import the ScoringSystem model
        from surveys.models import ScoringSystem, ScoreRule, OptionScore, ScoreRange
        from surveys.models.scoring import ResponseScore

        # Get the scoring system
        scoring_system = get_object_or_404(ScoringSystem, id=system_id)

        # Check if user has access to this scoring system
        if not is_staff and scoring_system.questionnaire.created_by != request.user:
            # Check if user is in the organization
            try:
                if not scoring_system.questionnaire.organization.members.filter(user=request.user).exists():
                    return redirect('dashboard:scoring_management')
            except:
                return redirect('dashboard:scoring_management')

        # Get score rules
        score_rules = ScoreRule.objects.filter(scoring_system=scoring_system)

        # Get score ranges
        score_ranges = ScoreRange.objects.filter(scoring_system=scoring_system)

        # Get option scores
        option_scores = OptionScore.objects.filter(score_rule__scoring_system=scoring_system)

        # Get response scores
        response_scores = ResponseScore.objects.filter(scoring_system=scoring_system).select_related('response', 'score_range').order_by('-calculated_at')[:10]

        context = {
            'scoring_system': scoring_system,
            'score_rules': score_rules,
            'score_ranges': score_ranges,
            'option_scores': option_scores,
            'response_scores': response_scores,
            'is_staff': is_staff
        }

        return render(request, 'admin_portal/scoring_detail.html', context)

    except Exception as e:
        import traceback
        print(f"Error in scoring_detail: {str(e)}")
        print(traceback.format_exc())

        # Create a dummy scoring system object for the template
        class DummyScoringSystem:
            def __init__(self):
                self.id = None
                self.name = "Error Loading Scoring System"
                self.description = "There was an error loading the scoring system."
                self.questionnaire = None
                self.scoring_type = None
                self.created_by = None
                self.created_at = None

            def get_scoring_type_display(self):
                return None

        context = {
            'scoring_system': DummyScoringSystem(),
            'error_message': str(e),
            'is_staff': is_staff,
            'score_rules': [],
            'score_ranges': [],
            'option_scores': [],
            'response_scores': []
        }

        return render(request, 'admin_portal/scoring_detail.html', context)


@login_required
def scoring_create(request):
    """
    Create new scoring system
    """
    # Check if user is staff
    if not request.user.is_staff:
        return redirect('dashboard:scoring_management')

    # Handle form submission
    if request.method == 'POST':
        # Import the ScoringSystem model
        from surveys.models import ScoringSystem
        from django.contrib import messages

        # Get form data
        name = request.POST.get('name')
        description = request.POST.get('description')
        questionnaire_id = request.POST.get('questionnaire')
        scoring_type = request.POST.get('scoring_type')

        # Validate form data
        if not name or not questionnaire_id or not scoring_type:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('dashboard:scoring_create')

        try:
            # Get the questionnaire
            questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)

            # Create the scoring system
            scoring_system = ScoringSystem.objects.create(
                name=name,
                description=description,
                questionnaire=questionnaire,
                scoring_type=scoring_type,
                created_by=request.user
            )

            messages.success(request, f'Scoring system "{name}" created successfully.')
            return redirect('dashboard:scoring_detail', system_id=scoring_system.id)

        except Exception as e:
            messages.error(request, f'Error creating scoring system: {str(e)}')
            return redirect('dashboard:scoring_create')

    # Get all questionnaires
    questionnaires = Questionnaire.objects.all().order_by('-created_at')

    context = {
        'questionnaires': questionnaires
    }

    return render(request, 'admin_portal/scoring_create.html', context)