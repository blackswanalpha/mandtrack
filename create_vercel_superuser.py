#!/usr/bin/env python
"""
Script to create a superuser during Vercel deployment.
"""

import os
import django
from django.db import IntegrityError

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.vercel_settings')
django.setup()

# Import User model after Django setup
from django.contrib.auth import get_user_model
User = get_user_model()

# Superuser credentials
SUPERUSER_EMAIL = 'admin@example.com'
SUPERUSER_PASSWORD = 'Admin@123456'

def create_superuser():
    """Create a superuser if it doesn't exist."""
    try:
        superuser = User.objects.create_superuser(
            email=SUPERUSER_EMAIL,
            password=SUPERUSER_PASSWORD,
            first_name='Admin',
            last_name='User',
            is_active=True,
        )
        print(f"Superuser '{SUPERUSER_EMAIL}' created successfully!")
        return superuser
    except IntegrityError:
        print(f"Superuser '{SUPERUSER_EMAIL}' already exists.")
        return None
    except Exception as e:
        print(f"Error creating superuser: {str(e)}")
        return None

if __name__ == '__main__':
    create_superuser()
