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

        # Create a list of all CSS and JS files to ensure they exist
        css_files = [
            'styles.css',
            'enhanced-styles.css',
            'animations.css',
            'admin-portal.css',
            'modern-sidebar.css',
            'sidebar-animations.css',
            'tailwind-custom.css'
        ]

        js_files = [
            'main.js',
            'admin-portal.js',
            'dashboard-charts.js',
            'modern-sidebar.js',
            'notifications.js',
            'search.js',
            'sidebar.js',
            'theme-switcher.js'
        ]

        # Ensure all CSS files exist
        for css_file in css_files:
            src_path = os.path.join('static', 'css', css_file)
            dest_path = os.path.join(settings.STATIC_ROOT, 'css', css_file)

            # Create destination directory
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # If the file doesn't exist in staticfiles but exists in static, copy it
            if not os.path.exists(dest_path) and os.path.exists(src_path):
                print(f"Copying {src_path} to {dest_path}")
                shutil.copy2(src_path, dest_path)
            # If the file doesn't exist in either location, create an empty file
            elif not os.path.exists(dest_path) and not os.path.exists(src_path):
                print(f"Creating empty file {dest_path}")
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, 'w') as f:
                    f.write('/* Auto-generated empty file */')

        # Ensure all JS files exist
        for js_file in js_files:
            src_path = os.path.join('static', 'js', js_file)
            dest_path = os.path.join(settings.STATIC_ROOT, 'js', js_file)

            # Create destination directory
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # If the file doesn't exist in staticfiles but exists in static, copy it
            if not os.path.exists(dest_path) and os.path.exists(src_path):
                print(f"Copying {src_path} to {dest_path}")
                shutil.copy2(src_path, dest_path)
            # If the file doesn't exist in either location, create an empty file
            elif not os.path.exists(dest_path) and not os.path.exists(src_path):
                print(f"Creating empty file {dest_path}")
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, 'w') as f:
                    f.write('// Auto-generated empty file')

        # Now copy all files from staticfiles back to static for Vercel
        print("Copying all files from staticfiles to static")
        for root, dirs, files in os.walk(settings.STATIC_ROOT):
            for file in files:
                staticfiles_path = os.path.join(root, file)
                # Get the relative path from STATIC_ROOT
                rel_path = os.path.relpath(staticfiles_path, settings.STATIC_ROOT)
                static_path = os.path.join('static', rel_path)

                # Create destination directory
                os.makedirs(os.path.dirname(static_path), exist_ok=True)

                # Copy the file
                print(f"Copying {staticfiles_path} to {static_path}")
                shutil.copy2(staticfiles_path, static_path)

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
        # Try to create the specified admin user
        superuser = User.objects.create_superuser(
            email='admin12@example.com',
            password='admin1234',
            first_name='Admin',
            last_name='User',
            is_active=True,
        )
        print("Superuser 'admin12@example.com' created successfully!")
        return superuser
    except IntegrityError:
        print("Superuser 'admin12@example.com' already exists.")
        # Check if we need to update the password
        try:
            admin_user = User.objects.get(email='admin12@example.com')
            admin_user.set_password('admin1234')
            admin_user.save()
            print("Updated password for 'admin12@example.com'")
        except Exception as e:
            print(f"Error updating admin password: {str(e)}")
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
