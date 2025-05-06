from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from feedback.models import Response

class EmailService:
    """
    Service for sending emails related to feedback responses
    """
    
    @staticmethod
    def send_high_risk_notification(response, recipient_email=None):
        """
        Send a notification email for a high-risk response
        
        Args:
            response: Response instance with high risk level
            recipient_email: Optional email address to send to (defaults to organization admin)
        
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not response or response.risk_level != 'high':
            return False
            
        # Get the questionnaire and organization
        questionnaire = response.survey
        organization = questionnaire.organization if hasattr(questionnaire, 'organization') else None
        
        # Get the respondent information
        respondent_name = response.user.get_full_name() if response.user else response.patient_name
        respondent_email = response.user.email if response.user else response.patient_email
        
        # If no recipient email provided, use organization admin email
        if not recipient_email and organization:
            # Get the first admin of the organization
            admin_member = organization.members.filter(role='admin').first()
            if admin_member and admin_member.user:
                recipient_email = admin_member.user.email
        
        # If still no recipient email, use the default admin email
        if not recipient_email:
            recipient_email = settings.DEFAULT_FROM_EMAIL
            
        # Prepare email context
        context = {
            'response': response,
            'questionnaire': questionnaire,
            'organization': organization,
            'respondent_name': respondent_name or 'Anonymous',
            'respondent_email': respondent_email or 'Not provided',
            'score': response.score,
            'risk_level': response.get_risk_level_display(),
            'completed_at': response.completed_at,
            'response_url': f"{settings.BASE_URL}/feedback/{response.id}/" if hasattr(settings, 'BASE_URL') else None
        }
        
        # Render email templates
        html_message = render_to_string('emails/high_risk_notification.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        try:
            send_mail(
                subject=f'High Risk Response Alert - {questionnaire.title}',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False
            )
            return True
        except Exception as e:
            print(f"Error sending high risk notification email: {str(e)}")
            return False
    
    @staticmethod
    def send_response_report(response, recipient_email=None):
        """
        Send a report email for a response
        
        Args:
            response: Response instance
            recipient_email: Optional email address to send to
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not response:
            return False
            
        # Get the questionnaire and organization
        questionnaire = response.survey
        organization = questionnaire.organization if hasattr(questionnaire, 'organization') else None
        
        # Get the respondent information
        respondent_name = response.user.get_full_name() if response.user else response.patient_name
        respondent_email = response.user.email if response.user else response.patient_email
        
        # If no recipient email provided, use respondent email
        if not recipient_email:
            recipient_email = respondent_email
            
        # If still no recipient email, use the default admin email
        if not recipient_email:
            recipient_email = settings.DEFAULT_FROM_EMAIL
            
        # Prepare email context
        context = {
            'response': response,
            'questionnaire': questionnaire,
            'organization': organization,
            'respondent_name': respondent_name or 'Anonymous',
            'score': response.score,
            'risk_level': response.get_risk_level_display(),
            'completed_at': response.completed_at,
            'response_url': f"{settings.BASE_URL}/feedback/{response.id}/" if hasattr(settings, 'BASE_URL') else None
        }
        
        # Get analysis if available
        try:
            if hasattr(response, 'analysis'):
                context['analysis'] = response.analysis
        except:
            pass
            
        # Render email templates
        html_message = render_to_string('emails/response_report.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        try:
            send_mail(
                subject=f'Response Report - {questionnaire.title}',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False
            )
            return True
        except Exception as e:
            print(f"Error sending response report email: {str(e)}")
            return False
