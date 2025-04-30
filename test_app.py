"""
Script to run the Django development server for testing.
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

def run_server():
    """Run the Django development server."""
    from django.core.management import execute_from_command_line
    
    # Run the development server
    print("Starting Django development server...")
    execute_from_command_line(['manage.py', 'runserver', '8000'])

if __name__ == "__main__":
    run_server()
