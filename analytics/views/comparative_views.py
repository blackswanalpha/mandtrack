"""
Views for comparative analytics.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Count, Sum, Q, F
from django.utils import timezone
from surveys.models import Questionnaire
from feedback.models import Response, Answer
from analytics.utils.chart_generators import (
    generate_comparative_analysis_chart,
    generate_demographic_analysis_chart
)
import json
from datetime import datetime, timedelta
import logging

# Set up logger
logger = logging.getLogger(__name__)

@login_required
def time_period_comparison(request, questionnaire_id):
    """
    Compare questionnaire responses across different time periods
    """
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    
    # Check if user has permission to view this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to view this questionnaire's analytics.")
        return redirect('dashboard:index')
    
    # Get time periods from request or use defaults
    period1_start = request.GET.get('period1_start', (timezone.now() - timedelta(days=60)).strftime('%Y-%m-%d'))
    period1_end = request.GET.get('period1_end', (timezone.now() - timedelta(days=31)).strftime('%Y-%m-%d'))
    period2_start = request.GET.get('period2_start', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    period2_end = request.GET.get('period2_end', timezone.now().strftime('%Y-%m-%d'))
    
    # Convert to datetime objects
    try:
        period1_start_date = datetime.strptime(period1_start, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        period1_end_date = datetime.strptime(period1_end, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        period2_start_date = datetime.strptime(period2_start, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        period2_end_date = datetime.strptime(period2_end, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
    except ValueError:
        messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
        return redirect('analytics:questionnaire_dashboard', questionnaire_id=questionnaire_id)
    
    # Get responses for each period
    period1_responses = Response.objects.filter(
        survey=questionnaire,
        created_at__gte=period1_start_date,
        created_at__lte=period1_end_date
    )
    
    period2_responses = Response.objects.filter(
        survey=questionnaire,
        created_at__gte=period2_start_date,
        created_at__lte=period2_end_date
    )
    
    # Calculate statistics for each period
    period1_stats = calculate_period_stats(period1_responses)
    period2_stats = calculate_period_stats(period2_responses)
    
    # Calculate percentage changes
    changes = calculate_percentage_changes(period1_stats, period2_stats)
    
    # Generate comparison charts
    score_comparison_chart = generate_score_comparison_chart(period1_responses, period2_responses, period1_start, period1_end, period2_start, period2_end)
    risk_comparison_chart = generate_risk_comparison_chart(period1_responses, period2_responses, period1_start, period1_end, period2_start, period2_end)
    
    context = {
        'questionnaire': questionnaire,
        'period1_start': period1_start,
        'period1_end': period1_end,
        'period2_start': period2_start,
        'period2_end': period2_end,
        'period1_stats': period1_stats,
        'period2_stats': period2_stats,
        'changes': changes,
        'score_comparison_chart': score_comparison_chart,
        'risk_comparison_chart': risk_comparison_chart
    }
    
    return render(request, 'analytics/comparative/time_period_comparison.html', context)

@login_required
def demographic_comparison(request, questionnaire_id):
    """
    Compare questionnaire responses across different demographic groups
    """
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    
    # Check if user has permission to view this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to view this questionnaire's analytics.")
        return redirect('dashboard:index')
    
    # Get demographic parameters from request
    demographic_type = request.GET.get('demographic_type', 'age')  # age, gender
    
    # Get all responses for this questionnaire
    responses = Response.objects.filter(survey=questionnaire)
    
    if demographic_type == 'age':
        # Define age groups
        age_groups = {
            '18-25': (18, 25),
            '26-35': (26, 35),
            '36-45': (36, 45),
            '46-55': (46, 55),
            '56+': (56, 120)
        }
        
        # Calculate statistics for each age group
        group_stats = {}
        
        for group_name, (min_age, max_age) in age_groups.items():
            group_responses = responses.filter(
                patient_age__gte=min_age,
                patient_age__lte=max_age
            )
            
            if group_responses.exists():
                group_stats[group_name] = calculate_period_stats(group_responses)
        
        # Generate age comparison chart
        age_comparison_chart = generate_demographic_analysis_chart(questionnaire.id, 'patient_age')
        
        context = {
            'questionnaire': questionnaire,
            'demographic_type': demographic_type,
            'group_stats': group_stats,
            'comparison_chart': age_comparison_chart
        }
    
    elif demographic_type == 'gender':
        # Calculate statistics for each gender
        group_stats = {}
        
        for gender in ['male', 'female', 'other', 'prefer_not_to_say']:
            group_responses = responses.filter(patient_gender=gender)
            
            if group_responses.exists():
                group_stats[gender] = calculate_period_stats(group_responses)
        
        # Generate gender comparison chart
        gender_comparison_chart = generate_demographic_analysis_chart(questionnaire.id, 'patient_gender')
        
        context = {
            'questionnaire': questionnaire,
            'demographic_type': demographic_type,
            'group_stats': group_stats,
            'comparison_chart': gender_comparison_chart
        }
    
    else:
        messages.error(request, "Invalid demographic type.")
        return redirect('analytics:questionnaire_dashboard', questionnaire_id=questionnaire_id)
    
    return render(request, 'analytics/comparative/demographic_comparison.html', context)

@login_required
def questionnaire_comparison(request):
    """
    Compare multiple questionnaires
    """
    # Get questionnaire IDs from request
    questionnaire_ids = request.GET.getlist('questionnaire_ids')
    
    if not questionnaire_ids:
        # If no questionnaires selected, show selection form
        # Get questionnaires the user has access to
        user_questionnaires = Questionnaire.objects.filter(
            Q(created_by=request.user) | 
            Q(organization__members__user=request.user)
        ).distinct()
        
        context = {
            'questionnaires': user_questionnaires
        }
        
        return render(request, 'analytics/comparative/questionnaire_selection.html', context)
    
    # Get questionnaires
    questionnaires = Questionnaire.objects.filter(id__in=questionnaire_ids)
    
    # Check if user has permission to view these questionnaires
    for questionnaire in questionnaires:
        if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
            messages.error(request, f"You don't have permission to view {questionnaire.title}.")
            return redirect('analytics:questionnaire_comparison')
    
    # Calculate statistics for each questionnaire
    questionnaire_stats = {}
    
    for questionnaire in questionnaires:
        responses = Response.objects.filter(survey=questionnaire)
        questionnaire_stats[questionnaire.id] = {
            'questionnaire': questionnaire,
            'stats': calculate_period_stats(responses)
        }
    
    # Generate comparison chart
    comparison_chart = generate_comparative_analysis_chart(questionnaire_ids)
    
    context = {
        'questionnaires': questionnaires,
        'questionnaire_stats': questionnaire_stats,
        'comparison_chart': comparison_chart
    }
    
    return render(request, 'analytics/comparative/questionnaire_comparison.html', context)

def calculate_period_stats(responses):
    """
    Calculate statistics for a set of responses
    """
    total_responses = responses.count()
    
    if total_responses == 0:
        return {
            'total_responses': 0,
            'avg_score': 0,
            'completion_rate': 0,
            'avg_completion_time': 0,
            'risk_levels': {
                'low': 0,
                'medium': 0,
                'high': 0,
                'critical': 0
            }
        }
    
    # Calculate average score
    responses_with_scores = responses.exclude(score__isnull=True)
    avg_score = responses_with_scores.aggregate(Avg('score'))['score__avg'] or 0
    
    # Calculate completion rate
    completed_responses = responses.filter(status='completed')
    completion_rate = (completed_responses.count() / total_responses * 100) if total_responses > 0 else 0
    
    # Calculate average completion time
    avg_completion_time = completed_responses.aggregate(Avg('completion_time'))['completion_time__avg'] or 0
    
    # Calculate risk level distribution
    risk_levels = {
        'low': responses.filter(risk_level='low').count(),
        'medium': responses.filter(risk_level='medium').count(),
        'high': responses.filter(risk_level='high').count(),
        'critical': responses.filter(risk_level='critical').count()
    }
    
    return {
        'total_responses': total_responses,
        'avg_score': avg_score,
        'completion_rate': completion_rate,
        'avg_completion_time': avg_completion_time,
        'risk_levels': risk_levels
    }

def calculate_percentage_changes(period1_stats, period2_stats):
    """
    Calculate percentage changes between two periods
    """
    changes = {}
    
    # Calculate change in total responses
    if period1_stats['total_responses'] > 0:
        changes['total_responses'] = ((period2_stats['total_responses'] - period1_stats['total_responses']) / period1_stats['total_responses']) * 100
    else:
        changes['total_responses'] = 100 if period2_stats['total_responses'] > 0 else 0
    
    # Calculate change in average score
    if period1_stats['avg_score'] > 0:
        changes['avg_score'] = ((period2_stats['avg_score'] - period1_stats['avg_score']) / period1_stats['avg_score']) * 100
    else:
        changes['avg_score'] = 100 if period2_stats['avg_score'] > 0 else 0
    
    # Calculate change in completion rate
    if period1_stats['completion_rate'] > 0:
        changes['completion_rate'] = ((period2_stats['completion_rate'] - period1_stats['completion_rate']) / period1_stats['completion_rate']) * 100
    else:
        changes['completion_rate'] = 100 if period2_stats['completion_rate'] > 0 else 0
    
    # Calculate change in average completion time
    if period1_stats['avg_completion_time'] > 0:
        changes['avg_completion_time'] = ((period2_stats['avg_completion_time'] - period1_stats['avg_completion_time']) / period1_stats['avg_completion_time']) * 100
    else:
        changes['avg_completion_time'] = 100 if period2_stats['avg_completion_time'] > 0 else 0
    
    # Calculate change in risk levels
    changes['risk_levels'] = {}
    
    for level in ['low', 'medium', 'high', 'critical']:
        if period1_stats['risk_levels'][level] > 0:
            changes['risk_levels'][level] = ((period2_stats['risk_levels'][level] - period1_stats['risk_levels'][level]) / period1_stats['risk_levels'][level]) * 100
        else:
            changes['risk_levels'][level] = 100 if period2_stats['risk_levels'][level] > 0 else 0
    
    return changes

def generate_score_comparison_chart(period1_responses, period2_responses, period1_start, period1_end, period2_start, period2_end):
    """
    Generate a chart comparing score distributions between two periods
    """
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    import base64
    from io import BytesIO
    
    # Get scores for each period
    period1_scores = [r.score for r in period1_responses if r.score is not None]
    period2_scores = [r.score for r in period2_responses if r.score is not None]
    
    if not period1_scores and not period2_scores:
        return None
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    
    # Create histogram
    bins = np.linspace(0, max(max(period1_scores, default=0), max(period2_scores, default=0)) + 5, 20)
    
    if period1_scores:
        plt.hist(period1_scores, bins=bins, alpha=0.5, label=f'Period 1 ({period1_start} to {period1_end})')
    
    if period2_scores:
        plt.hist(period2_scores, bins=bins, alpha=0.5, label=f'Period 2 ({period2_start} to {period2_end})')
    
    # Add labels and title
    plt.title('Score Distribution Comparison', fontsize=14)
    plt.xlabel('Score', fontsize=12)
    plt.ylabel('Number of Responses', fontsize=12)
    plt.legend()
    plt.grid(alpha=0.3)
    
    # Convert to base64 for embedding in HTML
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_png).decode('utf-8')

def generate_risk_comparison_chart(period1_responses, period2_responses, period1_start, period1_end, period2_start, period2_end):
    """
    Generate a chart comparing risk level distributions between two periods
    """
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    import base64
    from io import BytesIO
    
    # Count risk levels for each period
    risk_levels = ['low', 'medium', 'high', 'critical']
    
    period1_counts = []
    for level in risk_levels:
        period1_counts.append(period1_responses.filter(risk_level=level).count())
    
    period2_counts = []
    for level in risk_levels:
        period2_counts.append(period2_responses.filter(risk_level=level).count())
    
    if sum(period1_counts) == 0 and sum(period2_counts) == 0:
        return None
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    
    # Set up bar positions
    x = np.arange(len(risk_levels))
    width = 0.35
    
    # Create bars
    plt.bar(x - width/2, period1_counts, width, label=f'Period 1 ({period1_start} to {period1_end})')
    plt.bar(x + width/2, period2_counts, width, label=f'Period 2 ({period2_start} to {period2_end})')
    
    # Add labels and title
    plt.title('Risk Level Distribution Comparison', fontsize=14)
    plt.xlabel('Risk Level', fontsize=12)
    plt.ylabel('Number of Responses', fontsize=12)
    plt.xticks(x, [level.capitalize() for level in risk_levels])
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    # Add count labels on top of bars
    for i, count in enumerate(period1_counts):
        plt.text(i - width/2, count + 0.1, str(count), ha='center', va='bottom')
    
    for i, count in enumerate(period2_counts):
        plt.text(i + width/2, count + 0.1, str(count), ha='center', va='bottom')
    
    # Convert to base64 for embedding in HTML
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_png).decode('utf-8')
