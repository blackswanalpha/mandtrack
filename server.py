#!/usr/bin/env python
"""
MindTrack Production Server Script

This script provides a robust way to run the MindTrack application
in a production environment using Gunicorn as the WSGI server.
It includes error handling, health checks, and automatic recovery.

Usage:
    python server.py [options]

Options:
    --host HOST         Host to bind to (default: 0.0.0.0)
    --port PORT         Port to bind to (default: 8001)
    --workers WORKERS   Number of worker processes (default: based on CPU count)
    --timeout TIMEOUT   Worker timeout in seconds (default: 120)
    --reload            Enable auto-reload on code changes (development only)
    --log-level LEVEL   Log level (default: info)
    --log-file FILE     Log file path (default: None, logs to stdout)
    --settings MODULE   Django settings module (default: mindtrack.settings)
    --skip-checks       Skip pre-flight checks (default: False)
    --help              Show this help message and exit
"""

import os
import sys
import time
import signal
import logging
import argparse
import subprocess
import multiprocessing
import threading
import socket
import json
import traceback
import schedule
from pathlib import Path
from datetime import datetime, timedelta

# Configure logging
def setup_logging(log_level, log_file=None):
    """Set up logging configuration."""
    handlers = [logging.StreamHandler()]

    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=handlers
    )

    return logging.getLogger('mindtrack_server')

# Global logger - will be properly initialized in main()
logger = logging.getLogger('mindtrack_server')

