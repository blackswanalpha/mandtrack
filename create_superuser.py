
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
        