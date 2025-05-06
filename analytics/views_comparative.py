from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Count, Q, F
from feedback.models import Response, Answer
from groups.models import Organization, OrganizationMember
from surveys.models import Questionnaire
import json

@login_required
def compare_members(request, org_pk):
    """
    Compare responses between members of an organization
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    
    # Check if user has permission to view organization data
    try:
        user_membership = OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            is_active=True
        )
        is_admin = user_membership.role == 'admin'
        can_view_responses = user_membership.can_view_responses()
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not a member
        if request.user.is_staff:
            is_admin = True
            can_view_responses = True
        else:
            messages.error(request, "You don't have permission to view this organization's data.")
            return redirect('groups:organization_list')
    
    # If user is not admin and can't view responses, deny access
    if not is_admin and not can_view_responses:
        messages.error(request, "You don't have permission to view this organization's data.")
        return redirect('groups:organization_detail', pk=org_pk)
    
    # Get all active members of the organization
    members = OrganizationMember.objects.filter(
        organization=organization,
        is_active=True
    ).select_related('user')
    
    # Get all questionnaires for this organization
    questionnaires = Questionnaire.objects.filter(organization=organization)
    
    # Get selected members for comparison
    selected_member_ids = request.GET.getlist('members')
    selected_questionnaire_id = request.GET.get('questionnaire')
    
    # If no members selected, don't show comparison
    if not selected_member_ids:
        return render(request, 'analytics/compare_members.html', {
            'organization': organization,
            'members': members,
            'questionnaires': questionnaires,
            'is_admin': is_admin,
            'show_comparison': False
        })
    
    # Get the selected members
    selected_members = OrganizationMember.objects.filter(
        pk__in=selected_member_ids,
        organization=organization,
        is_active=True
    ).select_related('user')
    
    # Get the selected questionnaire
    selected_questionnaire = None
    if selected_questionnaire_id:
        selected_questionnaire = get_object_or_404(
            Questionnaire,
            pk=selected_questionnaire_id,
            organization=organization
        )
    
    # Get responses for the selected members
    responses_query = Response.objects.filter(
        user__in=[member.user for member in selected_members],
        survey__organization=organization
    )
    
    # Filter by questionnaire if selected
    if selected_questionnaire:
        responses_query = responses_query.filter(survey=selected_questionnaire)
    
    # Get response statistics for each member
    member_stats = []
    for member in selected_members:
        member_responses = responses_query.filter(user=member.user)
        
        # Calculate statistics
        total_responses = member_responses.count()
        completed_responses = member_responses.filter(status='completed').count()
        average_score = member_responses.aggregate(Avg('score'))['score__avg'] or 0
        
        # Get risk level distribution
        risk_levels = member_responses.values('risk_level').annotate(count=Count('risk_level'))
        risk_distribution = {
            'low': 0,
            'medium': 0,
            'high': 0,
            'critical': 0,
            'unknown': 0
        }
        for level in risk_levels:
            risk_distribution[level['risk_level']] = level['count']
        
        # Add to member stats
        member_stats.append({
            'member': member,
            'total_responses': total_responses,
            'completed_responses': completed_responses,
            'average_score': average_score,
            'risk_distribution': risk_distribution
        })
    
    # Prepare data for charts
    chart_data = {
        'labels': [member.user.get_full_name() or member.user.email for member in selected_members],
        'average_scores': [stats['average_score'] for stats in member_stats],
        'total_responses': [stats['total_responses'] for stats in member_stats],
        'completed_responses': [stats['completed_responses'] for stats in member_stats],
        'risk_levels': {
            'low': [stats['risk_distribution']['low'] for stats in member_stats],
            'medium': [stats['risk_distribution']['medium'] for stats in member_stats],
            'high': [stats['risk_distribution']['high'] for stats in member_stats],
            'critical': [stats['risk_distribution']['critical'] for stats in member_stats]
        }
    }
    
    # If this is an AJAX request, return JSON data
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'chart_data': chart_data,
            'member_stats': [
                {
                    'name': member.user.get_full_name() or member.user.email,
                    'total_responses': stats['total_responses'],
                    'completed_responses': stats['completed_responses'],
                    'average_score': stats['average_score'],
                    'risk_distribution': stats['risk_distribution']
                }
                for member, stats in zip(selected_members, member_stats)
            ]
        })
    
    # Render the template
    return render(request, 'analytics/compare_members.html', {
        'organization': organization,
        'members': members,
        'questionnaires': questionnaires,
        'selected_members': selected_members,
        'selected_questionnaire': selected_questionnaire,
        'member_stats': member_stats,
        'chart_data': json.dumps(chart_data),
        'is_admin': is_admin,
        'show_comparison': True
    })

@login_required
def organization_overview(request, org_pk):
    """
    Overview of all members in an organization
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    
    # Check if user has permission to view organization data
    try:
        user_membership = OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            is_active=True
        )
        is_admin = user_membership.role == 'admin'
        can_view_responses = user_membership.can_view_responses()
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not a member
        if request.user.is_staff:
            is_admin = True
            can_view_responses = True
        else:
            messages.error(request, "You don't have permission to view this organization's data.")
            return redirect('groups:organization_list')
    
    # If user is not admin and can't view responses, deny access
    if not is_admin and not can_view_responses:
        messages.error(request, "You don't have permission to view this organization's data.")
        return redirect('groups:organization_detail', pk=org_pk)
    
    # Get all active members of the organization
    members = OrganizationMember.objects.filter(
        organization=organization,
        is_active=True
    ).select_related('user')
    
    # Get all questionnaires for this organization
    questionnaires = Questionnaire.objects.filter(organization=organization)
    
    # Get selected questionnaire
    selected_questionnaire_id = request.GET.get('questionnaire')
    selected_questionnaire = None
    if selected_questionnaire_id:
        selected_questionnaire = get_object_or_404(
            Questionnaire,
            pk=selected_questionnaire_id,
            organization=organization
        )
    
    # Get responses for all members
    responses_query = Response.objects.filter(
        user__in=[member.user for member in members],
        survey__organization=organization
    )
    
    # Filter by questionnaire if selected
    if selected_questionnaire:
        responses_query = responses_query.filter(survey=selected_questionnaire)
    
    # Calculate organization-wide statistics
    total_responses = responses_query.count()
    completed_responses = responses_query.filter(status='completed').count()
    average_score = responses_query.aggregate(Avg('score'))['score__avg'] or 0
    
    # Get risk level distribution
    risk_levels = responses_query.values('risk_level').annotate(count=Count('risk_level'))
    risk_distribution = {
        'low': 0,
        'medium': 0,
        'high': 0,
        'critical': 0,
        'unknown': 0
    }
    for level in risk_levels:
        risk_distribution[level['risk_level']] = level['count']
    
    # Get response statistics for each member
    member_stats = []
    for member in members:
        member_responses = responses_query.filter(user=member.user)
        
        # Calculate statistics
        member_total_responses = member_responses.count()
        member_completed_responses = member_responses.filter(status='completed').count()
        member_average_score = member_responses.aggregate(Avg('score'))['score__avg'] or 0
        
        # Get risk level distribution
        member_risk_levels = member_responses.values('risk_level').annotate(count=Count('risk_level'))
        member_risk_distribution = {
            'low': 0,
            'medium': 0,
            'high': 0,
            'critical': 0,
            'unknown': 0
        }
        for level in member_risk_levels:
            member_risk_distribution[level['risk_level']] = level['count']
        
        # Add to member stats
        member_stats.append({
            'member': member,
            'total_responses': member_total_responses,
            'completed_responses': member_completed_responses,
            'average_score': member_average_score,
            'risk_distribution': member_risk_distribution
        })
    
    # Sort members by average score
    member_stats.sort(key=lambda x: x['average_score'], reverse=True)
    
    # Prepare data for charts
    chart_data = {
        'labels': [stats['member'].user.get_full_name() or stats['member'].user.email for stats in member_stats],
        'average_scores': [stats['average_score'] for stats in member_stats],
        'total_responses': [stats['total_responses'] for stats in member_stats],
        'completed_responses': [stats['completed_responses'] for stats in member_stats],
        'risk_levels': {
            'low': [stats['risk_distribution']['low'] for stats in member_stats],
            'medium': [stats['risk_distribution']['medium'] for stats in member_stats],
            'high': [stats['risk_distribution']['high'] for stats in member_stats],
            'critical': [stats['risk_distribution']['critical'] for stats in member_stats]
        }
    }
    
    # Render the template
    return render(request, 'analytics/organization_overview.html', {
        'organization': organization,
        'questionnaires': questionnaires,
        'selected_questionnaire': selected_questionnaire,
        'total_responses': total_responses,
        'completed_responses': completed_responses,
        'average_score': average_score,
        'risk_distribution': risk_distribution,
        'member_stats': member_stats,
        'chart_data': json.dumps(chart_data),
        'is_admin': is_admin
    })
