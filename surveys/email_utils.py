from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
import logging
import uuid
import base64
from datetime import timedelta

logger = logging.getLogger(__name__)

def send_email_template(template, recipient_email, context, from_email=None, schedule=None,
                      related_object=None, enable_tracking=True):
    """
    Send an email using a template

    Args:
        template: EmailTemplate instance
        recipient_email: Email address of the recipient
        context: Dictionary of context variables for the template
        from_email: Sender email address (defaults to settings.DEFAULT_FROM_EMAIL)
        schedule: EmailSchedule instance (optional)
        related_object: Related object (optional)
        enable_tracking: Whether to enable email tracking (default: True)

    Returns:
        Boolean indicating success or failure
    """
    try:
        # Get the from email
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL

        # Replace template variables
        subject = replace_template_variables(template.subject, context)
        html_content = replace_template_variables(template.content, context)
        text_content = strip_tags(html_content)

        # Log email and get tracking ID
        log_entry = log_email_sent(
            template=template,
            recipient_email=recipient_email,
            context=context,
            content=html_content,
            schedule=schedule,
            related_object=related_object
        )

        # Add tracking if enabled and log entry exists
        if enable_tracking and log_entry and log_entry.tracking_id:
            html_content = add_tracking(html_content, log_entry.tracking_id)

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[recipient_email]
        )

        # Attach HTML content
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send()

        return True

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

def send_questionnaire_invitation(questionnaire, recipient_email, recipient_name=None, custom_message=None):
    """
    Send a questionnaire invitation email

    Args:
        questionnaire: Questionnaire instance
        recipient_email: Email address of the recipient
        recipient_name: Name of the recipient (optional)
        custom_message: Custom message to include in the email (optional)

    Returns:
        Boolean indicating success or failure
    """
    try:
        # Get the invitation template
        from surveys.models import EmailTemplate
        template = EmailTemplate.objects.filter(
            template_type='invitation',
            is_active=True,
            is_default=True
        ).first()

        # If no template found, use a default one
        if not template:
            subject = f"Invitation to complete {questionnaire.title}"
            html_content = render_to_string('emails/questionnaire_invitation.html', {
                'questionnaire': questionnaire,
                'recipient_name': recipient_name or 'there',
                'custom_message': custom_message,
                'survey_link': get_questionnaire_url(questionnaire),
                'organization': questionnaire.organization.name if questionnaire.organization else None
            })
            text_content = strip_tags(html_content)

            # Send email
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_content
            )
        else:
            # Use the template
            context = {
                'name': recipient_name or 'there',
                'survey_title': questionnaire.title,
                'survey_link': get_questionnaire_url(questionnaire),
                'organization': questionnaire.organization.name if questionnaire.organization else None,
                'custom_message': custom_message
            }

            send_email_template(template, recipient_email, context)

        return True

    except Exception as e:
        logger.error(f"Error sending questionnaire invitation: {str(e)}")
        return False

def send_completion_confirmation(response):
    """
    Send a completion confirmation email

    Args:
        response: Response instance

    Returns:
        Boolean indicating success or failure
    """
    try:
        # Get the recipient email
        recipient_email = response.patient_email
        if not recipient_email:
            logger.warning(f"No email address for response {response.id}")
            return False

        # Get the completion template
        from surveys.models import EmailTemplate
        template = EmailTemplate.objects.filter(
            template_type='completion',
            is_active=True,
            is_default=True
        ).first()

        # If no template found, use a default one
        if not template:
            subject = f"Thank you for completing {response.survey.title}"
            html_content = render_to_string('emails/completion_confirmation.html', {
                'response': response,
                'questionnaire': response.survey,
                'organization': response.survey.organization.name if response.survey.organization else None
            })
            text_content = strip_tags(html_content)

            # Send email
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_content
            )
        else:
            # Use the template
            context = {
                'name': 'there',  # We don't collect names in responses
                'survey_title': response.survey.title,
                'organization': response.survey.organization.name if response.survey.organization else None,
                'completion_time': format_completion_time(response.completion_time) if response.completion_time else 'N/A',
                'score': response.score if response.score is not None else 'N/A'
            }

            send_email_template(template, recipient_email, context)

        return True

    except Exception as e:
        logger.error(f"Error sending completion confirmation: {str(e)}")
        return False

