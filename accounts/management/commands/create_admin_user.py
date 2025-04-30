from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import User
from accounts.models import AdminProfile


class Command(BaseCommand):
    help = 'Creates an admin user for the admin portal'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for the admin user')
        parser.add_argument('--email', type=str, help='Email for the admin user')
        parser.add_argument('--password', type=str, help='Password for the admin user')
        parser.add_argument('--first_name', type=str, help='First name for the admin user')
        parser.add_argument('--last_name', type=str, help='Last name for the admin user')
        parser.add_argument('--department', type=str, help='Department for the admin user')
        parser.add_argument('--position', type=str, help='Position for the admin user')

    def handle(self, *args, **options):
        username = options.get('username') or input('Enter username: ')
        email = options.get('email') or input('Enter email: ')
        password = options.get('password') or input('Enter password: ')
        first_name = options.get('first_name') or input('Enter first name (optional): ')
        last_name = options.get('last_name') or input('Enter last name (optional): ')
        department = options.get('department') or input('Enter department (optional): ')
        position = options.get('position') or input('Enter position (optional): ')

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'User with username "{username}" already exists'))
            return
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f'User with email "{email}" already exists'))
            return

        try:
            with transaction.atomic():
                # Create the user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role='admin',
                    is_staff=True,
                    is_superuser=True,
                    email_verified=True
                )

                # Create admin profile
                admin_profile = AdminProfile.objects.create(
                    user=user,
                    department=department,
                    position=position,
                    access_level='full'
                )

                self.stdout.write(self.style.SUCCESS(f'Successfully created admin user: {username}'))
                self.stdout.write(self.style.SUCCESS(f'Email: {email}'))
                self.stdout.write(self.style.SUCCESS(f'Role: Administrator'))
                self.stdout.write(self.style.SUCCESS(f'Access Level: Full'))
                self.stdout.write(self.style.SUCCESS(f'Login at: /admin-portal/login/'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating admin user: {str(e)}'))
