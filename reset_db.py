"""
Script to reset the database and create tables from scratch.
"""
import os
import django
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

from django.conf import settings

def reset_database():
    """Reset the database and create tables from scratch."""
    print("Connecting to database...")
    
    # Get database settings
    db_settings = settings.DATABASES['default']
    db_name = db_settings['NAME']
    db_user = db_settings['USER']
    db_password = db_settings['PASSWORD']
    db_host = db_settings['HOST']
    db_port = db_settings['PORT']
    
    # Connect to the database
    try:
        # Connect to the database server (not the specific database)
        conn = psycopg2.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Drop the database if it exists
        print(f"Dropping database {db_name} if it exists...")
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        
        # Create the database
        print(f"Creating database {db_name}...")
        cursor.execute(f"CREATE DATABASE {db_name}")
        
        # Close the connection
        cursor.close()
        conn.close()
        
        print("Database reset successfully.")
        
        # Run migrations
        print("Running migrations...")
        os.system("python manage.py migrate")
        
        # Create a superuser
        print("Creating superuser...")
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role='admin',
                email_verified=True
            )
            print("Superuser created successfully.")
        else:
            print("Superuser already exists.")
        
        print("Database setup completed successfully.")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    reset_database()
