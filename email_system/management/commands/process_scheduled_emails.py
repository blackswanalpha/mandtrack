"""
Management command to process scheduled emails.
"""
import logging
import traceback
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings

from email_system.models import ScheduledEmail, EmailLog
from email_system.template_variables import template_renderer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process scheduled emails that are due to be sent'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Do not actually send emails, just log what would be sent',
        )
        parser.add_argument(
            '--limit',
            type=int,
            dest='limit',
            default=50,
            help='Maximum number of emails to process in a single run',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        
        now = timezone.now()
        self.stdout.write(f"Processing scheduled emails at {now}")
        
        # Get scheduled emails that are due to be sent
        scheduled_emails = ScheduledEmail.objects.filter(
            status='scheduled',
            next_scheduled__lte=now
        ).order_by('next_scheduled')[:limit]
        
        count = scheduled_emails.count()
        self.stdout.write(f"Found {count} scheduled emails to process")
        
        for scheduled_email in scheduled_emails:
            try:
                self.process_email(scheduled_email, dry_run)
            except Exception as e:
                error_message = f"Error processing scheduled email {scheduled_email.id}: {str(e)}\n{traceback.format_exc()}"
                self.stderr.write(error_message)
                logger.error(error_message)
                
                # Mark as error
                scheduled_email.mark_as_error(str(e))
    
    def process_email(self, scheduled_email, dry_run=False):
        """
        Process a single scheduled email
        """
        self.stdout.write(f"Processing scheduled email: {scheduled_email}")
        
        # Mark as processing
        scheduled_email.status = 'processing'
        scheduled_email.save(update_fields=['status'])
        
        try:
            # Prepare context for template rendering
            context = scheduled_email.context_data or {}
            
            # Add basic user data
            if 'user' not in context:
                context['user'] = {
                    'email': scheduled_email.to_email,
                    'name': scheduled_email.to_email.split('@')[0] if '@' in scheduled_email.to_email else scheduled_email.to_email,
                }
            
            # Add response data if available
            if scheduled_email.response and 'response' not in context:
                response = scheduled_email.response
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
            
            # Add analysis data if available
            if scheduled_email.analysis and 'analysis' not in context:
                analysis = scheduled_email.analysis
                context['analysis'] = {
                    'id': analysis.id,
                    'created_at': analysis.created_at,
                    'content': analysis.content
                }
            
            # Get template
            template = scheduled_email.template
            
            # Render subject
            subject = scheduled_email.subject_override or template.subject
            subject = template_renderer.render(subject, context)
            
            # Render message
            message = scheduled_email.message_override or template.message
            message = template_renderer.render(message, context)
            
            # Render HTML content if available
            html_content = scheduled_email.html_content_override or template.html_content
            if html_content:
                html_content = template_renderer.render(html_content, context)
            
            # Create email log
            email_log = EmailLog.objects.create(
                subject=subject,
                message=message,
                html_content=html_content or '',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_email=scheduled_email.to_email,
                cc_emails=scheduled_email.cc_emails,
                bcc_emails=scheduled_email.bcc_emails,
                template=template,
                response=scheduled_email.response,
                analysis=scheduled_email.analysis,
                status='draft',
                sent_by=scheduled_email.created_by
            )
            
            if dry_run:
                self.stdout.write(f"[DRY RUN] Would send email to {scheduled_email.to_email}: {subject}")
                email_log.status = 'sent'
                email_log.sent_at = timezone.now()
                email_log.save(update_fields=['status', 'sent_at'])
            else:
                # Prepare email
                from_email = settings.DEFAULT_FROM_EMAIL
                to_emails = [scheduled_email.to_email]
                
                # Add CC and BCC recipients
                cc_list = [email.strip() for email in scheduled_email.cc_emails.split(',')] if scheduled_email.cc_emails else []
                bcc_list = [email.strip() for email in scheduled_email.bcc_emails.split(',')] if scheduled_email.bcc_emails else []
                
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
                
                try:
                    # Send email
                    email_log.status = 'sending'
                    email_log.save(update_fields=['status'])
                    
                    email.send()
                    
                    # Mark as sent
                    email_log.mark_as_sent()
                    self.stdout.write(f"Sent email to {scheduled_email.to_email}: {subject}")
                except Exception as e:
                    error_message = f"Error sending email: {str(e)}"
                    self.stderr.write(error_message)
                    logger.error(error_message)
                    
                    # Mark as failed
                    email_log.mark_as_failed(str(e))
                    
                    # Re-raise to mark the scheduled email as error
                    raise
            
            # Update scheduled email
            scheduled_email.last_sent = timezone.now()
            
            # Calculate next scheduled time for recurring emails
            if scheduled_email.frequency != 'once':
                next_scheduled = scheduled_email.calculate_next_scheduled()
                
                if next_scheduled:
                    scheduled_email.next_scheduled = next_scheduled
                    scheduled_email.status = 'scheduled'
                    self.stdout.write(f"Next scheduled time: {next_scheduled}")
                else:
                    scheduled_email.status = 'completed'
                    self.stdout.write("No more occurrences, marking as completed")
            else:
                scheduled_email.status = 'completed'
                self.stdout.write("One-time email, marking as completed")
            
            scheduled_email.save()
            
        except Exception as e:
            error_message = f"Error processing scheduled email: {str(e)}"
            self.stderr.write(error_message)
            logger.error(error_message)
            
            # Mark as error
            scheduled_email.mark_as_error(str(e))
            
            # Re-raise to be caught by the outer try/except
            raise
