"""
Views for email reports.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings
from surveys.models import Questionnaire
from feedback.models import Response
from analytics.models import Report, ScheduledReport
from analytics.utils.email_service import (
    send_clinical_report_email,
    send_dashboard_report_email,
    send_batch_report_email,
    schedule_recurring_report
)
import json
import logging

# Set up logger
logger = logging.getLogger(__name__)

@login_required
def email_report_form(request, report_id):
    """
    Display a form for sending a report via email
    """
    report = get_object_or_404(Report, id=report_id)
    
    # Check if user has permission to view this report
    if report.created_by != request.user and (
        not report.questionnaire or 
        not report.questionnaire.organization or 
        not report.questionnaire.organization.members.filter(user=request.user).exists()
    ):
        messages.error(request, "You don't have permission to email this report.")
        return redirect('dashboard:index')
    
    context = {
        'report': report
    }
    
    return render(request, 'analytics/email/email_report_form.html', context)

@login_required
@require_POST
def send_report_email(request, report_id):
    """
    Send a report via email
    """
    report = get_object_or_404(Report, id=report_id)
    
    # Check if user has permission to view this report
    if report.created_by != request.user and (
        not report.questionnaire or 
        not report.questionnaire.organization or 
        not report.questionnaire.organization.members.filter(user=request.user).exists()
    ):
        messages.error(request, "You don't have permission to email this report.")
        return redirect('dashboard:index')
    
    # Get form data
    recipient_email = request.POST.get('recipient_email')
    sender_name = request.POST.get('sender_name', request.user.get_full_name() or request.user.username)
    additional_message = request.POST.get('additional_message')
    
    if not recipient_email:
        messages.error(request, "Recipient email is required.")
        return redirect('analytics:email_report_form', report_id=report_id)
    
    # Send email based on report type
    if report.report_type == 'clinical':
        success = send_clinical_report_email(
            report=report,
            recipient_email=recipient_email,
            sender_name=sender_name,
            additional_message=additional_message
        )
    elif report.report_type == 'dashboard':
        success = send_dashboard_report_email(
            report=report,
            recipient_email=recipient_email,
            sender_name=sender_name,
            additional_message=additional_message
        )
    else:
        messages.error(request, f"Unsupported report type: {report.report_type}")
        return redirect('analytics:email_report_form', report_id=report_id)
    
    if success:
        messages.success(request, f"Report sent to {recipient_email} successfully.")
    else:
        messages.error(request, "Failed to send report. Please try again.")
    
    return redirect('analytics:report_detail', pk=report_id)

@login_required
def email_batch_form(request, questionnaire_id):
    """
    Display a form for sending a batch report via email
    """
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    
    # Check if user has permission to view this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to email reports for this questionnaire.")
        return redirect('dashboard:index')
    
    # Get responses for this questionnaire
    responses = Response.objects.filter(survey=questionnaire)
    
    context = {
        'questionnaire': questionnaire,
        'response_count': responses.count()
    }
    
    return render(request, 'analytics/email/email_batch_form.html', context)

@login_required
@require_POST
def send_batch_email(request, questionnaire_id):
    """
    Send a batch report via email
    """
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    
    # Check if user has permission to view this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to email reports for this questionnaire.")
        return redirect('dashboard:index')
    
    # Get form data
    recipient_email = request.POST.get('recipient_email')
    sender_name = request.POST.get('sender_name', request.user.get_full_name() or request.user.username)
    additional_message = request.POST.get('additional_message')
    
    if not recipient_email:
        messages.error(request, "Recipient email is required.")
        return redirect('analytics:email_batch_form', questionnaire_id=questionnaire_id)
    
    # Get responses for this questionnaire
    responses = Response.objects.filter(survey=questionnaire)
    
    if not responses.exists():
        messages.error(request, "No responses found for this questionnaire.")
        return redirect('analytics:email_batch_form', questionnaire_id=questionnaire_id)
    
    # Send batch email
    success = send_batch_report_email(
        responses=responses,
        recipient_email=recipient_email,
        sender_name=sender_name,
        additional_message=additional_message
    )
    
    if success:
        messages.success(request, f"Batch report sent to {recipient_email} successfully.")
    else:
        messages.error(request, "Failed to send batch report. Please try again.")
    
    return redirect('analytics:questionnaire_dashboard', questionnaire_id=questionnaire_id)

@login_required
def schedule_report_form(request, report_id=None, questionnaire_id=None):
    """
    Display a form for scheduling a recurring report
    """
    report = None
    questionnaire = None
    
    if report_id:
        report = get_object_or_404(Report, id=report_id)
        
        # Check if user has permission to view this report
        if report.created_by != request.user and (
            not report.questionnaire or 
            not report.questionnaire.organization or 
            not report.questionnaire.organization.members.filter(user=request.user).exists()
        ):
            messages.error(request, "You don't have permission to schedule this report.")
            return redirect('dashboard:index')
        
        questionnaire = report.questionnaire
    
    elif questionnaire_id:
        questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
        
        # Check if user has permission to view this questionnaire
        if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
            messages.error(request, "You don't have permission to schedule reports for this questionnaire.")
            return redirect('dashboard:index')
    
    else:
        messages.error(request, "Either report_id or questionnaire_id is required.")
        return redirect('dashboard:index')
    
    context = {
        'report': report,
        'questionnaire': questionnaire
    }
    
    return render(request, 'analytics/email/schedule_report_form.html', context)

@login_required
@require_POST
def create_scheduled_report(request):
    """
    Create a scheduled report
    """
    # Get form data
    report_type = request.POST.get('report_type')
    report_id = request.POST.get('report_id')
    questionnaire_id = request.POST.get('questionnaire_id')
    recipient_email = request.POST.get('recipient_email')
    frequency = request.POST.get('frequency', 'daily')
    day = request.POST.get('day', '0')
    time = request.POST.get('time', '08:00')
    
    if not recipient_email:
        messages.error(request, "Recipient email is required.")
        return redirect('dashboard:index')
    
    # Validate parameters
    if report_type not in ['clinical', 'dashboard', 'batch']:
        messages.error(request, f"Unsupported report type: {report_type}")
        return redirect('dashboard:index')
    
    # Prepare parameters
    parameters = {
        'user': request.user.id
    }
    
    if report_id:
        report = get_object_or_404(Report, id=report_id)
        
        # Check if user has permission to view this report
        if report.created_by != request.user and (
            not report.questionnaire or 
            not report.questionnaire.organization or 
            not report.questionnaire.organization.members.filter(user=request.user).exists()
        ):
            messages.error(request, "You don't have permission to schedule this report.")
            return redirect('dashboard:index')
        
        parameters['report_id'] = report_id
        
        if report.questionnaire:
            parameters['questionnaire_id'] = str(report.questionnaire.id)
    
    elif questionnaire_id:
        questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
        
        # Check if user has permission to view this questionnaire
        if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
            messages.error(request, "You don't have permission to schedule reports for this questionnaire.")
            return redirect('dashboard:index')
        
        parameters['questionnaire_id'] = questionnaire_id
    
    else:
        messages.error(request, "Either report_id or questionnaire_id is required.")
        return redirect('dashboard:index')
    
    # Prepare schedule
    try:
        day_int = int(day)
    except (ValueError, TypeError):
        day_int = 0
    
    schedule = {
        'frequency': frequency,
        'day': day_int,
        'time': time
    }
    
    # Create scheduled report
    scheduled_report = schedule_recurring_report(
        report_type=report_type,
        parameters=parameters,
        schedule=schedule,
        recipient_email=recipient_email
    )
    
    if scheduled_report:
        messages.success(request, f"Report scheduled to be sent to {recipient_email} {frequency}.")
        
        if report_id:
            return redirect('analytics:report_detail', pk=report_id)
        elif questionnaire_id:
            return redirect('analytics:questionnaire_dashboard', questionnaire_id=questionnaire_id)
    else:
        messages.error(request, "Failed to schedule report. Please try again.")
        
        if report_id:
            return redirect('analytics:schedule_report_form', report_id=report_id)
        elif questionnaire_id:
            return redirect('analytics:schedule_report_form', questionnaire_id=questionnaire_id)
    
    return redirect('dashboard:index')

@login_required
def scheduled_reports_list(request):
    """
    Display a list of scheduled reports
    """
    # Get scheduled reports for this user
    scheduled_reports = ScheduledReport.objects.filter(created_by=request.user)
    
    context = {
        'scheduled_reports': scheduled_reports
    }
    
    return render(request, 'analytics/email/scheduled_reports_list.html', context)

@login_required
def toggle_scheduled_report(request, report_id):
    """
    Toggle the active status of a scheduled report
    """
    scheduled_report = get_object_or_404(ScheduledReport, id=report_id)
    
    # Check if user has permission to modify this scheduled report
    if scheduled_report.created_by != request.user:
        messages.error(request, "You don't have permission to modify this scheduled report.")
        return redirect('analytics:scheduled_reports_list')
    
    # Toggle active status
    scheduled_report.is_active = not scheduled_report.is_active
    scheduled_report.save(update_fields=['is_active'])
    
    if scheduled_report.is_active:
        messages.success(request, "Scheduled report activated.")
    else:
        messages.success(request, "Scheduled report deactivated.")
    
    return redirect('analytics:scheduled_reports_list')

@login_required
def delete_scheduled_report(request, report_id):
    """
    Delete a scheduled report
    """
    scheduled_report = get_object_or_404(ScheduledReport, id=report_id)
    
    # Check if user has permission to delete this scheduled report
    if scheduled_report.created_by != request.user:
        messages.error(request, "You don't have permission to delete this scheduled report.")
        return redirect('analytics:scheduled_reports_list')
    
    # Delete scheduled report
    scheduled_report.delete()
    
    messages.success(request, "Scheduled report deleted.")
    
    return redirect('analytics:scheduled_reports_list')
