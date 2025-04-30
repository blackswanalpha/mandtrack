"""
Script to reset migrations and create a fresh database.
"""
import os
import shutil
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

def reset_migrations():
    """Reset migrations and create a fresh database."""
    # List of apps to reset migrations for
    apps = ['users', 'surveys', 'feedback', 'analytics', 'dashboard', 'groups', 'core']
    
    # Remove migration files
    for app in apps:
        migrations_dir = os.path.join(app, 'migrations')
        if os.path.exists(migrations_dir):
            print(f"Removing migration files for {app}...")
            for filename in os.listdir(migrations_dir):
                if filename.startswith('0') and filename.endswith('.py'):
                    file_path = os.path.join(migrations_dir, filename)
                    os.remove(file_path)
                    print(f"  Removed {file_path}")
    
    # Create new migration files
    print("\nCreating new migration files...")
    os.system("python manage.py makemigrations users")
    os.system("python manage.py makemigrations surveys")
    os.system("python manage.py makemigrations feedback")
    os.system("python manage.py makemigrations analytics")
    os.system("python manage.py makemigrations dashboard")
    os.system("python manage.py makemigrations groups")
    os.system("python manage.py makemigrations core")
    
    # Create a superuser script
    with open('create_superuser.py', 'w') as f:
        f.write("""
from django.contrib.auth import get_user_model
from users.models import UserProfile

User = get_user_model()

# Create superuser if it doesn't exist
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123',
        role='admin',
        email_verified=True
    )
    
    # Create user profile
    UserProfile.objects.create(
        user=admin,
        bio="Admin user",
        preferences={}
    )
    
    print("Superuser created successfully.")
else:
    print("Superuser already exists.")
        """)
    
    print("\nMigration files created successfully.")
    print("Now you can run the following commands:")
    print("1. python manage.py migrate")
    print("2. python manage.py shell < create_superuser.py")
    print("3. python migrate_data.py")

if __name__ == "__main__":
    reset_migrations()
