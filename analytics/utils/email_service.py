"""
Utility functions for sending email reports.
"""
import logging
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile

# Set up logger
logger = logging.getLogger(__name__)

def send_clinical_report_email(report, recipient_email, sender_name=None, additional_message=None):
    """
    Send a clinical report via email
    
    Args:
        report: Report object to send
        recipient_email: Email address to send the report to
        sender_name: Name of the sender (optional)
        additional_message: Additional message to include in the email (optional)
        
    Returns:
        Boolean indicating whether the email was sent successfully
    """
    try:
        # Get report data
        if hasattr(report, 'response') and report.response:
            response = report.response
            questionnaire = report.questionnaire
            
            # Parse report content
            if isinstance(report.content, str):
                import json
                content = json.loads(report.content)
            else:
                content = report.content
            
            # Prepare context for email template
            context = {
                'report': report,
                'content': content,
                'response': response,
                'questionnaire': questionnaire,
                'sender_name': sender_name or 'MindTrack',
                'additional_message': additional_message,
                'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            # Render email templates
            html_content = render_to_string('analytics/email/clinical_report_email.html', context)
            text_content = strip_tags(html_content)
            
            # Create email
            subject = f"Clinical Report: {questionnaire.title}"
            from_email = settings.DEFAULT_FROM_EMAIL
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[recipient_email]
            )
            
            # Attach HTML content
            email.attach_alternative(html_content, "text/html")
            
            # Attach PDF if available
            if report.pdf_file:
                email.attach(
                    f"clinical_report_{response.id}.pdf",
                    report.pdf_file.read(),
                    'application/pdf'
                )
            
            # Send email
            email.send()
            
            # Log success
            logger.info(f"Clinical report email sent to {recipient_email}")
            
            return True
        else:
            logger.error("Report is missing required data")
            return False
    
    except Exception as e:
        logger.error(f"Error sending clinical report email: {str(e)}")
        return False

def send_dashboard_report_email(report, recipient_email, sender_name=None, additional_message=None):
    """
    Send a dashboard report via email
    
    Args:
        report: Report object to send
        recipient_email: Email address to send the report to
        sender_name: Name of the sender (optional)
        additional_message: Additional message to include in the email (optional)
        
    Returns:
        Boolean indicating whether the email was sent successfully
    """
    try:
        # Get report data
        if hasattr(report, 'questionnaire') and report.questionnaire:
            questionnaire = report.questionnaire
            
            # Prepare context for email template
            context = {
                'report': report,
                'questionnaire': questionnaire,
                'sender_name': sender_name or 'MindTrack',
                'additional_message': additional_message,
                'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            # Render email templates
            html_content = render_to_string('analytics/email/dashboard_report_email.html', context)
            text_content = strip_tags(html_content)
            
            # Create email
            subject = f"Dashboard Report: {questionnaire.title}"
            from_email = settings.DEFAULT_FROM_EMAIL
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[recipient_email]
            )
            
            # Attach HTML content
            email.attach_alternative(html_content, "text/html")
            
            # Attach PDF if available
            if report.pdf_file:
                email.attach(
                    f"dashboard_report_{questionnaire.id}.pdf",
                    report.pdf_file.read(),
                    'application/pdf'
                )
            
            # Send email
            email.send()
            
            # Log success
            logger.info(f"Dashboard report email sent to {recipient_email}")
            
            return True
        else:
            logger.error("Report is missing required data")
            return False
    
    except Exception as e:
        logger.error(f"Error sending dashboard report email: {str(e)}")
        return False

def send_batch_report_email(responses, recipient_email, sender_name=None, additional_message=None):
    """
    Send a batch report of multiple responses via email
    
    Args:
        responses: List of Response objects to include in the report
        recipient_email: Email address to send the report to
        sender_name: Name of the sender (optional)
        additional_message: Additional message to include in the email (optional)
        
    Returns:
        Boolean indicating whether the email was sent successfully
    """
    try:
        if not responses:
            logger.error("No responses provided for batch report")
            return False
        
        # Group responses by questionnaire
        from collections import defaultdict
        grouped_responses = defaultdict(list)
        
        for response in responses:
            grouped_responses[response.survey].append(response)
        
        # Prepare context for email template
        context = {
            'grouped_responses': grouped_responses,
            'response_count': len(responses),
            'questionnaire_count': len(grouped_responses),
            'sender_name': sender_name or 'MindTrack',
            'additional_message': additional_message,
            'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # Render email templates
        html_content = render_to_string('analytics/email/batch_report_email.html', context)
        text_content = strip_tags(html_content)
        
        # Create email
        subject = f"Batch Report: {len(responses)} Responses"
        from_email = settings.DEFAULT_FROM_EMAIL
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[recipient_email]
        )
        
        # Attach HTML content
        email.attach_alternative(html_content, "text/html")
        
        # Generate and attach PDF report
        from analytics.utils.pdf_generator import generate_batch_report_pdf
        
        try:
            pdf_data = generate_batch_report_pdf(grouped_responses)
            
            # Attach PDF
            email.attach(
                f"batch_report_{timezone.now().strftime('%Y%m%d')}.pdf",
                pdf_data,
                'application/pdf'
            )
        except Exception as pdf_error:
            logger.error(f"Error generating PDF for batch report: {str(pdf_error)}")
            # Continue without PDF
        
        # Send email
        email.send()
        
        # Log success
        logger.info(f"Batch report email sent to {recipient_email}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error sending batch report email: {str(e)}")
        return False

def schedule_recurring_report(report_type, parameters, schedule, recipient_email):
    """
    Schedule a recurring report to be sent via email
    
    Args:
        report_type: Type of report to send ('clinical', 'dashboard', 'batch', 'comparative')
        parameters: Dictionary of parameters for the report
        schedule: Dictionary with schedule information (frequency, day, time)
        recipient_email: Email address to send the report to
        
    Returns:
        ScheduledReport object or None if there was an error
    """
    try:
        from analytics.models import ScheduledReport
        
        # Create scheduled report
        scheduled_report = ScheduledReport.objects.create(
            report_type=report_type,
            parameters=parameters,
            schedule=schedule,
            recipient_email=recipient_email,
            is_active=True,
            created_by=parameters.get('user')
        )
        
        # Log success
        logger.info(f"Recurring report scheduled for {recipient_email}")
        
        return scheduled_report
    
    except Exception as e:
        logger.error(f"Error scheduling recurring report: {str(e)}")
        return None
