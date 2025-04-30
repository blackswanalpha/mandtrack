"""
Script to test migrations on a test database.
"""
import os
import django
import sys

# Set up Django environment with test database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
os.environ['DJANGO_DATABASE'] = 'test'  # Use the test database

# Initialize Django
django.setup()

# Import Django modules after setup
from django.db import connections
from django.core.management import call_command
from django.conf import settings

def setup_test_database():
    """Set up the test database for migrations"""
    print("Setting up test database...")

    # Check if test database exists and remove it if it does
    if os.path.exists(settings.DATABASES['test']['NAME']):
        os.remove(settings.DATABASES['test']['NAME'])
        print(f"Removed existing test database: {settings.DATABASES['test']['NAME']}")

    # Create a new test database
    print("Creating new test database...")

    # Force Django to use the test database
    settings.DATABASES['default'] = settings.DATABASES['test']

    return True

def run_migrations():
    """Run all migrations on the test database"""
    print("Running migrations on test database...")

    # Make migrations for all apps
    call_command('makemigrations')

    # Apply migrations one app at a time in a specific order
    print("Applying migrations for auth...")
    call_command('migrate', 'auth')

    print("Applying migrations for contenttypes...")
    call_command('migrate', 'contenttypes')

    print("Applying migrations for users...")
    call_command('migrate', 'users')

    print("Applying migrations for accounts...")
    call_command('migrate', 'accounts')

    print("Applying migrations for groups...")
    call_command('migrate', 'groups')

    print("Applying migrations for surveys...")
    call_command('migrate', 'surveys')

    print("Applying migrations for feedback...")
    call_command('migrate', 'feedback')

    print("Applying migrations for analytics...")
    call_command('migrate', 'analytics', '0001_initial')

    # Apply remaining migrations
    print("Applying remaining migrations...")
    call_command('migrate')

    print("Migrations completed successfully!")

def create_superuser():
    """Create a superuser for testing"""
    print("Creating superuser...")

    # Import the User model
    from django.contrib.auth import get_user_model
    from users.models import UserProfile

    User = get_user_model()

    # Check if admin user exists
    if not User.objects.filter(username='admin').exists():
        # Create admin user
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin',
            email_verified=True
        )

        # Create user profile
        UserProfile.objects.create(
            user=admin_user,
            bio="Admin user",
            preferences={}
        )

        print(f"Created admin user: {admin_user.username}")
    else:
        print("Admin user already exists. Skipping...")

def main():
    """Main function to run the test migrations"""
    try:
        # Set up test database
        if setup_test_database():
            # Run migrations
            run_migrations()

            # Create superuser
            create_superuser()

            print("\nTest migrations completed successfully!")
            print("You can now apply these migrations to your production database.")
            print("Run: python manage.py migrate")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