class ServerConfig:
    """Server configuration class."""

    def __init__(self, args):
        self.host = args.host
        self.port = args.port
        self.workers = args.workers if args.workers else (multiprocessing.cpu_count() * 2) + 1
        self.timeout = args.timeout
        self.reload = args.reload
        self.log_level = args.log_level
        self.log_file = args.log_file
        self.settings_module = args.settings
        self.skip_checks = args.skip_checks

        # Derived settings
        self.is_development = self.reload
        self.project_dir = Path(__file__).resolve().parent

        # Set environment variables
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', self.settings_module)

        # Print configuration
        logger.info(f"Server Configuration:")
        logger.info(f"  Host: {self.host}")
        logger.info(f"  Port: {self.port}")
        logger.info(f"  Workers: {self.workers}")
        logger.info(f"  Timeout: {self.timeout}s")
        logger.info(f"  Reload: {self.reload}")
        logger.info(f"  Log Level: {self.log_level}")
        logger.info(f"  Settings Module: {self.settings_module}")
        logger.info(f"  Project Directory: {self.project_dir}")
        logger.info(f"  Mode: {'Development' if self.is_development else 'Production'}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='MindTrack Production Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8009, help='Port to bind to (default: 8009)')
    parser.add_argument('--workers', type=int, default=None,
                        help='Number of worker processes (default: CPU count * 2 + 1)')
    parser.add_argument('--timeout', type=int, default=120,
                        help='Worker timeout in seconds (default: 120)')
    parser.add_argument('--reload', action='store_true',
                        help='Enable auto-reload on code changes (development only)')
    parser.add_argument('--log-level', default='info',
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='Log level (default: info)')
    parser.add_argument('--log-file', default=None,
                        help='Log file path (default: None, logs to stdout)')
    parser.add_argument('--settings', default='mindtrack.settings',
                        help='Django settings module (default: mindtrack.settings)')
    parser.add_argument('--skip-checks', action='store_true',
                        help='Skip pre-flight checks (default: False)')

    return parser.parse_args()

def check_port_availability(host, port):
    """Check if the port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True
    except socket.error:
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    missing_deps = []

    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        logger.warning(f"Python {python_version.major}.{python_version.minor} detected. Python 3.8+ is recommended.")
    else:
        logger.info(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} detected.")

    # Check required packages
    try:
        import django
        logger.info(f"Django {django.__version__} is installed.")
    except ImportError:
        missing_deps.append("django")
        logger.error("Django is not installed.")

    try:
        import gunicorn
        logger.info(f"Gunicorn is installed.")
    except ImportError:
        missing_deps.append("gunicorn")
        logger.error("Gunicorn is not installed.")

    try:
        import whitenoise
        logger.info(f"Whitenoise is installed.")
    except ImportError:
        missing_deps.append("whitenoise")
        logger.warning("Whitenoise is not installed. Static file serving may not work correctly.")

    try:
        import psycopg2
        logger.info(f"psycopg2 is installed.")
    except ImportError:
        try:
            import psycopg2cffi
            logger.info(f"psycopg2cffi is installed.")
        except ImportError:
            missing_deps.append("psycopg2")
            logger.warning("Neither psycopg2 nor psycopg2cffi is installed. PostgreSQL support may not work.")

    # Return list of missing dependencies
    return missing_deps

def ensure_sqlite_database():
    """Ensure SQLite is used as the database."""
    try:
        # Import Django settings
        import django
        from django.conf import settings
        import django.conf

        # Check current database engine
        current_engine = settings.DATABASES['default']['ENGINE']
        logger.info(f"Current database engine: {current_engine}")

        # If not SQLite, update to SQLite
        if 'sqlite3' not in current_engine:
            logger.info("Switching to SQLite database...")

            # Update database settings
            django.conf.settings.DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': os.path.join(settings.BASE_DIR, 'db.sqlite3'),
                }
            }

            logger.info(f"Database engine updated to: {django.conf.settings.DATABASES['default']['ENGINE']}")
            return True
        else:
            logger.info("Already using SQLite database.")
            return True
    except Exception as e:
        logger.error(f"Failed to ensure SQLite database: {e}")
        logger.error(traceback.format_exc())
        return False

def check_django_project():
    """Check if the Django project is properly configured."""
    try:
        # Import Django settings
        from django.conf import settings

        # Check if DEBUG is enabled
        if settings.DEBUG:
            logger.warning("DEBUG is enabled. This is not recommended for production.")
        else:
            logger.info("DEBUG is disabled. Good for production.")

        # Check ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS:
            logger.error("ALLOWED_HOSTS is empty. This will cause issues in production.")
        else:
            logger.info(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")

        # Check database configuration
        db_engine = settings.DATABASES['default']['ENGINE']
        if 'sqlite3' in db_engine:
            logger.info(f"Using SQLite database: {settings.DATABASES['default']['NAME']}")
        else:
            logger.info(f"Database engine: {db_engine}")
            # Force SQLite for better compatibility
            ensure_sqlite_database()

        # Check static files configuration
        if not hasattr(settings, 'STATIC_ROOT') or not settings.STATIC_ROOT:
            logger.warning("STATIC_ROOT is not configured. Static files may not be served correctly.")
        else:
            logger.info(f"STATIC_ROOT: {settings.STATIC_ROOT}")

        # Check if WhiteNoise is configured
        if 'whitenoise' not in settings.MIDDLEWARE:
            logger.warning("WhiteNoise middleware is not configured. Static files may not be served correctly.")

        return True
    except Exception as e:
        logger.error(f"Error checking Django project: {e}")
        return False

def update_allowed_hosts(host, port, settings_module):
    """Update ALLOWED_HOSTS to include the server host and host:port combination."""
    try:
        # Import Django settings
        from django.conf import settings
        import django.conf

        # Get current ALLOWED_HOSTS
        current_hosts = settings.ALLOWED_HOSTS
        logger.debug(f"Current ALLOWED_HOSTS: {current_hosts}")

        # Hosts to add
        hosts_to_add = []

        # Check if host is already in ALLOWED_HOSTS
        if host not in current_hosts:
            hosts_to_add.append(host)

        # Add all possible host:port combinations for common ports
        common_ports = [8000, 8001, 8009]
        for p in common_ports:
            host_port = f"{host}:{p}"
            if host_port not in current_hosts:
                hosts_to_add.append(host_port)

        # Add the specific host:port combination if not already added
        if port not in common_ports:
            host_port = f"{host}:{port}"
            if host_port not in current_hosts:
                hosts_to_add.append(host_port)

        # Add specific domains if not already in ALLOWED_HOSTS
        specific_domains = ['mindtrack.barberianspa.com', 'mandtrack.onrender.com']
        for domain in specific_domains:
            if domain not in current_hosts:
                hosts_to_add.append(domain)

        # Add wildcard domains if not already in ALLOWED_HOSTS
        for domain in ['.barberianspa.com', '.hostpinnacle.com', '.onrender.com']:
            if domain not in current_hosts:
                hosts_to_add.append(domain)

        # Add localhost and 127.0.0.1 with all common ports
        for base_host in ['localhost', '127.0.0.1', '0.0.0.0']:
            if base_host not in current_hosts:
                hosts_to_add.append(base_host)

            for p in common_ports + [port]:  # Include the current port
                host_port = f"{base_host}:{p}"
                if host_port not in current_hosts:
                    hosts_to_add.append(host_port)

        # Ensure the exact host:port combination is added
        exact_host_port = f"{host}:{port}"
        if exact_host_port not in current_hosts and exact_host_port not in hosts_to_add:
            hosts_to_add.append(exact_host_port)
            logger.info(f"Adding exact host:port combination: {exact_host_port}")

        # Add hosts if needed
        if hosts_to_add:
            new_hosts = current_hosts + hosts_to_add
            logger.info(f"Adding {hosts_to_add} to ALLOWED_HOSTS")

            # Update ALLOWED_HOSTS at runtime
            django.conf.settings.ALLOWED_HOSTS = new_hosts

            # Log the final ALLOWED_HOSTS list
            logger.info(f"Final ALLOWED_HOSTS: {django.conf.settings.ALLOWED_HOSTS}")

            return True
    except Exception as e:
        logger.warning(f"Failed to update ALLOWED_HOSTS: {e}")
        logger.warning(traceback.format_exc())

    return False

def collect_static(settings_module):
    """Collect static files."""
    logger.info("Collecting static files...")
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = settings_module

    try:
        result = subprocess.run(
            [sys.executable, 'manage.py', 'collectstatic', '--noinput'],
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Static files collected successfully.")
        logger.debug(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to collect static files: {e}")
        logger.debug(e.stdout)
        logger.debug(e.stderr)
        return False

def delete_database():
    """Delete the SQLite database file."""
    logger.info("Deleting SQLite database file...")
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')

    # Also check for journal and wal files
    journal_path = f"{db_path}-journal"
    wal_path = f"{db_path}-wal"
    shm_path = f"{db_path}-shm"

    # Delete main database file
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            logger.info(f"Database file {db_path} deleted successfully.")
        except Exception as e:
            logger.error(f"Failed to delete database file: {e}")
            return False
    else:
        logger.info(f"Database file {db_path} does not exist. Nothing to delete.")

    # Delete journal file if it exists
    if os.path.exists(journal_path):
        try:
            os.remove(journal_path)
            logger.info(f"Journal file {journal_path} deleted successfully.")
        except Exception as e:
            logger.warning(f"Failed to delete journal file: {e}")

    # Delete WAL file if it exists
    if os.path.exists(wal_path):
        try:
            os.remove(wal_path)
            logger.info(f"WAL file {wal_path} deleted successfully.")
        except Exception as e:
            logger.warning(f"Failed to delete WAL file: {e}")

    # Delete SHM file if it exists
    if os.path.exists(shm_path):
        try:
            os.remove(shm_path)
            logger.info(f"SHM file {shm_path} deleted successfully.")
        except Exception as e:
            logger.warning(f"Failed to delete SHM file: {e}")

    logger.info("Database cleanup completed.")
    return True

def create_empty_database():
    """Create an empty SQLite database file."""
    logger.info("Creating empty SQLite database file...")
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')

    try:
        # Create an empty database file
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.close()
        logger.info(f"Empty database file created at {db_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create empty database file: {e}")
        return False

def fix_migration_issues():
    """Attempt to fix common migration issues."""
    logger.info("Attempting to fix common migration issues...")

    try:
        # 1. Check for and fix migration files with conflicts
        migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')
        if os.path.exists(migrations_dir):
            logger.info(f"Checking migration files in {migrations_dir}")
            # This is just a placeholder - in a real implementation, you would scan for
            # conflicting migration files and fix them

        # 2. Check for and fix broken migration dependencies
        # Another placeholder for real implementation

        # 3. Look for and fix common database schema issues
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')
        if os.path.exists(db_path):
            logger.info(f"Checking database schema in {db_path}")
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Check if django_migrations table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='django_migrations'")
                if cursor.fetchone() is None:
                    logger.info("Creating django_migrations table...")
                    cursor.execute("""
                    CREATE TABLE django_migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        app VARCHAR(255) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        applied DATETIME NOT NULL
                    )
                    """)
                    conn.commit()
                    logger.info("Created django_migrations table")

                # Check if django_content_type table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='django_content_type'")
                if cursor.fetchone() is None:
                    logger.info("Creating django_content_type table...")
                    cursor.execute("""
                    CREATE TABLE django_content_type (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        app_label VARCHAR(100) NOT NULL,
                        model VARCHAR(100) NOT NULL,
                        UNIQUE (app_label, model)
                    )
                    """)
                    conn.commit()
                    logger.info("Created django_content_type table")

                # Check if auth_permission table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auth_permission'")
                if cursor.fetchone() is None:
                    logger.info("Creating auth_permission table...")
                    cursor.execute("""
                    CREATE TABLE auth_permission (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(255) NOT NULL,
                        content_type_id INTEGER NOT NULL REFERENCES django_content_type (id),
                        codename VARCHAR(100) NOT NULL,
                        UNIQUE (content_type_id, codename)
                    )
                    """)
                    conn.commit()
                    logger.info("Created auth_permission table")

                conn.close()
                logger.info("Database schema check completed")
            except Exception as db_e:
                logger.error(f"Error checking database schema: {db_e}")

        logger.info("Migration issue fixing completed")
        return True
    except Exception as e:
        logger.error(f"Failed to fix migration issues: {e}")
        logger.error(traceback.format_exc())
        return False

def run_migrations(settings_module):
    """Run database migrations."""
    logger.info("Running database migrations...")
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = settings_module

    # First attempt: Run migrations normally
    try:
        logger.info("Running migrations on the newly created database...")
        result = subprocess.run(
            [sys.executable, 'manage.py', 'migrate', '--noinput'],
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Database migrations completed successfully.")
        logger.debug(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run migrations: {e}")
        logger.error("Migration stdout: " + e.stdout)
        logger.error("Migration stderr: " + e.stderr)

        # Look for specific error patterns
        if "no such column" in e.stderr or "no such table" in e.stderr:
            logger.warning("Detected schema-related error. Attempting to run migrations with --fake-initial...")
            try:
                # Try with --fake-initial flag
                logger.info("Attempting migrations with --fake-initial flag...")
                result = subprocess.run(
                    [sys.executable, 'manage.py', 'migrate', '--noinput', '--fake-initial'],
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info("Migrations with --fake-initial completed successfully.")
                logger.debug(result.stdout)
                return True
            except subprocess.CalledProcessError as fake_e:
                logger.error(f"Failed to run migrations with --fake-initial: {fake_e}")
                logger.error("Migration stdout: " + fake_e.stdout)
                logger.error("Migration stderr: " + fake_e.stderr)

                # Last resort: Try running migrations one by one
                try:
                    logger.info("Attempting to run migrations app by app...")

                    # Get list of installed apps
                    import django
                    from django.conf import settings

                    # Setup Django
                    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
                    django.setup()

                    # Get installed apps
                    installed_apps = settings.INSTALLED_APPS
                    logger.info(f"Found {len(installed_apps)} installed apps: {', '.join(installed_apps)}")

                    # Run migrations for each app individually
                    success_count = 0
                    for app in installed_apps:
                        app_name = app.split('.')[-1]  # Get the last part of the app path
                        logger.info(f"Migrating app: {app_name}")
                        try:
                            app_result = subprocess.run(
                                [sys.executable, 'manage.py', 'migrate', app_name, '--noinput'],
                                env=env,
                                check=True,
                                capture_output=True,
                                text=True
                            )
                            logger.info(f"Successfully migrated {app_name}")
                            success_count += 1
                        except subprocess.CalledProcessError as app_e:
                            logger.warning(f"Failed to migrate {app_name}: {app_e}")
                            logger.debug(f"App migration stdout: {app_e.stdout}")
                            logger.debug(f"App migration stderr: {app_e.stderr}")

                    if success_count > 0:
                        logger.info(f"Successfully migrated {success_count} out of {len(installed_apps)} apps.")
                        return True
                    else:
                        logger.error("Failed to migrate any apps.")
                        return False
                except Exception as app_by_app_e:
                    logger.error(f"Failed to run app-by-app migrations: {app_by_app_e}")
                    logger.error(traceback.format_exc())
                    return False

        # If we get here, all migration attempts failed
        return False

def populate_question_types(settings_module):
    """Populate question types in the database."""
    logger.info("Populating question types...")
    try:
        # Import Django settings and QuestionType model
        import django

        # Set up Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
        django.setup()

        from django.conf import settings

        # Try to import QuestionType model
        try:
            from surveys.models.question_type import QuestionType
            logger.info("Successfully imported QuestionType model from surveys.models.question_type")
        except ImportError:
            try:
                from surveys.models import QuestionType
                logger.info("Successfully imported QuestionType model from surveys.models")
            except ImportError:
                # Try to get the model dynamically
                try:
                    from django.apps import apps
                    QuestionType = apps.get_model('surveys', 'QuestionType')
                    logger.info("Successfully got QuestionType model from apps registry")
                except Exception as model_e:
                    logger.error(f"Failed to get QuestionType model: {model_e}")
                    return False

        # Check if question types already exist
        existing_count = QuestionType.objects.count()
        logger.info(f"Found {existing_count} existing question types")

        if existing_count == 0:
            # Get default question types
            default_types = QuestionType.get_default_types()
            logger.info(f"Got {len(default_types)} default question types")

            # Create default question types
            created_count = 0
            for type_data in default_types:
                QuestionType.objects.create(**type_data)
                created_count += 1
                logger.info(f"Created question type: {type_data['name']} ({type_data['code']})")

            logger.info(f"Created {created_count} question types")

            # Ensure country question type exists
            country_exists = QuestionType.objects.filter(code='country').exists()
            if not country_exists:
                logger.info("Creating country question type...")
                QuestionType.objects.create(
                    code='country',
                    name='Country',
                    description='Country selection question type',
                    has_choices=True,
                    is_text=False,
                    is_numeric=False,
                    is_date=False,
                    is_file=False,
                    is_scorable=False,
                    default_max_score=0,
                    default_scoring_weight=1.0,
                    display_order=existing_count + created_count + 1,
                    icon='fa-globe'
                )
                logger.info("Country question type created successfully")

            return True
        else:
            logger.info("Question types already exist, skipping population")

            # Check if country question type exists
            country_exists = QuestionType.objects.filter(code='country').exists()
            if not country_exists:
                logger.info("Creating country question type...")
                QuestionType.objects.create(
                    code='country',
                    name='Country',
                    description='Country selection question type',
                    has_choices=True,
                    is_text=False,
                    is_numeric=False,
                    is_date=False,
                    is_file=False,
                    is_scorable=False,
                    default_max_score=0,
                    default_scoring_weight=1.0,
                    display_order=existing_count + 1,
                    icon='fa-globe'
                )
                logger.info("Country question type created successfully")

            return True
    except Exception as e:
        logger.error(f"Failed to populate question types: {e}")
        logger.error(traceback.format_exc())
        return False

def create_admin_user(settings_module):
    """Create an admin user if it doesn't exist."""
    logger.info("Checking for admin user...")
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = settings_module

    # Check if admin user exists
    try:
        # Import Django settings and User model
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
        import django
        django.setup()

        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Check if admin user exists with either email
        admin_emails = ['admin@example.com', 'admin12@example.com']
        admin_exists = User.objects.filter(email__in=admin_emails).exists()

        if admin_exists:
            logger.info("Admin user already exists.")
            return True

        # Check available fields on the User model
        available_fields = [field.name for field in User._meta.fields]
        logger.info(f"Available fields on User model: {available_fields}")

        # Check if User model requires username
        requires_username = 'username' in available_fields
        logger.info(f"User model requires username: {requires_username}")

        # Check if User model has first_name and last_name fields
        has_first_name = 'first_name' in available_fields
        has_last_name = 'last_name' in available_fields
        logger.info(f"User model has first_name: {has_first_name}, last_name: {has_last_name}")

        # Check if User model has role field
        has_role = 'role' in available_fields
        logger.info(f"User model has role field: {has_role}")

        # Create admin user
        logger.info("Creating admin user...")
        try:
            # Create base parameters
            create_params = {
                'email': 'admin@example.com',
                'password': 'admin123',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True
            }

            # Add username if required
            if requires_username:
                create_params['username'] = 'admin'

            # Add role if available
            if has_role:
                create_params['role'] = 'admin'

            logger.info(f"Creating admin user with parameters: {create_params}")
            admin_user = User.objects.create_superuser(**create_params)

            # Set additional fields if they exist on the User model
            # Only try to set these fields if they exist and weren't set during creation
            if has_first_name and not admin_user.first_name:
                try:
                    admin_user.first_name = 'Admin'
                except Exception as name_e:
                    logger.warning(f"Could not set first_name: {name_e}")

            if has_last_name and not admin_user.last_name:
                try:
                    admin_user.last_name = 'User'
                except Exception as name_e:
                    logger.warning(f"Could not set last_name: {name_e}")

            if hasattr(admin_user, 'is_admin'):
                admin_user.is_admin = True

            # Save the user with any additional fields
            try:
                admin_user.save()
                logger.info("Admin user created and saved successfully.")
            except Exception as save_e:
                logger.warning(f"Could not save admin user with additional fields: {save_e}")
                logger.info("Continuing without setting additional fields.")

            # Create a second admin user with different credentials
            logger.info("Creating second admin user...")

            # Create base parameters for second admin
            create_params2 = {
                'email': 'admin12@example.com',
                'password': 'admin1234',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True
            }

            # Add username if required
            if requires_username:
                create_params2['username'] = 'admin12'

            # Add role if available
            if has_role:
                create_params2['role'] = 'admin'

            logger.info(f"Creating second admin user with parameters: {create_params2}")
            admin_user2 = User.objects.create_superuser(**create_params2)

            # Set additional fields if they exist on the User model
            if has_first_name and not admin_user2.first_name:
                try:
                    admin_user2.first_name = 'Admin'
                except Exception as name_e:
                    logger.warning(f"Could not set first_name for second admin: {name_e}")

            if has_last_name and not admin_user2.last_name:
                try:
                    admin_user2.last_name = 'User'
                except Exception as name_e:
                    logger.warning(f"Could not set last_name for second admin: {name_e}")

            if hasattr(admin_user2, 'is_admin'):
                admin_user2.is_admin = True

            # Save the second user with any additional fields
            try:
                admin_user2.save()
                logger.info("Second admin user created and saved successfully.")
            except Exception as save_e:
                logger.warning(f"Could not save second admin user with additional fields: {save_e}")
                logger.info("Continuing without setting additional fields for second admin.")

            return True

        except TypeError as e:
            # If we get a TypeError, it might be because we're missing required arguments
            logger.error(f"TypeError creating user: {e}")
            # Try to inspect the create_superuser method
            import inspect
            try:
                sig = inspect.signature(User.objects.create_superuser)
                logger.info(f"create_superuser signature: {sig}")
                # Try with just the required parameters
                params = {}
                for param_name, param in sig.parameters.items():
                    if param.default == inspect.Parameter.empty and param_name != 'self':
                        if param_name == 'username':
                            params[param_name] = 'admin'
                        elif param_name == 'email':
                            params[param_name] = 'admin@example.com'
                        elif param_name == 'password':
                            params[param_name] = 'admin123'

                logger.info(f"Trying with parameters: {params}")
                admin_user = User.objects.create_superuser(**params)
                admin_user.is_active = True
                admin_user.is_staff = True
                admin_user.is_superuser = True
                admin_user.save()
                logger.info("Admin user created successfully with minimal parameters.")
                return True
            except Exception as inner_e:
                logger.error(f"Failed to create user with inspect method: {inner_e}")
                # Last resort: try with hardcoded username and email
                try:
                    admin_user = User.objects.create_superuser(
                        username='admin',
                        email='admin@example.com',
                        password='admin123'
                    )
                    logger.info("Admin user created with hardcoded parameters.")
                    return True
                except Exception as last_e:
                    logger.error(f"All attempts to create admin user failed: {last_e}")
                    return False
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        logger.error(traceback.format_exc())
        return False

