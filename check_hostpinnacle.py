#!/usr/bin/env python
"""
HostPinnacle Environment Check Script

This script checks if the environment is properly configured for running
the MindTrack application on a HostPinnacle server.

Usage:
    python check_hostpinnacle.py
"""

import os
import sys
import platform
import subprocess
import importlib.util
import socket
import datetime

def print_header(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def check_python():
    """Check Python version and installation."""
    print_header("Python Environment")
    print(f"Python Version: {platform.python_version()}")
    print(f"Python Path: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Hostname: {socket.gethostname()}")
    print(f"Current Time: {datetime.datetime.now()}")
    print(f"Current Directory: {os.getcwd()}")

def check_django():
    """Check Django installation."""
    print_header("Django Installation")
    try:
        import django
        print(f"Django Version: {django.__version__}")
        print(f"Django Path: {django.__file__}")
        
        # Check if settings can be imported
        try:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.hostpinnacle_settings')
            from django.conf import settings
            print(f"Settings Module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
            print(f"Debug Mode: {settings.DEBUG}")
            print(f"Allowed Hosts: {settings.ALLOWED_HOSTS}")
            print(f"Database Engine: {settings.DATABASES['default']['ENGINE']}")
            print(f"Static Root: {settings.STATIC_ROOT}")
            print(f"Media Root: {settings.MEDIA_ROOT}")
        except Exception as e:
            print(f"Error importing settings: {e}")
    except ImportError:
        print("Django is not installed.")

def check_passenger():
    """Check Passenger installation."""
    print_header("Passenger Environment")
    passenger_env = {k: v for k, v in os.environ.items() if 'PASSENGER' in k}
    if passenger_env:
        print("Passenger environment variables found:")
        for key, value in passenger_env.items():
            print(f"  {key}: {value}")
    else:
        print("No Passenger environment variables found.")
    
    # Check if passenger_wsgi.py exists
    if os.path.exists('passenger_wsgi.py'):
        print("passenger_wsgi.py file found.")
    else:
        print("passenger_wsgi.py file not found.")

def check_gunicorn():
    """Check Gunicorn installation."""
    print_header("Gunicorn Installation")
    try:
        import gunicorn
        print(f"Gunicorn Version: {gunicorn.__version__}")
        print(f"Gunicorn Path: {gunicorn.__file__}")
    except ImportError:
        print("Gunicorn is not installed.")

def check_dependencies():
    """Check required dependencies."""
    print_header("Dependencies")
    dependencies = [
        'django', 'gunicorn', 'psycopg2', 'whitenoise', 'django-environ',
        'pillow', 'django-crispy-forms', 'crispy-bootstrap5', 'django-allauth',
        'django-htmx', 'qrcode'
    ]
    
    for package in dependencies:
        spec = importlib.util.find_spec(package.replace('-', '_'))
        if spec is not None:
            try:
                module = importlib.import_module(package.replace('-', '_'))
                version = getattr(module, '__version__', 'unknown')
                print(f"{package}: Installed (version: {version})")
            except ImportError:
                print(f"{package}: Found but could not import")
        else:
            print(f"{package}: Not installed")

def check_file_permissions():
    """Check file permissions for key files."""
    print_header("File Permissions")
    files_to_check = [
        'passenger_wsgi.py',
        'server.py',
        'manage.py',
        'mindtrack/wsgi.py',
        'mindtrack/settings.py',
        'mindtrack/hostpinnacle_settings.py'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            permissions = oct(os.stat(file_path).st_mode)[-3:]
            print(f"{file_path}: {permissions}")
        else:
            print(f"{file_path}: File not found")

def check_database_connection():
    """Check database connection."""
    print_header("Database Connection")
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.hostpinnacle_settings')
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"Database connection successful")
            print(f"Database version: {version}")
            
            # Check if tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            print(f"Number of tables: {len(tables)}")
            print("Tables:")
            for table in tables[:10]:  # Show only first 10 tables
                print(f"  - {table[0]}")
            if len(tables) > 10:
                print(f"  ... and {len(tables) - 10} more")
    except Exception as e:
        print(f"Database connection error: {e}")

def main():
    """Main function."""
    print_header("HostPinnacle Environment Check")
    print(f"Check Time: {datetime.datetime.now()}")
    
    check_python()
    check_django()
    check_passenger()
    check_gunicorn()
    check_dependencies()
    check_file_permissions()
    check_database_connection()
    
    print("\nEnvironment check completed.")

if __name__ == '__main__':
    main()
