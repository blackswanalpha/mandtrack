from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Response, EmailLog
from groups.models import Organization, OrganizationMember
from surveys.models import Questionnaire
from .services.bulk_email_service import BulkEmailService

@login_required
def email_dashboard(request, org_pk):
    """
    Dashboard for sending bulk emails
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    
    # Check if user has permission to send emails
    try:
        user_membership = OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            is_active=True
        )
        is_admin = user_membership.role == 'admin'
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not a member
        if request.user.is_staff:
            is_admin = True
        else:
            messages.error(request, "You don't have permission to send emails for this organization.")
            return redirect('groups:organization_list')
    
    # If user is not admin, deny access
    if not is_admin:
        messages.error(request, "You don't have permission to send emails for this organization.")
        return redirect('groups:organization_detail', pk=org_pk)
    
    # Get all members of the organization
    members = OrganizationMember.objects.filter(
        organization=organization,
        is_active=True
    ).select_related('user')
    
    # Get all questionnaires for this organization
    questionnaires = Questionnaire.objects.filter(organization=organization)
    
    # Get high risk responses
    high_risk_responses = Response.objects.filter(
        survey__organization=organization,
        risk_level='high'
    ).select_related('survey', 'user')
    
    # Get recent email logs
    email_logs = EmailLog.objects.filter(
        organization=organization
    ).order_by('-created_at')[:10]
    
    # Render the template
    return render(request, 'feedback/email_dashboard.html', {
        'organization': organization,
        'members': members,
        'questionnaires': questionnaires,
        'high_risk_responses': high_risk_responses,
        'email_logs': email_logs,
        'is_admin': is_admin
    })

@login_required
@require_POST
def send_high_risk_notifications(request, org_pk):
    """
    Send high risk notifications for an organization
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    
    # Check if user has permission to send emails
    try:
        user_membership = OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            is_active=True
        )
        is_admin = user_membership.role == 'admin'
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not a member
        if request.user.is_staff:
            is_admin = True
        else:
            messages.error(request, "You don't have permission to send emails for this organization.")
            return redirect('groups:organization_list')
    
    # If user is not admin, deny access
    if not is_admin:
        messages.error(request, "You don't have permission to send emails for this organization.")
        return redirect('groups:organization_detail', pk=org_pk)
    
    # Get selected questionnaire
    questionnaire_id = request.POST.get('questionnaire')
    
    # Get high risk responses
    responses_query = Response.objects.filter(
        survey__organization=organization,
        risk_level='high'
    )
    
    # Filter by questionnaire if selected
    if questionnaire_id:
        responses_query = responses_query.filter(survey_id=questionnaire_id)
    
    # Send high risk notifications
    result = BulkEmailService.send_high_risk_notifications(
        organization=organization,
        responses=responses_query,
        sender=request.user
    )
    
    # Show message based on result
    if result['success']:
        messages.success(request, result['message'])
    else:
        messages.error(request, result['message'])
    
    # Redirect back to the email dashboard
    return redirect('feedback:email_dashboard', org_pk=org_pk)

@login_required
@require_POST
def send_member_reports(request, org_pk):
    """
    Send reports to selected members
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    
    # Check if user has permission to send emails
    try:
        user_membership = OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            is_active=True
        )
        is_admin = user_membership.role == 'admin'
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not a member
        if request.user.is_staff:
            is_admin = True
        else:
            messages.error(request, "You don't have permission to send emails for this organization.")
            return redirect('groups:organization_list')
    
    # If user is not admin, deny access
    if not is_admin:
        messages.error(request, "You don't have permission to send emails for this organization.")
        return redirect('groups:organization_detail', pk=org_pk)
    
    # Get selected members
    member_ids = request.POST.getlist('members')
    
    if not member_ids:
        messages.error(request, "No members selected.")
        return redirect('feedback:email_dashboard', org_pk=org_pk)
    
    # Get member objects
    members = OrganizationMember.objects.filter(
        pk__in=member_ids,
        organization=organization,
        is_active=True
    )
    
    # Send reports to members
    result = BulkEmailService.send_member_reports(
        organization=organization,
        members=members,
        sender=request.user
    )
    
    # Show message based on result
    if result['success']:
        messages.success(request, result['message'])
    else:
        messages.error(request, result['message'])
    
    # Redirect back to the email dashboard
    return redirect('feedback:email_dashboard', org_pk=org_pk)
