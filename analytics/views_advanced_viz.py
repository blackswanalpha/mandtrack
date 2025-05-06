from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from feedback.models import Response
from groups.models import Organization, OrganizationMember
from surveys.models import Questionnaire
from .services.advanced_visualization import AdvancedVisualizationService

@login_required
def advanced_visualizations(request, org_pk):
    """
    Advanced visualizations dashboard for an organization
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
    
    # Get selected member and questionnaire
    selected_member_id = request.GET.get('member')
    selected_questionnaire_id = request.GET.get('questionnaire')
    
    selected_member = None
    if selected_member_id:
        selected_member = get_object_or_404(
            OrganizationMember,
            pk=selected_member_id,
            organization=organization,
            is_active=True
        )
    
    selected_questionnaire = None
    if selected_questionnaire_id:
        selected_questionnaire = get_object_or_404(
            Questionnaire,
            pk=selected_questionnaire_id,
            organization=organization
        )
    
    # Get selected visualization type
    viz_type = request.GET.get('viz_type', 'radar')
    
    # Generate visualization based on type
    visualization_data = None
    if selected_member or viz_type in ['heatmap', 'bubble']:
        if viz_type == 'radar' and selected_member:
            visualization_data = AdvancedVisualizationService.generate_radar_chart(
                member=selected_member,
                organization=organization,
                questionnaire=selected_questionnaire
            )
        elif viz_type == 'heatmap':
            visualization_data = AdvancedVisualizationService.generate_heatmap(
                organization=organization,
                questionnaire=selected_questionnaire,
                time_period=int(request.GET.get('time_period', 30))
            )
        elif viz_type == 'bubble':
            visualization_data = AdvancedVisualizationService.generate_bubble_chart(
                organization=organization,
                questionnaire=selected_questionnaire
            )
        elif viz_type == 'timeline' and selected_member:
            visualization_data = AdvancedVisualizationService.generate_timeline_chart(
                member=selected_member,
                organization=organization,
                time_period=int(request.GET.get('time_period', 90))
            )
    
    # Render the template
    return render(request, 'analytics/advanced_visualizations.html', {
        'organization': organization,
        'members': members,
        'questionnaires': questionnaires,
        'selected_member': selected_member,
        'selected_questionnaire': selected_questionnaire,
        'viz_type': viz_type,
        'visualization_data': visualization_data,
        'is_admin': is_admin,
        'time_period': request.GET.get('time_period', 30)
    })

@login_required
def member_radar_chart(request, org_pk, member_pk):
    """
    Generate a radar chart for a member
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
            return JsonResponse({
                'success': False,
                'message': "You don't have permission to view this member's data."
            }, status=403)
    
    # If user is not admin and can't view responses, deny access
    if not is_admin and not can_view_responses:
        return JsonResponse({
            'success': False,
            'message': "You don't have permission to view this member's data."
        }, status=403)
    
    # Get selected questionnaire
    questionnaire_id = request.GET.get('questionnaire')
    questionnaire = None
    if questionnaire_id:
        questionnaire = get_object_or_404(
            Questionnaire,
            pk=questionnaire_id,
            organization=organization
        )
    
    # Generate radar chart
    result = AdvancedVisualizationService.generate_radar_chart(
        member=member,
        organization=organization,
        questionnaire=questionnaire
    )
    
    # Return JSON response
    return JsonResponse(result)

@login_required
def organization_heatmap(request, org_pk):
    """
    Generate a heatmap for an organization
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
            return JsonResponse({
                'success': False,
                'message': "You don't have permission to view this organization's data."
            }, status=403)
    
    # If user is not admin and can't view responses, deny access
    if not is_admin and not can_view_responses:
        return JsonResponse({
            'success': False,
            'message': "You don't have permission to view this organization's data."
        }, status=403)
    
    # Get selected questionnaire
    questionnaire_id = request.GET.get('questionnaire')
    questionnaire = None
    if questionnaire_id:
        questionnaire = get_object_or_404(
            Questionnaire,
            pk=questionnaire_id,
            organization=organization
        )
    
    # Get time period
    time_period = int(request.GET.get('time_period', 30))
    
    # Generate heatmap
    result = AdvancedVisualizationService.generate_heatmap(
        organization=organization,
        questionnaire=questionnaire,
        time_period=time_period
    )
    
    # Return JSON response
    return JsonResponse(result)

@login_required
def bubble_chart(request, org_pk):
    """
    Generate a bubble chart for an organization
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
            return JsonResponse({
                'success': False,
                'message': "You don't have permission to view this organization's data."
            }, status=403)
    
    # If user is not admin and can't view responses, deny access
    if not is_admin and not can_view_responses:
        return JsonResponse({
            'success': False,
            'message': "You don't have permission to view this organization's data."
        }, status=403)
    
    # Get selected questionnaire
    questionnaire_id = request.GET.get('questionnaire')
    questionnaire = None
    if questionnaire_id:
        questionnaire = get_object_or_404(
            Questionnaire,
            pk=questionnaire_id,
            organization=organization
        )
    
    # Generate bubble chart
    result = AdvancedVisualizationService.generate_bubble_chart(
        organization=organization,
        questionnaire=questionnaire
    )
    
    # Return JSON response
    return JsonResponse(result)

@login_required
def timeline_chart(request, org_pk, member_pk):
    """
    Generate a timeline chart for a member
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
            return JsonResponse({
                'success': False,
                'message': "You don't have permission to view this member's data."
            }, status=403)
    
    # If user is not admin and can't view responses, deny access
    if not is_admin and not can_view_responses:
        return JsonResponse({
            'success': False,
            'message': "You don't have permission to view this member's data."
        }, status=403)
    
    # Get time period
    time_period = int(request.GET.get('time_period', 90))
    
    # Generate timeline chart
    result = AdvancedVisualizationService.generate_timeline_chart(
        member=member,
        organization=organization,
        time_period=time_period
    )
    
    # Return JSON response
    return JsonResponse(result)
