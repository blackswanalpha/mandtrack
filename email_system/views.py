"""
Views for the email system app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q

from .models import EmailTemplate, EmailLog, ScheduledEmail
from feedback.models import Response, AIAnalysis
from .template_variables import template_renderer, get_available_variables

@login_required
def template_list(request):
    """
    List all email templates
    """
    templates = EmailTemplate.objects.all()

    # Filter by category if provided
    category = request.GET.get('category')
    if category:
        templates = templates.filter(category=category)

    # Filter by search term if provided
    search = request.GET.get('search')
    if search:
        templates = templates.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(subject__icontains=search)
        )

    return render(request, 'email_system/template_list.html', {
        'templates': templates,
        'category': category,
        'search': search,
    })

@login_required
def template_create(request):
    """
    Create a new email template
    """
    if request.method == 'POST':
        form = request.POST
        template = EmailTemplate(
            name=form.get('name'),
            description=form.get('description', ''),
            subject=form.get('subject'),
            message=form.get('message'),
            html_content=form.get('html_content', ''),
            category=form.get('category', 'notification'),
            is_active=form.get('is_active') == 'on',
            is_default=form.get('is_default') == 'on',
            created_by=request.user
        )
        template.save()
        messages.success(request, f'Template "{template.name}" created successfully.')
        return redirect('email_system:template_detail', pk=template.pk)

    return render(request, 'email_system/template_form.html', {
        'title': 'Create Email Template',
    })

@login_required
def template_detail(request, pk):
    """
    View an email template
    """
    template = get_object_or_404(EmailTemplate, pk=pk)
    return render(request, 'email_system/template_detail.html', {
        'template': template,
    })

@login_required
def template_edit(request, pk):
    """
    Edit an email template
    """
    template = get_object_or_404(EmailTemplate, pk=pk)

    if request.method == 'POST':
        form = request.POST
        template.name = form.get('name')
        template.description = form.get('description', '')
        template.subject = form.get('subject')
        template.message = form.get('message')
        template.html_content = form.get('html_content', '')
        template.category = form.get('category', 'notification')
        template.is_active = form.get('is_active') == 'on'
        template.is_default = form.get('is_default') == 'on'
        template.save()
        messages.success(request, f'Template "{template.name}" updated successfully.')
        return redirect('email_system:template_detail', pk=template.pk)

    return render(request, 'email_system/template_form.html', {
        'template': template,
        'title': f'Edit Template: {template.name}',
    })

@login_required
def template_delete(request, pk):
    """
    Delete an email template
    """
    template = get_object_or_404(EmailTemplate, pk=pk)

    if request.method == 'POST':
        name = template.name
        template.delete()
        messages.success(request, f'Template "{name}" deleted successfully.')
        return redirect('email_system:template_list')

    return render(request, 'email_system/template_confirm_delete.html', {
        'template': template,
    })

@login_required
def template_preview(request, pk):
    """
    Preview an email template
    """
    template = get_object_or_404(EmailTemplate, pk=pk)

    # Get preview context from template renderer
    preview_context = template_renderer.get_preview_context()

    # Add current user to context
    preview_context['user']['email'] = request.user.email
    preview_context['user']['name'] = request.user.get_full_name() or request.user.email
    preview_context['user']['first_name'] = request.user.first_name
    preview_context['user']['last_name'] = request.user.last_name

    # If template is for a response, add sample response data
    if template.category in ['report', 'feedback']:
        # Get a sample response if available
        sample_response = Response.objects.first()
        if sample_response:
            preview_context['response'] = {
                'id': sample_response.id,
                'score': sample_response.score,
                'created_at': sample_response.created_at,
                'status': sample_response.status,
                'completion_time': sample_response.completion_time
            }
            preview_context['questionnaire'] = {
                'title': sample_response.survey.title,
                'description': sample_response.survey.description,
                'category': sample_response.survey.category
            }

    # Render the template with variables
    rendered_subject = template_renderer.render(template.subject, preview_context)
    rendered_message = template_renderer.render(template.message, preview_context)
    rendered_html = template_renderer.render(template.html_content, preview_context) if template.html_content else ''

    # Get all available variables for the template editor
    available_variables = get_available_variables()

    return render(request, 'email_system/template_preview.html', {
        'template': template,
        'rendered_subject': rendered_subject,
        'rendered_message': rendered_message,
        'rendered_html': rendered_html,
        'preview_context': preview_context,
        'available_variables': available_variables,
    })

@login_required
def send_email(request):
    """
    Send an email using a template
    """
    if request.method == 'POST':
        form = request.POST
        template_id = form.get('template')
        to_email = form.get('to_email')
        cc_emails = form.get('cc_emails', '')
        bcc_emails = form.get('bcc_emails', '')
        response_id = form.get('response')

        if not template_id or not to_email:
            messages.error(request, 'Template and recipient email are required.')
            return redirect('email_system:send_email')

        try:
            template = EmailTemplate.objects.get(pk=template_id)
        except EmailTemplate.DoesNotExist:
            messages.error(request, 'Selected template does not exist.')
            return redirect('email_system:send_email')

        # Create email log
        email_log = EmailLog(
            subject=template.subject,
            message=template.message,
            html_content=template.html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_email=to_email,
            cc_emails=cc_emails,
            bcc_emails=bcc_emails,
            template=template,
            status='sending',
            sent_by=request.user
        )

        # If sending for a specific response, link it
        if response_id:
            try:
                response = Response.objects.get(pk=response_id)
                email_log.response = response
            except Response.DoesNotExist:
                pass

        email_log.save()

        try:
            # Prepare context for template rendering
            context = {
                'user': {
                    'email': to_email,
                    'name': to_email.split('@')[0] if '@' in to_email else to_email,
                }
            }

            # If sending for a specific response, add response data
            if email_log.response:
                response = email_log.response
                context['response'] = {
                    'id': response.id,
                    'score': response.score,
                    'created_at': response.created_at,
                    'status': response.status,
                    'completion_time': response.completion_time
                }
                context['questionnaire'] = {
                    'title': response.survey.title,
                    'description': response.survey.description,
                    'category': response.survey.category
                }

            # Render template with variables
            subject = template_renderer.render(template.subject, context)
            message = template_renderer.render(template.message, context)
            html_content = template_renderer.render(template.html_content, context) if template.html_content else ''

            # Update email log with rendered content
            email_log.subject = subject
            email_log.message = message
            email_log.html_content = html_content
            email_log.save()

            # Prepare email
            from_email = settings.DEFAULT_FROM_EMAIL
            to_emails = [to_email]

            # Add CC and BCC recipients
            cc_list = [email.strip() for email in cc_emails.split(',')] if cc_emails else []
            bcc_list = [email.strip() for email in bcc_emails.split(',')] if bcc_emails else []

            # Create email message
            if html_content:
                text_content = strip_tags(html_content)
                email = EmailMultiAlternatives(
                    subject, text_content, from_email, to_emails,
                    cc=cc_list, bcc=bcc_list
                )
                email.attach_alternative(html_content, "text/html")
            else:
                email = EmailMultiAlternatives(
                    subject, message, from_email, to_emails,
                    cc=cc_list, bcc=bcc_list
                )

            # Send email
            email.send()

            # Update email log
            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
            email_log.save()

            messages.success(request, f'Email sent successfully to {to_email}.')
            return redirect('email_system:email_log_list')

        except Exception as e:
            # Mark as failed and log error
            email_log.status = 'failed'
            email_log.error_message = str(e)
            email_log.save()
            messages.error(request, f'Failed to send email: {str(e)}')

    # Get templates for dropdown
    templates = EmailTemplate.objects.filter(is_active=True)

    # Pre-populate with template ID if provided
    template_id = request.GET.get('template')
    selected_template = None
    if template_id:
        try:
            selected_template = EmailTemplate.objects.get(pk=template_id)
        except EmailTemplate.DoesNotExist:
            pass

    # Pre-populate with response ID if provided
    response_id = request.GET.get('response')
    selected_response = None
    recipient_email = ''
    if response_id:
        try:
            selected_response = Response.objects.get(pk=response_id)
            if selected_response.email:
                recipient_email = selected_response.email
        except Response.DoesNotExist:
            pass

    return render(request, 'email_system/send_email.html', {
        'templates': templates,
        'selected_template': selected_template,
        'selected_response': selected_response,
        'recipient_email': recipient_email,
    })

@login_required
def email_log_list(request):
    """
    List all email logs
    """
    logs = EmailLog.objects.all()

    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        logs = logs.filter(status=status)

    # Filter by search term if provided
    search = request.GET.get('search')
    if search:
        logs = logs.filter(
            Q(subject__icontains=search) |
            Q(to_email__icontains=search) |
            Q(from_email__icontains=search)
        )

    return render(request, 'email_system/email_log_list.html', {
        'logs': logs,
        'status': status,
        'search': search,
    })

@login_required
def email_log_detail(request, pk):
    """
    View an email log
    """
    log = get_object_or_404(EmailLog, pk=pk)
    return render(request, 'email_system/email_log_detail.html', {
        'log': log,
    })

@login_required
def resend_email(request, pk):
    """
    Resend a previously sent email
    """
    log = get_object_or_404(EmailLog, pk=pk)

    if request.method == 'POST':
        try:
            # Prepare context for template rendering
            context = {
                'user': {
                    'email': log.to_email,
                    'name': log.to_email.split('@')[0] if '@' in log.to_email else log.to_email,
                }
            }

            # If sending for a specific response, add response data
            if log.response:
                response = log.response
                context['response'] = {
                    'id': response.id,
                    'score': response.score,
                    'created_at': response.created_at,
                    'status': response.status,
                    'completion_time': response.completion_time
                }
                context['questionnaire'] = {
                    'title': response.survey.title,
                    'description': response.survey.description,
                    'category': response.survey.category
                }

            # Get the original template if available
            template = log.template

            # Render template with variables
            if template:
                subject = template_renderer.render(template.subject, context)
                message = template_renderer.render(template.message, context)
                html_content = template_renderer.render(template.html_content, context) if template.html_content else ''
            else:
                # Use the log content directly if no template is available
                subject = log.subject
                message = log.message
                html_content = log.html_content

            # Prepare email
            from_email = settings.DEFAULT_FROM_EMAIL
            to_emails = [log.to_email]

            # Add CC and BCC recipients
            cc_list = [email.strip() for email in log.cc_emails.split(',')] if log.cc_emails else []
            bcc_list = [email.strip() for email in log.bcc_emails.split(',')] if log.bcc_emails else []

            # Create email message
            if html_content:
                text_content = strip_tags(html_content)
                email = EmailMultiAlternatives(
                    subject, text_content, from_email, to_emails,
                    cc=cc_list, bcc=bcc_list
                )
                email.attach_alternative(html_content, "text/html")
            else:
                email = EmailMultiAlternatives(
                    subject, message, from_email, to_emails,
                    cc=cc_list, bcc=bcc_list
                )

            # Send email
            email.send()

            # Create new email log
            new_log = EmailLog.objects.create(
                subject=log.subject,
                message=log.message,
                html_content=log.html_content,
                from_email=log.from_email,
                to_email=log.to_email,
                cc_emails=log.cc_emails,
                bcc_emails=log.bcc_emails,
                template=log.template,
                response=log.response,
                analysis=log.analysis,
                status='sent',
                sent_at=timezone.now(),
                sent_by=request.user
            )

            messages.success(request, f'Email resent successfully to {log.to_email}.')
            return redirect('email_system:email_log_detail', pk=new_log.pk)

        except Exception as e:
            messages.error(request, f'Failed to resend email: {str(e)}')
            return redirect('email_system:email_log_detail', pk=log.pk)

    return render(request, 'email_system/resend_email_confirm.html', {
        'log': log,
    })


@login_required
def scheduled_email_list(request):
    """
    List all scheduled emails
    """
    scheduled_emails = ScheduledEmail.objects.all()

    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        scheduled_emails = scheduled_emails.filter(status=status)

    # Filter by search term if provided
    search = request.GET.get('search')
    if search:
        scheduled_emails = scheduled_emails.filter(
            Q(name__icontains=search) |
            Q(to_email__icontains=search) |
            Q(description__icontains=search)
        )

    return render(request, 'email_system/scheduled_email_list.html', {
        'scheduled_emails': scheduled_emails,
        'status': status,
        'search': search,
    })


@login_required
def scheduled_email_create(request):
    """
    Create a new scheduled email
    """
    if request.method == 'POST':
        form = request.POST
        template_id = form.get('template')
        to_email = form.get('to_email')
        cc_emails = form.get('cc_emails', '')
        bcc_emails = form.get('bcc_emails', '')
        response_id = form.get('response')

        # Get scheduling information
        name = form.get('name')
        description = form.get('description', '')
        frequency = form.get('frequency', 'once')
        scheduled_time_str = form.get('scheduled_time')
        end_date_str = form.get('end_date', '')

        if not template_id or not to_email or not name or not scheduled_time_str:
            messages.error(request, 'Template, recipient email, name, and scheduled time are required.')
            return redirect('email_system:scheduled_email_create')

        try:
            template = EmailTemplate.objects.get(pk=template_id)
        except EmailTemplate.DoesNotExist:
            messages.error(request, 'Selected template does not exist.')
            return redirect('email_system:scheduled_email_create')

        try:
            # Parse scheduled time
            scheduled_time = timezone.datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M')
            scheduled_time = timezone.make_aware(scheduled_time)

            # Parse end date if provided
            end_date = None
            if end_date_str and frequency != 'once':
                end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = timezone.make_aware(end_date.replace(hour=23, minute=59, second=59))
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('email_system:scheduled_email_create')

        # Create scheduled email
        scheduled_email = ScheduledEmail(
            name=name,
            description=description,
            template=template,
            to_email=to_email,
            cc_emails=cc_emails,
            bcc_emails=bcc_emails,
            frequency=frequency,
            scheduled_time=scheduled_time,
            end_date=end_date,
            next_scheduled=scheduled_time,
            created_by=request.user
        )

        # Set recurring options
        if frequency == 'weekly':
            scheduled_email.weekday = int(form.get('weekday', scheduled_time.weekday()))
        elif frequency in ['monthly', 'quarterly', 'yearly']:
            scheduled_email.day_of_month = int(form.get('day_of_month', scheduled_time.day))

        # If sending for a specific response, link it
        if response_id:
            try:
                response = Response.objects.get(pk=response_id)
                scheduled_email.response = response

                # Add response data to context
                scheduled_email.context_data = {
                    'response': {
                        'id': response.id,
                        'score': response.score,
                        'created_at': response.created_at.isoformat(),
                        'status': response.status,
                        'completion_time': response.completion_time
                    },
                    'questionnaire': {
                        'title': response.survey.title,
                        'description': response.survey.description,
                        'category': response.survey.category
                    }
                }
            except Response.DoesNotExist:
                pass

        scheduled_email.save()
        messages.success(request, f'Scheduled email "{scheduled_email.name}" created successfully.')
        return redirect('email_system:scheduled_email_detail', pk=scheduled_email.pk)

    # Get templates for dropdown
    templates = EmailTemplate.objects.filter(is_active=True)

    # Pre-populate with template ID if provided
    template_id = request.GET.get('template')
    selected_template = None
    if template_id:
        try:
            selected_template = EmailTemplate.objects.get(pk=template_id)
        except EmailTemplate.DoesNotExist:
            pass

    # Pre-populate with response ID if provided
    response_id = request.GET.get('response')
    selected_response = None
    recipient_email = ''
    if response_id:
        try:
            selected_response = Response.objects.get(pk=response_id)
            if selected_response.email:
                recipient_email = selected_response.email
        except Response.DoesNotExist:
            pass

    return render(request, 'email_system/scheduled_email_form.html', {
        'templates': templates,
        'selected_template': selected_template,
        'selected_response': selected_response,
        'recipient_email': recipient_email,
        'title': 'Schedule Email',
    })


@login_required
def scheduled_email_detail(request, pk):
    """
    View a scheduled email
    """
    scheduled_email = get_object_or_404(ScheduledEmail, pk=pk)
    return render(request, 'email_system/scheduled_email_detail.html', {
        'scheduled_email': scheduled_email,
    })


@login_required
def scheduled_email_edit(request, pk):
    """
    Edit a scheduled email
    """
    scheduled_email = get_object_or_404(ScheduledEmail, pk=pk)

    if request.method == 'POST':
        form = request.POST

        # Update basic information
        scheduled_email.name = form.get('name')
        scheduled_email.description = form.get('description', '')

        # Update email content
        template_id = form.get('template')
        try:
            scheduled_email.template = EmailTemplate.objects.get(pk=template_id)
        except EmailTemplate.DoesNotExist:
            messages.error(request, 'Selected template does not exist.')
            return redirect('email_system:scheduled_email_edit', pk=scheduled_email.pk)

        # Update recipients
        scheduled_email.to_email = form.get('to_email')
        scheduled_email.cc_emails = form.get('cc_emails', '')
        scheduled_email.bcc_emails = form.get('bcc_emails', '')

        # Update scheduling
        scheduled_email.frequency = form.get('frequency', 'once')

        # Parse scheduled time
        scheduled_time_str = form.get('scheduled_time')
        try:
            scheduled_time = timezone.datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M')
            scheduled_time = timezone.make_aware(scheduled_time)
            scheduled_email.scheduled_time = scheduled_time

            # Only update next_scheduled if it's in the future
            if scheduled_email.status == 'scheduled' and (not scheduled_email.next_scheduled or scheduled_time > timezone.now()):
                scheduled_email.next_scheduled = scheduled_time
        except ValueError:
            messages.error(request, 'Invalid scheduled time format.')
            return redirect('email_system:scheduled_email_edit', pk=scheduled_email.pk)

        # Parse end date
        end_date_str = form.get('end_date', '')
        if end_date_str and scheduled_email.frequency != 'once':
            try:
                end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = timezone.make_aware(end_date.replace(hour=23, minute=59, second=59))
                scheduled_email.end_date = end_date
            except ValueError:
                messages.error(request, 'Invalid end date format.')
                return redirect('email_system:scheduled_email_edit', pk=scheduled_email.pk)
        else:
            scheduled_email.end_date = None

        # Update recurring options
        if scheduled_email.frequency == 'weekly':
            scheduled_email.weekday = int(form.get('weekday', scheduled_time.weekday()))
        elif scheduled_email.frequency in ['monthly', 'quarterly', 'yearly']:
            scheduled_email.day_of_month = int(form.get('day_of_month', scheduled_time.day))

        # Save changes
        scheduled_email.save()
        messages.success(request, f'Scheduled email "{scheduled_email.name}" updated successfully.')
        return redirect('email_system:scheduled_email_detail', pk=scheduled_email.pk)

    # Get templates for dropdown
    templates = EmailTemplate.objects.filter(is_active=True)

    return render(request, 'email_system/scheduled_email_form.html', {
        'scheduled_email': scheduled_email,
        'templates': templates,
        'selected_template': scheduled_email.template,
        'selected_response': scheduled_email.response,
        'title': f'Edit Scheduled Email: {scheduled_email.name}',
    })


@login_required
def scheduled_email_delete(request, pk):
    """
    Delete a scheduled email
    """
    scheduled_email = get_object_or_404(ScheduledEmail, pk=pk)

    if request.method == 'POST':
        name = scheduled_email.name
        scheduled_email.delete()
        messages.success(request, f'Scheduled email "{name}" deleted successfully.')
        return redirect('email_system:scheduled_email_list')

    return render(request, 'email_system/scheduled_email_confirm_delete.html', {
        'scheduled_email': scheduled_email,
    })


@login_required
def scheduled_email_cancel(request, pk):
    """
    Cancel a scheduled email
    """
    scheduled_email = get_object_or_404(ScheduledEmail, pk=pk)

    if request.method == 'POST':
        scheduled_email.cancel()
        messages.success(request, f'Scheduled email "{scheduled_email.name}" cancelled successfully.')
        return redirect('email_system:scheduled_email_detail', pk=scheduled_email.pk)

    return render(request, 'email_system/scheduled_email_confirm_cancel.html', {
        'scheduled_email': scheduled_email,
    })
