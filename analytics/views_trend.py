from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from feedback.models import Response
from groups.models import Organization, OrganizationMember
from surveys.models import Questionnaire
from .services.trend_analysis import TrendAnalysisService

@login_required
def member_trend_analysis(request, org_pk, member_pk):
    """
    Detailed trend analysis for a member's responses over time
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    member = get_object_or_404(OrganizationMember, pk=member_pk, organization=organization)
    
    # Check if user has permission to view member data
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
            messages.error(request, "You don't have permission to view this member's data.")
            return redirect('groups:organization_list')
    
    # If user is not admin and can't view responses, deny access
    if not is_admin and not can_view_responses:
        messages.error(request, "You don't have permission to view this member's data.")
        return redirect('groups:member_detail', org_pk=org_pk, pk=member_pk)
    
    # Get time period from request
    time_period = int(request.GET.get('time_period', 90))
    
    # Get trend analysis
    analysis = TrendAnalysisService.analyze_member_trends(
        member=member,
        organization=organization,
        time_period=time_period
    )
    
    # If this is an AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(analysis)
    
    # Render the template
    return render(request, 'analytics/member_trend_analysis.html', {
        'organization': organization,
        'member': member,
        'analysis': analysis,
        'time_period': time_period,
        'is_admin': is_admin
    })

@login_required
def organization_trend_analysis(request, org_pk):
    """
    Detailed trend analysis for an organization's responses over time
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
    
    # Get time period from request
    time_period = int(request.GET.get('time_period', 90))
    
    # Get trend analysis
    analysis = TrendAnalysisService.analyze_organization_trends(
        organization=organization,
        time_period=time_period
    )
    
    # If this is an AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(analysis)
    
    # Render the template
    return render(request, 'analytics/organization_trend_analysis.html', {
        'organization': organization,
        'analysis': analysis,
        'time_period': time_period,
        'is_admin': is_admin
    })
