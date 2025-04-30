"""
Script to fix migration issues.
"""
import os
import django
import sys
import shutil

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Import Django modules after setup
from django.core.management import call_command

def backup_migrations():
    """Backup existing migrations"""
    print("Backing up existing migrations...")
    
    # Create backup directory if it doesn't exist
    if not os.path.exists('migrations_backup'):
        os.makedirs('migrations_backup')
    
    # List of apps to backup migrations for
    apps = ['users', 'surveys', 'feedback', 'analytics', 'dashboard', 'groups', 'core', 'accounts']
    
    # Backup migrations for each app
    for app in apps:
        migrations_dir = os.path.join(app, 'migrations')
        backup_dir = os.path.join('migrations_backup', app)
        
        if os.path.exists(migrations_dir):
            # Create app backup directory if it doesn't exist
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Copy migration files
            for filename in os.listdir(migrations_dir):
                if filename.endswith('.py'):
                    src = os.path.join(migrations_dir, filename)
                    dst = os.path.join(backup_dir, filename)
                    shutil.copy2(src, dst)
                    print(f"  Backed up {src} to {dst}")

def reset_migrations():
    """Reset migrations for all apps"""
    print("Resetting migrations...")
    
    # List of apps to reset migrations for
    apps = ['users', 'surveys', 'feedback', 'analytics', 'dashboard', 'groups', 'core', 'accounts']
    
    # Remove migration files for each app
    for app in apps:
        migrations_dir = os.path.join(app, 'migrations')
        if os.path.exists(migrations_dir):
            print(f"  Removing migration files for {app}...")
            for filename in os.listdir(migrations_dir):
                if filename.startswith('0') and filename.endswith('.py'):
                    file_path = os.path.join(migrations_dir, filename)
                    os.remove(file_path)
                    print(f"    Removed {file_path}")
                    
                # Also remove compiled Python files
                if filename.endswith('.pyc'):
                    file_path = os.path.join(migrations_dir, filename)
                    os.remove(file_path)
                    print(f"    Removed {file_path}")

def create_initial_migrations():
    """Create initial migrations for all apps"""
    print("Creating initial migrations...")
    
    # Create migrations for each app in a specific order
    apps = ['users', 'accounts', 'groups', 'surveys', 'feedback', 'analytics', 'dashboard', 'core']
    
    for app in apps:
        print(f"  Creating migrations for {app}...")
        call_command('makemigrations', app)

def apply_migrations():
    """Apply migrations in a specific order"""
    print("Applying migrations...")
    
    # Apply migrations for each app in a specific order
    apps = ['users', 'accounts', 'groups', 'surveys', 'feedback', 'analytics', 'dashboard', 'core']
    
    for app in apps:
        print(f"  Applying migrations for {app}...")
        try:
            call_command('migrate', app)
        except Exception as e:
            print(f"    Error applying migrations for {app}: {e}")
            print(f"    Skipping {app} migrations...")

def main():
    """Main function to fix migration issues"""
    try:
        # Backup existing migrations
        backup_migrations()
        
        # Reset migrations
        reset_migrations()
        
        # Create initial migrations
        create_initial_migrations()
        
        # Apply migrations
        apply_migrations()
        
        print("\nMigration fix completed!")
        print("If you encounter any issues, you can restore the backup migrations from the 'migrations_backup' directory.")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
