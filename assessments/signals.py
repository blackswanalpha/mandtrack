from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
import logging

from .models import Assessment

logger = logging.getLogger(__name__)

# Temporarily disable the signal by commenting out the decorator
# @receiver(post_save, sender=Assessment)
def send_high_risk_notification(sender, instance, created, **kwargs):
    """
    Send email notification when an assessment is marked as high risk
    """
    # Check if this is a high-risk assessment
    if instance.is_high_risk() and instance.consultation_recommended in ['recommended', 'required']:
        logger.info(f"Sending high risk notification for assessment {instance.pk}")

        try:
            # Prepare context for email template
            context = {
                'assessment': instance,
                'response': instance.response,
                'patient_id': instance.response.patient_identifier or 'Anonymous',
                'risk_level': instance.get_risk_level(),
                'assessment_date': instance.assessment_date,
                'assessment_url': f"{settings.SITE_URL}{reverse('assessments:assessment_detail', kwargs={'pk': instance.pk})}",
                'consultation_status': instance.get_consultation_recommended_display(),
                'consultation_urgency': instance.consultation_urgency,
                'assessor': instance.assessor.get_full_name() if instance.assessor else 'System',
            }

            # Render email templates
            html_content = render_to_string('assessments/email/high_risk_notification.html', context)
            text_content = strip_tags(html_content)

            # Create email subject
            subject = f"HIGH RISK ASSESSMENT: Patient {instance.response.patient_identifier or 'Anonymous'}"

            # Get recipient email(s)
            recipient_emails = []

            # Add the assessor if available
            if instance.assessor and instance.assessor.email:
                recipient_emails.append(instance.assessor.email)

            # Add organization admins if available
            if hasattr(instance.response, 'organization') and instance.response.organization:
                admin_emails = instance.response.organization.members.filter(
                    role='admin'
                ).values_list('user__email', flat=True)
                recipient_emails.extend(admin_emails)

            # Add default recipients from settings
            if hasattr(settings, 'HIGH_RISK_NOTIFICATION_RECIPIENTS'):
                recipient_emails.extend(settings.HIGH_RISK_NOTIFICATION_RECIPIENTS)

            # If no recipients, use the DEFAULT_FROM_EMAIL
            if not recipient_emails:
                recipient_emails = [settings.DEFAULT_FROM_EMAIL]

            # Remove duplicates
            recipient_emails = list(set(recipient_emails))

            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_emails
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            logger.info(f"High risk notification sent to {', '.join(recipient_emails)}")

        except Exception as e:
            logger.error(f"Error sending high risk notification: {str(e)}")
