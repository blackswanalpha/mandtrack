"""
Script to reset the migration history in the database.
"""
import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Import Django modules after setup
from django.db import connection

def reset_migration_history():
    """Reset the migration history in the database"""
    print("Resetting migration history in the database...")
    
    with connection.cursor() as cursor:
        # Check if django_migrations table exists
        cursor.execute("SELECT to_regclass('django_migrations');")
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            # Delete all migration records
            cursor.execute("DELETE FROM django_migrations;")
            print("Migration history has been reset.")
        else:
            print("django_migrations table does not exist. No action needed.")

def main():
    """Main function to reset migration history"""
    try:
        # Reset migration history
        reset_migration_history()
        
        print("\nMigration history reset completed!")
        print("You can now run migrations with the --fake-initial option:")
        print("python manage.py migrate --fake-initial")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