def send_high_risk_notification(response):
    """
    Send a high risk notification email to administrators

    Args:
        response: Response instance with high risk

    Returns:
        Boolean indicating success or failure
    """
    try:
        # Check if response is high risk
        if not response.risk_level or response.risk_level.lower() not in ['high', 'critical']:
            return False

        # Get admin emails
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)

        if not admin_emails:
            logger.warning("No admin emails found for high risk notification")
            return False

        # Get the high risk template
        from surveys.models import EmailTemplate
        template = EmailTemplate.objects.filter(
            template_type='high_risk',
            is_active=True,
            is_default=True
        ).first()

        # If no template found, use a default one
        if not template:
            subject = f"HIGH RISK ALERT: {response.survey.title}"
            html_content = render_to_string('emails/high_risk_notification.html', {
                'response': response,
                'questionnaire': response.survey,
                'risk_level': response.risk_level,
                'response_url': get_response_url(response)
            })
            text_content = strip_tags(html_content)

            # Send email to all admins
            for admin_email in admin_emails:
                send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin_email],
                    html_message=html_content
                )
        else:
            # Use the template for each admin
            context = {
                'survey_title': response.survey.title,
                'risk_level': response.risk_level,
                'response_url': get_response_url(response),
                'patient_email': response.patient_email or 'Anonymous',
                'patient_age': response.patient_age or 'Unknown',
                'patient_gender': response.patient_gender or 'Unknown',
                'score': response.score if response.score is not None else 'N/A'
            }

            for admin_email in admin_emails:
                send_email_template(template, admin_email, context)

        return True

    except Exception as e:
        logger.error(f"Error sending high risk notification: {str(e)}")
        return False

def replace_template_variables(content, context):
    """
    Replace template variables in content

    Args:
        content: String content with variables
        context: Dictionary of context variables

    Returns:
        String with variables replaced
    """
    if not content:
        return ""

    # Replace variables
    for key, value in context.items():
        if value is not None:
            content = content.replace(f"{{{key}}}", str(value))

    return content

def get_questionnaire_url(questionnaire):
    """
    Get the URL for a questionnaire

    Args:
        questionnaire: Questionnaire instance

    Returns:
        Absolute URL for the questionnaire
    """
    try:
        # Get the base URL from settings
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')

        # Get the URL
        if questionnaire.access_code:
            url = reverse('surveys:survey_respond_slug', args=[questionnaire.access_code])
        else:
            url = reverse('surveys:survey_respond', args=[questionnaire.id])

        return f"{base_url}{url}"

    except Exception as e:
        logger.error(f"Error getting questionnaire URL: {str(e)}")
        return "#"

def get_response_url(response):
    """
    Get the URL for a response

    Args:
        response: Response instance

    Returns:
        Absolute URL for the response
    """
    try:
        # Get the base URL from settings
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')

        # Get the URL
        url = reverse('feedback:response_detail', args=[response.id])

        return f"{base_url}{url}"

    except Exception as e:
        logger.error(f"Error getting response URL: {str(e)}")
        return "#"

def format_completion_time(seconds):
    """
    Format completion time in seconds to a human-readable string

    Args:
        seconds: Completion time in seconds

    Returns:
        Formatted string (e.g. "5m 30s")
    """
    if not seconds:
        return "N/A"

    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)

    if minutes > 0:
        return f"{minutes}m {remaining_seconds}s"
    else:
        return f"{remaining_seconds}s"

def log_email_sent(template, recipient_email, context, content=None, schedule=None, related_object=None):
    """
    Log email sent to the database with tracking

    Args:
        template: EmailTemplate instance
        recipient_email: Email address of the recipient
        context: Dictionary of context variables
        content: Email content (optional)
        schedule: EmailSchedule instance (optional)
        related_object: Related object (optional)

    Returns:
        EmailLog instance
    """
    try:
        from surveys.models.email_schedule import EmailLog

        # Generate tracking ID
        tracking_id = str(uuid.uuid4())

        # Create log entry
        log_entry = EmailLog.objects.create(
            template=template,
            recipient_email=recipient_email,
            subject=replace_template_variables(template.subject, context),
            sent_at=timezone.now(),
            context=context,
            content=content,
            schedule=schedule,
            tracking_id=tracking_id,
            status='sent'
        )

        # Add related object if provided
        if related_object:
            content_type = ContentType.objects.get_for_model(related_object)
            log_entry.content_type = content_type
            log_entry.object_id = related_object.id
            log_entry.save()

        return log_entry

    except Exception as e:
        logger.error(f"Error logging email: {str(e)}")
        return None

