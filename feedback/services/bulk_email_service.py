from django.core.mail import send_mass_mail, send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone
from feedback.models import Response, EmailLog
from groups.models import Organization, OrganizationMember

class BulkEmailService:
    """
    Service for sending bulk emails related to feedback responses
    """
    
    @staticmethod
    def send_high_risk_notifications(organization, responses=None, sender=None):
        """
        Send high risk notifications for multiple responses
        
        Args:
            organization: Organization instance
            responses: Optional list of Response instances (if None, all high risk responses will be used)
            sender: User who initiated the email sending
            
        Returns:
            dict: Results of the email sending operation
        """
        # Get high risk responses if not provided
        if responses is None:
            responses = Response.objects.filter(
                survey__organization=organization,
                risk_level='high',
                flagged_for_review=True
            ).select_related('survey', 'user')
        
        # Filter responses to only include high risk ones
        high_risk_responses = [r for r in responses if r.risk_level == 'high']
        
        if not high_risk_responses:
            return {
                'success': False,
                'message': 'No high risk responses found.',
                'sent_count': 0,
                'failed_count': 0
            }
        
        # Get organization admins
        admin_members = OrganizationMember.objects.filter(
            organization=organization,
            role='admin',
            is_active=True
        ).select_related('user')
        
        if not admin_members:
            return {
                'success': False,
                'message': 'No admin members found for the organization.',
                'sent_count': 0,
                'failed_count': 0
            }
        
        admin_emails = [member.user.email for member in admin_members if member.user.email]
        
        if not admin_emails:
            return {
                'success': False,
                'message': 'No admin email addresses found.',
                'sent_count': 0,
                'failed_count': 0
            }
        
        # Prepare email context
        context = {
            'organization': organization,
            'responses': high_risk_responses,
            'response_count': len(high_risk_responses),
            'date': timezone.now(),
            'base_url': settings.BASE_URL if hasattr(settings, 'BASE_URL') else ''
        }
        
        # Render email templates
        html_message = render_to_string('emails/bulk_high_risk_notification.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        subject = f'High Risk Responses Alert - {organization.name}'
        from_email = settings.DEFAULT_FROM_EMAIL
        
        sent_count = 0
        failed_count = 0
        
        try:
            # Send the email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=from_email,
                recipient_list=admin_emails,
                html_message=html_message,
                fail_silently=False
            )
            
            # Log the email
            for response in high_risk_responses:
                email_log = EmailLog(
                    email_type='bulk',
                    subject=subject,
                    recipient_email=', '.join(admin_emails),
                    sender_email=from_email,
                    template='emails/bulk_high_risk_notification.html',
                    context={
                        'response_id': str(response.id),
                        'questionnaire_title': response.survey.title,
                        'risk_level': response.risk_level
                    },
                    status='sent',
                    response=response,
                    organization=organization,
                    sent_by=sender,
                    sent_at=timezone.now()
                )
                email_log.save()
                sent_count += 1
            
            return {
                'success': True,
                'message': f'Successfully sent {sent_count} high risk notifications.',
                'sent_count': sent_count,
                'failed_count': failed_count
            }
            
        except Exception as e:
            # Log the error
            for response in high_risk_responses:
                email_log = EmailLog(
                    email_type='bulk',
                    subject=subject,
                    recipient_email=', '.join(admin_emails),
                    sender_email=from_email,
                    template='emails/bulk_high_risk_notification.html',
                    context={
                        'response_id': str(response.id),
                        'questionnaire_title': response.survey.title,
                        'risk_level': response.risk_level
                    },
                    status='failed',
                    error_message=str(e),
                    response=response,
                    organization=organization,
                    sent_by=sender
                )
                email_log.save()
                failed_count += 1
            
            return {
                'success': False,
                'message': f'Error sending high risk notifications: {str(e)}',
                'sent_count': sent_count,
                'failed_count': failed_count
            }
    
    @staticmethod
    def send_member_reports(organization, members, sender=None):
        """
        Send response reports to multiple members
        
        Args:
            organization: Organization instance
            members: List of OrganizationMember instances
            sender: User who initiated the email sending
            
        Returns:
            dict: Results of the email sending operation
        """
        if not members:
            return {
                'success': False,
                'message': 'No members provided.',
                'sent_count': 0,
                'failed_count': 0
            }
        
        sent_count = 0
        failed_count = 0
        
        for member in members:
            # Get the most recent completed response for this member
            response = Response.objects.filter(
                user=member.user,
                survey__organization=organization,
                status='completed'
            ).order_by('-completed_at').first()
            
            if not response:
                failed_count += 1
                continue
            
            # Prepare email context
            context = {
                'member': member,
                'organization': organization,
                'response': response,
                'questionnaire': response.survey,
                'respondent_name': member.user.get_full_name() or member.user.email,
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
            subject = f'Response Report - {response.survey.title}'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_email = member.user.email
            
            if not recipient_email:
                failed_count += 1
                continue
            
            try:
                # Send the email
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=from_email,
                    recipient_list=[recipient_email],
                    html_message=html_message,
                    fail_silently=False
                )
                
                # Log the email
                email_log = EmailLog(
                    email_type='report',
                    subject=subject,
                    recipient_email=recipient_email,
                    sender_email=from_email,
                    template='emails/response_report.html',
                    context={
                        'response_id': str(response.id),
                        'questionnaire_title': response.survey.title,
                        'member_name': member.user.get_full_name() or member.user.email
                    },
                    status='sent',
                    response=response,
                    organization=organization,
                    sent_by=sender,
                    sent_at=timezone.now()
                )
                email_log.save()
                sent_count += 1
                
            except Exception as e:
                # Log the error
                email_log = EmailLog(
                    email_type='report',
                    subject=subject,
                    recipient_email=recipient_email,
                    sender_email=from_email,
                    template='emails/response_report.html',
                    context={
                        'response_id': str(response.id),
                        'questionnaire_title': response.survey.title,
                        'member_name': member.user.get_full_name() or member.user.email
                    },
                    status='failed',
                    error_message=str(e),
                    response=response,
                    organization=organization,
                    sent_by=sender
                )
                email_log.save()
                failed_count += 1
        
        return {
            'success': sent_count > 0,
            'message': f'Successfully sent {sent_count} reports. Failed to send {failed_count} reports.',
            'sent_count': sent_count,
            'failed_count': failed_count
        }
