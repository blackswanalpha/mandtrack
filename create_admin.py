import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Import models
from users.models import User
from accounts.models import AdminProfile

# Create admin user
def create_admin_user():
    # Check if admin user already exists
    if User.objects.filter(email='admin@example.com').exists():
        print("Admin user already exists")
        return
    
    # Create admin user
    admin_user = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='admin123',
        first_name='Admin',
        last_name='User',
        is_staff=True,
        is_superuser=True,
        role='admin'
    )
    
    # Create admin profile
    AdminProfile.objects.create(
        user=admin_user,
        department='IT',
        position='Administrator',
        employee_id='ADMIN001',
        access_level='full'
    )
    
    print(f"Admin user created: {admin_user.email}")

if __name__ == '__main__':
    create_admin_user()