def schedule_email(template, recipient_email, context, scheduled_time, frequency='one_time',
                  end_date=None, custom_days=None, created_by=None, related_object=None,
                  recipient_name=None, subject_override=None):
    """
    Schedule an email to be sent

    Args:
        template: EmailTemplate instance
        recipient_email: Email address of the recipient
        context: Dictionary of context variables
        scheduled_time: When to send the email
        frequency: Frequency of sending ('one_time', 'daily', 'weekly', 'monthly', 'custom')
        end_date: End date for recurring emails (optional)
        custom_days: List of days for custom frequency (e.g., [0,3,6] for Sunday, Wednesday, Saturday)
        created_by: User who created the schedule
        related_object: Related object (optional)
        recipient_name: Name of the recipient (optional)
        subject_override: Override the template subject (optional)

    Returns:
        EmailSchedule instance
    """
    try:
        from surveys.models.email_schedule import EmailSchedule

        # Create schedule
        schedule = EmailSchedule(
            template=template,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject_override=subject_override,
            frequency=frequency,
            scheduled_time=scheduled_time,
            end_date=end_date,
            context_data=context,
            created_by=created_by
        )

        # Set custom days if provided
        if custom_days and frequency == 'custom':
            schedule.set_custom_days(custom_days)

        # Set next send time
        schedule.next_send = schedule.calculate_next_send()

        # Add related object if provided
        if related_object:
            content_type = ContentType.objects.get_for_model(related_object)
            schedule.content_type = content_type
            schedule.object_id = related_object.id

        schedule.save()
        return schedule

    except Exception as e:
        logger.error(f"Error scheduling email: {str(e)}")
        return None

def process_scheduled_emails():
    """
    Process scheduled emails that are due to be sent

    Returns:
        Number of emails sent
    """
    try:
        from surveys.models.email_schedule import EmailSchedule

        # Get schedules that are due
        now = timezone.now()
        due_schedules = EmailSchedule.objects.filter(
            status='pending',
            next_send__lte=now
        )

        sent_count = 0

        for schedule in due_schedules:
            # Send email
            template = schedule.template
            recipient_email = schedule.recipient_email
            context = schedule.context_data

            # Override subject if provided
            if schedule.subject_override:
                original_subject = template.subject
                template.subject = schedule.subject_override

            # Add recipient name to context if provided
            if schedule.recipient_name:
                context['name'] = schedule.recipient_name

            # Send email
            success = send_email_template(template, recipient_email, context)

            # Reset subject if overridden
            if schedule.subject_override:
                template.subject = original_subject

            if success:
                # Mark as sent and calculate next send time
                schedule.mark_as_sent()
                sent_count += 1
            else:
                # Mark as failed
                schedule.status = 'failed'
                schedule.save()

        return sent_count

    except Exception as e:
        logger.error(f"Error processing scheduled emails: {str(e)}")
        return 0

def generate_tracking_pixel(tracking_id):
    """
    Generate a tracking pixel for email open tracking

    Args:
        tracking_id: Tracking ID for the email

    Returns:
        HTML for tracking pixel
    """
    tracking_url = f"{settings.BASE_URL}/emails/track/open/{tracking_id}/"
    return f'<img src="{tracking_url}" width="1" height="1" alt="" style="display:none;">'

def generate_tracking_links(content, tracking_id):
    """
    Generate tracking links for email click tracking

    Args:
        content: Email content
        tracking_id: Tracking ID for the email

    Returns:
        Email content with tracking links
    """
    import re

    # Find all links in the content
    link_pattern = r'href=[\'"]([^\'"]+)[\'"]'
    links = re.findall(link_pattern, content)

    # Replace links with tracking links
    for link in links:
        # Skip tracking links and image sources
        if 'track' in link or link.startswith('data:') or link.startswith('#'):
            continue

        # Generate tracking link
        tracking_url = f"{settings.BASE_URL}/emails/track/click/{tracking_id}/?url={base64.urlsafe_b64encode(link.encode()).decode()}"
        content = content.replace(f'href="{link}"', f'href="{tracking_url}"')
        content = content.replace(f"href='{link}'", f"href='{tracking_url}'")

    return content

def add_tracking(content, tracking_id):
    """
    Add tracking to email content

    Args:
        content: Email content
        tracking_id: Tracking ID for the email

    Returns:
        Email content with tracking
    """
    # Add tracking pixel
    pixel = generate_tracking_pixel(tracking_id)

    # Add tracking links
    content = generate_tracking_links(content, tracking_id)

    # Add pixel before closing body tag
    if '</body>' in content:
        content = content.replace('</body>', f'{pixel}</body>')
    else:
        content += pixel

    return content
