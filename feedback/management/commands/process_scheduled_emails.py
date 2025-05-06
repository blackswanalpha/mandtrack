from django.core.management.base import BaseCommand
from django.utils import timezone
from feedback.services.email_scheduler import EmailSchedulerService
import logging
import json

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process scheduled emails that are due to be sent'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually sending emails',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS(f"Starting scheduled email processing at {timezone.now()}"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No emails will be sent"))
        
        try:
            # Process due schedules
            if dry_run:
                # Just show what would be processed
                from surveys.models.email_schedule import EmailSchedule
                now = timezone.now()
                
                # Get all active schedules that are due
                due_schedules = EmailSchedule.objects.filter(
                    status='pending',
                    next_send__lte=now,
                    is_active=True
                )
                
                self.stdout.write(f"Found {due_schedules.count()} schedules due for processing:")
                
                for schedule in due_schedules:
                    if schedule.is_bulk and schedule.organization:
                        self.stdout.write(f"  - Bulk {schedule.email_type} for {schedule.organization.name} (ID: {schedule.id})")
                    else:
                        self.stdout.write(f"  - Email to {schedule.recipient_email} (ID: {schedule.id})")
            else:
                # Actually process the schedules
                results = EmailSchedulerService.process_due_schedules()
                
                self.stdout.write(self.style.SUCCESS(
                    f"Processed {results['total']} schedules: "
                    f"{results['success']} succeeded, {results['failed']} failed"
                ))
                
                # Log details of failures
                if results['failed'] > 0:
                    self.stdout.write(self.style.WARNING("Failed schedules:"))
                    for detail in results['details']:
                        if detail.get('status') == 'failed':
                            self.stdout.write(f"  - ID: {detail.get('id')}, Error: {detail.get('error')}")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing scheduled emails: {str(e)}"))
            logger.error(f"Error in process_scheduled_emails command: {str(e)}")
            raise
        
        self.stdout.write(self.style.SUCCESS(f"Completed scheduled email processing at {timezone.now()}"))
