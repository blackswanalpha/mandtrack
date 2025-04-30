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
    try:
        # Make sure the static directory exists
        from django.conf import settings
        import os
        import shutil

        # Create staticfiles directory if it doesn't exist
        if not os.path.exists(settings.STATIC_ROOT):
            os.makedirs(settings.STATIC_ROOT, exist_ok=True)

        # Run collectstatic command
        call_command('collectstatic', '--noinput', '--clear')

        # Copy static files to the root static directory for Vercel
        if os.path.exists('static'):
            print("Static directory already exists")
        else:
            print("Creating static directory")
            os.makedirs('static', exist_ok=True)

        # Copy CSS files
        for css_file in ['styles.css', 'enhanced-styles.css', 'animations.css', 'admin-portal.css', 'modern-sidebar.css', 'sidebar-animations.css']:
            src_path = os.path.join(settings.STATIC_ROOT, 'css', css_file)
            dest_path = os.path.join('static', 'css', css_file)

            # Create destination directory
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # Copy file if it exists
            if os.path.exists(src_path):
                print(f"Copying {src_path} to {dest_path}")
                shutil.copy2(src_path, dest_path)
            else:
                print(f"Warning: {src_path} does not exist")

        # Copy JS files
        for js_file in ['main.js', 'admin-portal.js', 'dashboard-charts.js', 'modern-sidebar.js', 'notifications.js', 'search.js', 'sidebar.js', 'theme-switcher.js']:
            src_path = os.path.join(settings.STATIC_ROOT, 'js', js_file)
            dest_path = os.path.join('static', 'js', js_file)

            # Create destination directory
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # Copy file if it exists
            if os.path.exists(src_path):
                print(f"Copying {src_path} to {dest_path}")
                shutil.copy2(src_path, dest_path)
            else:
                print(f"Warning: {src_path} does not exist")

        print("Static files collected and copied.")
    except Exception as e:
        print(f"Error collecting static files: {str(e)}")
        import traceback
        print(traceback.format_exc())

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