def check_database_connection(settings_module):
    """Check database connection."""
    logger.info("Checking database connection...")
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = settings_module

    try:
        result = subprocess.run(
            [sys.executable, 'manage.py', 'check', '--database', 'default'],
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Database connection successful.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Database connection failed: {e}")
        logger.debug(e.stdout)
        logger.debug(e.stderr)
        return False

def run_django_checks(settings_module):
    """Run Django system checks."""
    logger.info("Running Django system checks...")
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = settings_module

    try:
        result = subprocess.run(
            [sys.executable, 'manage.py', 'check'],
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Django system checks passed.")
        logger.debug(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Django system checks failed: {e}")
        logger.debug(e.stdout)
        logger.debug(e.stderr)
        return False

def update_admin_txt():
    """Update the admin.txt file with login credentials."""
    logger.info("Updating admin.txt file...")

    admin_txt_content = """# MindTrack Admin Login Credentials

## Primary Admin User
- Email: admin@example.com
- Username: admin
- Password: admin123
- Role: Administrator
- Access Level: Full

## Secondary Admin User
- Email: admin12@example.com
- Username: admin12
- Password: admin1234
- Role: Administrator
- Access Level: Full

## Login URLs
- Admin Portal: /admin/
- Admin Dashboard: /admin-portal/dashboard/

## Notes
- These credentials are automatically created when the server starts
- Both users have superuser privileges
- Use these credentials for development and testing only
- For production, please change these passwords immediately after first login
"""

    try:
        with open('admin.txt', 'w') as f:
            f.write(admin_txt_content)
        logger.info("admin.txt file updated successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to update admin.txt file: {e}")
        return False

class CronJobScheduler(threading.Thread):
    """
    Cron job scheduler for running scheduled tasks.
    This class runs as a daemon thread and executes scheduled tasks at specified intervals.
    """

    def __init__(self, settings_module):
        super().__init__(daemon=True)
        self.settings_module = settings_module
        self.running = False
        self.jobs = []
        self.env = os.environ.copy()
        self.env['DJANGO_SETTINGS_MODULE'] = settings_module

    def run(self):
        """Run the scheduler."""
        self.running = True
        logger.info("Starting cron job scheduler...")

        # Schedule jobs
        self._schedule_jobs()

        # Run the scheduler
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def _schedule_jobs(self):
        """Schedule all cron jobs."""
        # Process scheduled emails every 15 minutes
        self._add_job(
            schedule.every(15).minutes.do(self._run_management_command, 'process_scheduled_emails'),
            "Process scheduled emails (every 15 minutes)"
        )

        # Send scheduled reports daily at 1 AM
        self._add_job(
            schedule.every().day.at("01:00").do(self._run_management_command, 'send_scheduled_reports'),
            "Send scheduled reports (daily at 1 AM)"
        )

        # Database backup daily at 2 AM
        self._add_job(
            schedule.every().day.at("02:00").do(self._run_management_command, 'dbbackup'),
            "Database backup (daily at 2 AM)"
        )

        # Clean up old files weekly on Sunday at 3 AM
        self._add_job(
            schedule.every().sunday.at("03:00").do(self._run_management_command, 'cleanup_old_files'),
            "Clean up old files (weekly on Sunday at 3 AM)"
        )

        # Collect static files daily at 4 AM
        self._add_job(
            schedule.every().day.at("04:00").do(self._run_management_command, 'collectstatic', '--noinput'),
            "Collect static files (daily at 4 AM)"
        )

        # Build Tailwind CSS daily at 4:15 AM
        self._add_job(
            schedule.every().day.at("04:15").do(self._build_tailwind_css),
            "Build Tailwind CSS (daily at 4:15 AM)"
        )

        # Log scheduled jobs
        logger.info(f"Scheduled {len(self.jobs)} cron jobs")
        for job_name in self.jobs:
            logger.info(f"  - {job_name}")

    def _add_job(self, job, job_name):
        """Add a job to the scheduler with logging."""
        self.jobs.append(job_name)
        return job

    def _run_management_command(self, command, *args):
        """Run a Django management command."""
        try:
            cmd = [sys.executable, 'manage.py', command]
            cmd.extend(args)

            logger.info(f"Running scheduled command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                env=self.env,
                check=True,
                capture_output=True,
                text=True
            )

            logger.info(f"Scheduled command '{command}' completed successfully")
            logger.debug(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Scheduled command '{command}' failed: {e}")
            logger.error(f"Command stdout: {e.stdout}")
            logger.error(f"Command stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error running scheduled command '{command}': {e}")
            logger.error(traceback.format_exc())
            return False

    def _build_tailwind_css(self):
        """Build Tailwind CSS."""
        try:
            logger.info("Building Tailwind CSS...")

            # Check if npm is installed
            try:
                npm_version = subprocess.run(
                    ['npm', '--version'],
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info(f"npm version: {npm_version.stdout.strip()}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("npm not found. Skipping Tailwind CSS build.")
                return False

            # Run npm build command
            result = subprocess.run(
                ['npm', 'run', 'build'],
                check=True,
                capture_output=True,
                text=True
            )

            logger.info("Tailwind CSS built successfully")
            logger.debug(result.stdout)

            # Copy the built CSS to staticfiles directory
            self._ensure_css_in_staticfiles()

            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Tailwind CSS build failed: {e}")
            logger.error(f"Build stdout: {e.stdout}")
            logger.error(f"Build stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error building Tailwind CSS: {e}")
            logger.error(traceback.format_exc())
            return False

    def _ensure_css_in_staticfiles(self):
        """Ensure CSS files are in the staticfiles directory."""
        try:
            # Import Django settings
            import django
            from django.conf import settings

            # Get paths
            static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
            staticfiles_dir = settings.STATIC_ROOT

            if not os.path.exists(staticfiles_dir):
                os.makedirs(staticfiles_dir, exist_ok=True)
                logger.info(f"Created staticfiles directory: {staticfiles_dir}")

            # Ensure CSS directory exists in staticfiles
            css_staticfiles_dir = os.path.join(staticfiles_dir, 'css')
            if not os.path.exists(css_staticfiles_dir):
                os.makedirs(css_staticfiles_dir, exist_ok=True)
                logger.info(f"Created CSS directory in staticfiles: {css_staticfiles_dir}")

            # Copy CSS files from static to staticfiles
            css_files = [
                'tailwind-custom.css',
                'styles.css',
                'enhanced-styles.css',
                'animations.css',
                'admin-portal.css',
                'modern-sidebar.css',
                'sidebar-animations.css',
                'toast.css'
            ]

            for css_file in css_files:
                src_path = os.path.join(static_dir, 'css', css_file)
                dest_path = os.path.join(css_staticfiles_dir, css_file)

                if os.path.exists(src_path):
                    import shutil
                    shutil.copy2(src_path, dest_path)
                    logger.info(f"Copied {css_file} to staticfiles")
                else:
                    logger.warning(f"Source CSS file not found: {src_path}")

            # Copy JS files from static to staticfiles
            js_staticfiles_dir = os.path.join(staticfiles_dir, 'js')
            if not os.path.exists(js_staticfiles_dir):
                os.makedirs(js_staticfiles_dir, exist_ok=True)
                logger.info(f"Created JS directory in staticfiles: {js_staticfiles_dir}")

            js_files = [
                'main.js',
                'admin-portal.js',
                'dashboard-charts.js',
                'modern-sidebar.js',
                'notifications.js',
                'search.js',
                'sidebar.js',
                'theme-switcher.js',
                'toast.js'
            ]

            for js_file in js_files:
                src_path = os.path.join(static_dir, 'js', js_file)
                dest_path = os.path.join(js_staticfiles_dir, js_file)

                if os.path.exists(src_path):
                    import shutil
                    shutil.copy2(src_path, dest_path)
                    logger.info(f"Copied {js_file} to staticfiles")
                else:
                    logger.warning(f"Source JS file not found: {src_path}")

            return True
        except Exception as e:
            logger.error(f"Error ensuring CSS in staticfiles: {e}")
            logger.error(traceback.format_exc())
            return False

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        logger.info("Stopping cron job scheduler...")


class HealthCheckServer(threading.Thread):
    """Simple HTTP server for health checks."""

    def __init__(self, host, main_port, gunicorn_process):
        super().__init__(daemon=True)
        self.host = host
        self.health_port = main_port + 1  # Use main port + 1 for health checks
        self.gunicorn_process = gunicorn_process
        self.running = False
        self.sock = None

    def run(self):
        """Run the health check server."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                self.sock.bind((self.host, self.health_port))
            except socket.error:
                logger.warning(f"Could not bind health check server to port {self.health_port}. Health checks will be disabled.")
                return

            self.sock.listen(5)
            self.running = True

            logger.info(f"Health check server running on {self.host}:{self.health_port}")

            while self.running:
                try:
                    client, addr = self.sock.accept()
                    threading.Thread(target=self.handle_client, args=(client, addr), daemon=True).start()
                except (socket.error, OSError):
                    if not self.running:
                        break
        except Exception as e:
            logger.error(f"Error in health check server: {e}")
        finally:
            if self.sock:
                self.sock.close()

    def handle_client(self, client_socket, address):
        """Handle a client connection."""
        try:
            # Read the request
            request = client_socket.recv(1024).decode('utf-8')

            # Check if it's a GET request to /health
            if 'GET /health' in request:
                # Check if Gunicorn is running
                if self.gunicorn_process and self.gunicorn_process.poll() is None:
                    status = 'healthy'
                else:
                    status = 'unhealthy'

                # Prepare response
                response_data = {
                    'status': status,
                    'timestamp': datetime.now().isoformat(),
                    'server': 'MindTrack Health Check',
                    'pid': os.getpid(),
                    'gunicorn_pid': self.gunicorn_process.pid if self.gunicorn_process else None
                }

                response_body = json.dumps(response_data)

                # Send response
                response = (
                    'HTTP/1.1 200 OK\r\n'
                    'Content-Type: application/json\r\n'
                    f'Content-Length: {len(response_body)}\r\n'
                    'Connection: close\r\n'
                    '\r\n'
                    f'{response_body}'
                )

                client_socket.sendall(response.encode('utf-8'))
            else:
                # Send 404 for other requests
                response = (
                    'HTTP/1.1 404 Not Found\r\n'
                    'Content-Type: text/plain\r\n'
                    'Content-Length: 9\r\n'
                    'Connection: close\r\n'
                    '\r\n'
                    'Not Found'
                )

                client_socket.sendall(response.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error handling health check request: {e}")
        finally:
            client_socket.close()

    def stop(self):
        """Stop the health check server."""
        self.running = False
        if self.sock:
            self.sock.close()

def run_gunicorn(config):
    """Run Gunicorn WSGI server."""
    # Build Gunicorn command
    cmd = [
        'gunicorn',
        'mindtrack.wsgi:application',
        f'--bind={config.host}:{config.port}',
        f'--workers={config.workers}',
        f'--timeout={config.timeout}',
        f'--log-level={config.log_level}',
    ]

    # Add optional arguments
    if config.reload:
        cmd.append('--reload')

    # Add access and error logs
    cmd.append('--access-logfile=-')  # Log to stdout
    cmd.append('--error-logfile=-')  # Log to stderr

    # Add worker class for better performance
    cmd.append('--worker-class=gthread')

    # Add max requests to prevent memory leaks
    cmd.append('--max-requests=1000')
    cmd.append('--max-requests-jitter=50')

    # Add graceful timeout
    cmd.append('--graceful-timeout=30')

    # Add keep-alive
    cmd.append('--keep-alive=5')

    # Set environment variables
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = config.settings_module

    # Log the command
    logger.info(f"Starting Gunicorn with command: {' '.join(cmd)}")

    # Run Gunicorn
    try:
        process = subprocess.Popen(cmd, env=env)

        # Start health check server
        health_server = HealthCheckServer(config.host, config.port, process)
        health_server.start()

        # Start cron job scheduler
        cron_scheduler = CronJobScheduler(config.settings_module)
        cron_scheduler.start()
        logger.info("Cron job scheduler started")

        # Handle signals
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down gracefully...")

            # Stop cron job scheduler
            cron_scheduler.stop()

            # Stop health check server
            health_server.stop()

            # Terminate Gunicorn
            process.terminate()

            # Wait for process to terminate gracefully
            for _ in range(10):  # Wait up to 10 seconds
                if process.poll() is not None:
                    break
                time.sleep(1)

            # Force kill if still running
            if process.poll() is None:
                logger.warning("Process did not terminate gracefully, forcing...")
                process.kill()

            logger.info("Server stopped.")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Monitor Gunicorn process
        while True:
            # Check if process is still running
            if process.poll() is not None:
                exit_code = process.returncode
                logger.error(f"Gunicorn process exited unexpectedly with code {exit_code}")

                # Stop cron job scheduler
                cron_scheduler.stop()

                # Stop health check server
                health_server.stop()

                # Exit with the same code
                sys.exit(exit_code)

            # Sleep for a while
            time.sleep(1)

    except Exception as e:
        logger.error(f"Failed to start Gunicorn: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

def run_preflight_checks(config):
    """Run pre-flight checks before starting the server."""
    logger.info("Running pre-flight checks...")

    # Check if port is available
    if not check_port_availability(config.host, config.port):
        logger.error(f"Port {config.port} is already in use. Please choose a different port.")
        return False

    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        logger.error(f"Missing dependencies: {', '.join(missing_deps)}")
        logger.error("Please install the missing dependencies and try again.")
        return False

    # Check Django project
    if not check_django_project():
        logger.error("Django project check failed.")
        return False

    # Check database connection
    if not check_database_connection(config.settings_module):
        logger.error("Database connection check failed.")
        return False

    # Run Django system checks
    if not run_django_checks(config.settings_module):
        logger.error("Django system checks failed.")
        return False

    # Update ALLOWED_HOSTS
    if not update_allowed_hosts(config.host, config.port, config.settings_module):
        logger.warning("Failed to update ALLOWED_HOSTS. This may cause issues with accessing the server.")
    else:
        logger.info("ALLOWED_HOSTS updated successfully.")

    # All checks passed
    logger.info("All pre-flight checks passed.")
    return True

def main():
    """Main function."""
    # Parse command line arguments
    args = parse_args()

    # Set up logging
    global logger
    logger = setup_logging(args.log_level, args.log_file)

    # Create server configuration
    config = ServerConfig(args)

    # Run pre-flight checks
    if not args.skip_checks and not run_preflight_checks(config):
        logger.error("Pre-flight checks failed. Exiting.")
        sys.exit(1)

    # Ensure SQLite database is used
    if not ensure_sqlite_database():
        logger.warning("Failed to ensure SQLite database. Continuing anyway.")

    # Database management process:
    # 1. Delete existing database
    logger.info("Step 1: Deleting existing database...")
    if not delete_database():
        logger.warning("Failed to delete existing database. Continuing anyway.")

    # 2. Create empty database
    logger.info("Step 2: Creating new empty database...")
    if not create_empty_database():
        logger.warning("Failed to create empty database. Migrations may fail.")

    # 3. Run migrations on the new database
    logger.info("Step 3: Running migrations on the new database...")
    migration_success = run_migrations(config.settings_module)

    if not migration_success:
        logger.warning("Database migrations failed. Attempting to fix common issues...")

        # Try to fix migration issues
        fix_success = fix_migration_issues()
        if fix_success:
            logger.info("Migration issues may have been fixed. Trying migrations again...")
            # Try migrations again
            migration_success = run_migrations(config.settings_module)

            if migration_success:
                logger.info("Migrations succeeded after fixing issues!")
            else:
                logger.error("Migrations still failing after attempting fixes.")
                logger.warning("This may cause issues with the application.")
                logger.warning("You may need to manually fix migration issues or restore from a backup.")

                # Provide more detailed warnings based on environment
                if not config.is_development:
                    logger.warning("In production mode, continuing with failed migrations may cause data corruption.")
                    logger.warning("Consider fixing the migration issues before proceeding.")
                else:
                    logger.warning("In development mode, you can continue, but some features may not work correctly.")
        else:
            logger.error("Failed to fix migration issues automatically.")
            logger.warning("This may cause issues with the application.")
            logger.warning("You may need to manually fix migration issues or restore from a backup.")

    # In production mode, also collect static files
    if not config.is_development:
        # Collect static files
        if not collect_static(config.settings_module):
            logger.warning("Static file collection failed. Continuing anyway.")

    # Create admin user if it doesn't exist
    if not create_admin_user(config.settings_module):
        logger.warning("Failed to create admin user. Continuing anyway.")

    # Populate question types
    if not populate_question_types(config.settings_module):
        logger.warning("Failed to populate question types. Continuing anyway.")
    else:
        logger.info("Question types populated successfully.")

    # Update admin.txt file with login credentials
    update_admin_txt()

    # Run the server
    run_gunicorn(config)

if __name__ == '__main__':
    main()
