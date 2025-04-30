from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dashboard.models import Notification
import random
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate sample notifications for testing'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5, help='Number of notifications to generate')
        parser.add_argument('--user', type=str, help='Email of user to generate notifications for')

    def handle(self, *args, **options):
        count = options['count']
        user_email = options.get('user')
        
        # Get users
        if user_email:
            users = User.objects.filter(email=user_email)
            if not users.exists():
                self.stdout.write(self.style.ERROR(f'User with email {user_email} not found'))
                return
        else:
            users = User.objects.filter(is_staff=True)
            if not users.exists():
                self.stdout.write(self.style.ERROR('No staff users found'))
                return
        
        # Sample notification data
        notification_types = ['info', 'success', 'warning', 'error']
        titles = [
            'New questionnaire response',
            'System update scheduled',
            'User account created',
            'Questionnaire completed',
            'Data export ready',
            'Password changed',
            'New feature available',
            'Maintenance scheduled',
            'Account verification required',
            'Survey results available'
        ]
        messages = [
            'A new response has been submitted for your questionnaire.',
            'System update is scheduled for tomorrow at 2:00 PM.',
            'A new user account has been created in your organization.',
            'A patient has completed the questionnaire you sent.',
            'Your data export is ready for download.',
            'Your password has been changed successfully.',
            'A new feature is now available in your dashboard.',
            'System maintenance is scheduled for this weekend.',
            'Please verify your account to continue using all features.',
            'Survey results are now available for analysis.'
        ]
        
        # Generate notifications
        notifications_created = 0
        for user in users:
            for _ in range(count):
                # Random data
                notification_type = random.choice(notification_types)
                title_index = random.randint(0, len(titles) - 1)
                
                # Create notification
                created_at = timezone.now() - timedelta(days=random.randint(0, 7), 
                                                       hours=random.randint(0, 23), 
                                                       minutes=random.randint(0, 59))
                
                notification = Notification(
                    user=user,
                    title=titles[title_index],
                    message=messages[title_index],
                    notification_type=notification_type,
                    is_read=random.choice([True, False]),
                    created_at=created_at
                )
                notification.save()
                notifications_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {notifications_created} notifications'))
