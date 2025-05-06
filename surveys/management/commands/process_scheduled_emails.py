from django.core.management.base import BaseCommand
from surveys.email_utils import process_scheduled_emails
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process scheduled emails that are due to be sent'

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Processing scheduled emails...'))
            
            # Process scheduled emails
            sent_count = process_scheduled_emails()
            
            self.stdout.write(self.style.SUCCESS(f'Successfully sent {sent_count} scheduled emails.'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing scheduled emails: {str(e)}'))
            logger.error(f'Error processing scheduled emails: {str(e)}')
