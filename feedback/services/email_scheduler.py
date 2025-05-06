from django.utils import timezone
from django.db.models import Q
from surveys.models.email_schedule import EmailSchedule
from feedback.services.bulk_email_service import BulkEmailService
from groups.models import Organization, OrganizationMember
import logging

logger = logging.getLogger(__name__)

class EmailSchedulerService:
    """
    Service for scheduling and sending automated emails
    """
    
    @staticmethod
    def create_high_risk_schedule(organization, frequency='weekly', day_of_week=1, time_of_day='09:00:00', created_by=None):
        """
        Create a schedule for high risk notifications
        
        Args:
            organization: Organization instance
            frequency: Frequency of the emails (daily, weekly, monthly, quarterly)
            day_of_week: Day of the week for weekly emails (0=Monday, 6=Sunday)
            time_of_day: Time of day to send the email (HH:MM:SS)
            created_by: User who created the schedule
            
        Returns:
            EmailSchedule: The created schedule
        """
        # Get or create a template for high risk notifications
        from surveys.models.email_schedule import EmailTemplate
        template, created = EmailTemplate.objects.get_or_create(
            name='High Risk Notification',
            category='notification',
            defaults={
                'subject': 'High Risk Responses Alert - {{ organization.name }}',
                'message': 'Multiple high-risk responses have been detected for {{ organization.name }}.',
                'html_content': '{% include "emails/bulk_high_risk_notification.html" %}',
                'variables': ['organization', 'responses', 'response_count', 'date', 'base_url'],
                'is_active': True,
                'organization': organization,
                'created_by': created_by or organization.created_by
            }
        )
        
        # Create the schedule
        schedule = EmailSchedule.objects.create(
            template=template,
            subject_override=f'High Risk Responses Alert - {organization.name}',
            is_bulk=True,
            email_type='high_risk',
            organization=organization,
            frequency=frequency,
            scheduled_time=timezone.now(),  # Will be adjusted based on frequency
            created_by=created_by or organization.created_by
        )
        
        # Set frequency-specific fields
        if frequency == 'weekly':
            schedule.custom_days = f'[{day_of_week}]'  # Day of week (0=Monday, 6=Sunday)
        
        # Parse time of day
        from datetime import datetime
        time_obj = datetime.strptime(time_of_day, '%H:%M:%S').time()
        
        # Set the scheduled time
        from datetime import datetime, timedelta
        import pytz
        
        now = timezone.now()
        scheduled_date = now.date()
        
        if frequency == 'weekly':
            # Calculate days until the next occurrence of day_of_week
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            scheduled_date = now.date() + timedelta(days=days_ahead)
        
        scheduled_time = datetime.combine(scheduled_date, time_obj, tzinfo=pytz.UTC)
        schedule.scheduled_time = scheduled_time
        
        # Save the schedule
        schedule.save()
        
        return schedule
    
    @staticmethod
    def create_member_reports_schedule(organization, frequency='monthly', day_of_month=1, time_of_day='09:00:00', created_by=None):
        """
        Create a schedule for member reports
        
        Args:
            organization: Organization instance
            frequency: Frequency of the emails (daily, weekly, monthly, quarterly)
            day_of_month: Day of the month for monthly emails (1-31)
            time_of_day: Time of day to send the email (HH:MM:SS)
            created_by: User who created the schedule
            
        Returns:
            EmailSchedule: The created schedule
        """
        # Get or create a template for member reports
        from surveys.models.email_schedule import EmailTemplate
        template, created = EmailTemplate.objects.get_or_create(
            name='Member Report',
            category='report',
            defaults={
                'subject': 'Your Response Report - {{ questionnaire.title }}',
                'message': 'Here is your response report for {{ questionnaire.title }}.',
                'html_content': '{% include "emails/response_report.html" %}',
                'variables': ['member', 'organization', 'response', 'questionnaire', 'respondent_name', 'score', 'risk_level', 'completed_at', 'response_url', 'analysis'],
                'is_active': True,
                'organization': organization,
                'created_by': created_by or organization.created_by
            }
        )
        
        # Create the schedule
        schedule = EmailSchedule.objects.create(
            template=template,
            is_bulk=True,
            email_type='report',
            organization=organization,
            frequency=frequency,
            scheduled_time=timezone.now(),  # Will be adjusted based on frequency
            created_by=created_by or organization.created_by
        )
        
        # Set frequency-specific fields
        if frequency == 'monthly' or frequency == 'quarterly':
            schedule.day_of_month = day_of_month
        
        # Parse time of day
        from datetime import datetime
        time_obj = datetime.strptime(time_of_day, '%H:%M:%S').time()
        
        # Set the scheduled time
        from datetime import datetime, timedelta
        import pytz
        
        now = timezone.now()
        scheduled_date = now.date()
        
        if frequency == 'monthly' or frequency == 'quarterly':
            # Calculate days until the next occurrence of day_of_month
            if now.day < day_of_month:
                # Still time this month
                scheduled_date = datetime(now.year, now.month, day_of_month).date()
            else:
                # Move to next month
                if now.month == 12:
                    scheduled_date = datetime(now.year + 1, 1, day_of_month).date()
                else:
                    scheduled_date = datetime(now.year, now.month + 1, day_of_month).date()
        
        scheduled_time = datetime.combine(scheduled_date, time_obj, tzinfo=pytz.UTC)
        schedule.scheduled_time = scheduled_time
        
        # Save the schedule
        schedule.save()
        
        return schedule
    
    @staticmethod
    def process_due_schedules():
        """
        Process all due email schedules
        
        Returns:
            dict: Results of the processing
        """
        now = timezone.now()
        
        # Get all active schedules that are due
        due_schedules = EmailSchedule.objects.filter(
            status='pending',
            next_send__lte=now,
            is_active=True
        )
        
        results = {
            'total': due_schedules.count(),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        # Process each schedule
        for schedule in due_schedules:
            try:
                # Check if it's a bulk email
                if schedule.is_bulk and schedule.organization:
                    if schedule.email_type == 'high_risk':
                        # Send high risk notifications
                        email_result = BulkEmailService.send_high_risk_notifications(
                            organization=schedule.organization,
                            sender=schedule.created_by
                        )
                        
                        if email_result['success']:
                            schedule.mark_as_sent()
                            results['success'] += 1
                            results['details'].append({
                                'id': str(schedule.id),
                                'type': 'high_risk',
                                'organization': schedule.organization.name,
                                'status': 'success',
                                'sent_count': email_result['sent_count']
                            })
                        else:
                            schedule.status = 'failed'
                            schedule.save()
                            results['failed'] += 1
                            results['details'].append({
                                'id': str(schedule.id),
                                'type': 'high_risk',
                                'organization': schedule.organization.name,
                                'status': 'failed',
                                'error': email_result['message']
                            })
                    
                    elif schedule.email_type == 'report':
                        # Get all active members of the organization
                        members = OrganizationMember.objects.filter(
                            organization=schedule.organization,
                            is_active=True
                        )
                        
                        # Send member reports
                        email_result = BulkEmailService.send_member_reports(
                            organization=schedule.organization,
                            members=members,
                            sender=schedule.created_by
                        )
                        
                        if email_result['success']:
                            schedule.mark_as_sent()
                            results['success'] += 1
                            results['details'].append({
                                'id': str(schedule.id),
                                'type': 'report',
                                'organization': schedule.organization.name,
                                'status': 'success',
                                'sent_count': email_result['sent_count']
                            })
                        else:
                            schedule.status = 'failed'
                            schedule.save()
                            results['failed'] += 1
                            results['details'].append({
                                'id': str(schedule.id),
                                'type': 'report',
                                'organization': schedule.organization.name,
                                'status': 'failed',
                                'error': email_result['message']
                            })
                
                # For non-bulk emails, use the standard email sending mechanism
                else:
                    # This would be handled by the existing email sending mechanism
                    # Just mark as sent for now
                    schedule.mark_as_sent()
                    results['success'] += 1
                    results['details'].append({
                        'id': str(schedule.id),
                        'type': 'standard',
                        'recipient': schedule.recipient_email,
                        'status': 'success'
                    })
            
            except Exception as e:
                logger.error(f"Error processing schedule {schedule.id}: {str(e)}")
                schedule.status = 'failed'
                schedule.save()
                results['failed'] += 1
                results['details'].append({
                    'id': str(schedule.id),
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results
