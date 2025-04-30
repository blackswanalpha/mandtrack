#!/usr/bin/env python
"""
Build script for Vercel deployment.
This script runs migrations and creates a superuser.
"""

import os
import sys
import django
import subprocess

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.vercel_settings')

# Initialize Django
django.setup()

# Import Django models after setup
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.management import call_command

User = get_user_model()

def collect_static():
    """Collect static files."""
    print("Collecting static files...")
    call_command('collectstatic', '--noinput')
    print("Static files collected.")

def run_migrations():
    """Run database migrations."""
    print("Running migrations...")
    call_command('migrate', '--noinput')
    print("Migrations completed.")

def create_superuser():
    """Create a superuser if it doesn't exist."""
    print("Creating superuser...")
    try:
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='Admin@123456',
            first_name='Admin',
            last_name='User',
            is_active=True,
        )
        print("Superuser 'admin@example.com' created successfully!")
        return superuser
    except IntegrityError:
        print("Superuser 'admin@example.com' already exists.")
        return None
    except Exception as e:
        print(f"Error creating superuser: {str(e)}")
        return None

def main():
    """Main build function."""
    print("Starting Vercel build process...")
    
    # Collect static files
    collect_static()
    
    # Run migrations
    run_migrations()
    
    # Create superuser
    create_superuser()
    
    print("Vercel build process completed successfully!")

if __name__ == '__main__':
    main()
