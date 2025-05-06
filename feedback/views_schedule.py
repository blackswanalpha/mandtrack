from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from surveys.models.email_schedule import EmailSchedule, EmailTemplate
from groups.models import Organization, OrganizationMember
from feedback.services.email_scheduler import EmailSchedulerService

@login_required
def schedule_dashboard(request, org_pk):
    """
    Dashboard for managing email schedules
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    
    # Check if user has permission to manage schedules
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
            messages.error(request, "You don't have permission to manage email schedules for this organization.")
            return redirect('groups:organization_list')
    
    # If user is not admin, deny access
    if not is_admin:
        messages.error(request, "You don't have permission to manage email schedules for this organization.")
        return redirect('groups:organization_detail', pk=org_pk)
    
    # Get all schedules for this organization
    schedules = EmailSchedule.objects.filter(
        organization=organization,
        is_bulk=True
    ).order_by('next_send')
    
    # Render the template
    return render(request, 'feedback/schedule_dashboard.html', {
        'organization': organization,
        'schedules': schedules,
        'is_admin': is_admin
    })

@login_required
@require_POST
def create_high_risk_schedule(request, org_pk):
    """
    Create a new high risk notification schedule
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    
    # Check if user has permission to manage schedules
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
            messages.error(request, "You don't have permission to manage email schedules for this organization.")
            return redirect('groups:organization_list')
    
    # If user is not admin, deny access
    if not is_admin:
        messages.error(request, "You don't have permission to manage email schedules for this organization.")
        return redirect('groups:organization_detail', pk=org_pk)
    
    # Get form data
    frequency = request.POST.get('frequency', 'weekly')
    day_of_week = int(request.POST.get('day_of_week', 1))  # Default to Monday
    time_of_day = request.POST.get('time_of_day', '09:00:00')
    
    try:
        # Create the schedule
        schedule = EmailSchedulerService.create_high_risk_schedule(
            organization=organization,
            frequency=frequency,
            day_of_week=day_of_week,
            time_of_day=time_of_day,
            created_by=request.user
        )
        
        messages.success(request, f"High risk notification schedule created successfully. Next send: {schedule.next_send.strftime('%Y-%m-%d %H:%M')}")
    except Exception as e:
        messages.error(request, f"Error creating schedule: {str(e)}")
    
    # Redirect back to the schedule dashboard
    return redirect('feedback:schedule_dashboard', org_pk=org_pk)

@login_required
@require_POST
def create_member_reports_schedule(request, org_pk):
    """
    Create a new member reports schedule
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    
    # Check if user has permission to manage schedules
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
            messages.error(request, "You don't have permission to manage email schedules for this organization.")
            return redirect('groups:organization_list')
    
    # If user is not admin, deny access
    if not is_admin:
        messages.error(request, "You don't have permission to manage email schedules for this organization.")
        return redirect('groups:organization_detail', pk=org_pk)
    
    # Get form data
    frequency = request.POST.get('frequency', 'monthly')
    day_of_month = int(request.POST.get('day_of_month', 1))
    time_of_day = request.POST.get('time_of_day', '09:00:00')
    
    try:
        # Create the schedule
        schedule = EmailSchedulerService.create_member_reports_schedule(
            organization=organization,
            frequency=frequency,
            day_of_month=day_of_month,
            time_of_day=time_of_day,
            created_by=request.user
        )
        
        messages.success(request, f"Member reports schedule created successfully. Next send: {schedule.next_send.strftime('%Y-%m-%d %H:%M')}")
    except Exception as e:
        messages.error(request, f"Error creating schedule: {str(e)}")
    
    # Redirect back to the schedule dashboard
    return redirect('feedback:schedule_dashboard', org_pk=org_pk)

@login_required
@require_POST
def toggle_schedule(request, schedule_id):
    """
    Toggle the active status of a schedule
    """
    schedule = get_object_or_404(EmailSchedule, pk=schedule_id)
    organization = schedule.organization
    
    # Check if user has permission to manage schedules
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
            messages.error(request, "You don't have permission to manage email schedules for this organization.")
            return redirect('groups:organization_list')
    
    # If user is not admin, deny access
    if not is_admin:
        messages.error(request, "You don't have permission to manage email schedules for this organization.")
        return redirect('groups:organization_detail', pk=organization.id)
    
    # Toggle the active status
    schedule.is_active = not schedule.is_active
    schedule.save()
    
    status = "activated" if schedule.is_active else "deactivated"
    messages.success(request, f"Schedule {status} successfully.")
    
    # Redirect back to the schedule dashboard
    return redirect('feedback:schedule_dashboard', org_pk=organization.id)

@login_required
@require_POST
def delete_schedule(request, schedule_id):
    """
    Delete a schedule
    """
    schedule = get_object_or_404(EmailSchedule, pk=schedule_id)
    organization = schedule.organization
    
    # Check if user has permission to manage schedules
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
            messages.error(request, "You don't have permission to manage email schedules for this organization.")
            return redirect('groups:organization_list')
    
    # If user is not admin, deny access
    if not is_admin:
        messages.error(request, "You don't have permission to manage email schedules for this organization.")
        return redirect('groups:organization_detail', pk=organization.id)
    
    # Delete the schedule
    schedule.delete()
    
    messages.success(request, "Schedule deleted successfully.")
    
    # Redirect back to the schedule dashboard
    return redirect('feedback:schedule_dashboard', org_pk=organization.id)
