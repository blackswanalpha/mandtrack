from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Response
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Response)
def response_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Response post_save
    
    Sends emails and creates notifications when a response is created or updated
    """
    # Only process completed responses
    if instance.status != 'completed':
        return
    
    # Send completion confirmation email
    if instance.patient_email:
        try:
            from surveys.email_utils import send_completion_confirmation
            send_completion_confirmation(instance)
        except Exception as e:
            logger.error(f"Error sending completion confirmation email: {str(e)}")
    
    # Check for high risk responses
    if instance.risk_level and instance.risk_level.lower() in ['high', 'critical']:
        try:
            # Send high risk notification email
            from surveys.email_utils import send_high_risk_notification
            send_high_risk_notification(instance)
            
            # Create notification for admins
            create_high_risk_notification(instance)
        except Exception as e:
            logger.error(f"Error processing high risk response: {str(e)}")

def create_high_risk_notification(response):
    """
    Create a notification for a high risk response
    
    Args:
        response: Response instance with high risk
    """
    try:
        from dashboard.models import Notification
        from django.contrib.auth import get_user_model
        from django.urls import reverse
        
        User = get_user_model()
        
        # Get all admin users
        admin_users = User.objects.filter(is_staff=True)
        
        # Create notification for each admin
        for user in admin_users:
            Notification.objects.create(
                user=user,
                title=f"HIGH RISK ALERT: {response.survey.title}",
                message=f"A response has been flagged as {response.risk_level.upper()} risk.",
                notification_type='danger',
                url=reverse('feedback:response_detail', args=[response.id]),
                created_at=timezone.now()
            )
    
    except Exception as e:
        logger.error(f"Error creating high risk notification: {str(e)}")
