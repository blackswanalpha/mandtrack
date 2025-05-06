from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from groups.models import Organization
from surveys.models import Questionnaire
from members.models import Member, MemberAccess

class Command(BaseCommand):
    help = 'Creates a test member and member access for testing'

    def handle(self, *args, **options):
        # Check if there are any organizations
        if not Organization.objects.exists():
            self.stdout.write(self.style.ERROR('No organizations found. Please create an organization first.'))
            return
        
        # Check if there are any questionnaires
        if not Questionnaire.objects.exists():
            self.stdout.write(self.style.ERROR('No questionnaires found. Please create a questionnaire first.'))
            return
        
        # Get the first organization
        organization = Organization.objects.first()
        
        # Get the first questionnaire
        questionnaire = Questionnaire.objects.first()
        
        # Create a test member
        member, created = Member.objects.get_or_create(
            member_number='TEST001',
            defaults={
                'name': 'Test Member',
                'email': 'test@example.com',
                'phone': '1234567890',
                'organization': organization,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created test member: {member}'))
        else:
            self.stdout.write(self.style.WARNING(f'Test member already exists: {member}'))
        
        # Create a test member access
        access_code = 'ACCESS123'
        member_access, created = MemberAccess.objects.get_or_create(
            member=member,
            questionnaire=questionnaire,
            access_code=access_code,
            defaults={
                'is_used': False,
                'expires_at': timezone.now() + timedelta(days=30)
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created test member access with code: {access_code}'))
        else:
            self.stdout.write(self.style.WARNING(f'Test member access already exists with code: {access_code}'))
        
        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))
        self.stdout.write(self.style.SUCCESS(f'Member Number: TEST001'))
        self.stdout.write(self.style.SUCCESS(f'Access Code: ACCESS123'))
