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
from pathlib import Path
from datetime import datetime

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

def run_migrations(settings_module):
    """Run database migrations."""
    logger.info("Running database migrations...")
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = settings_module

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
        logger.debug(e.stdout)
        logger.debug(e.stderr)
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

        # Check if User model requires username
        requires_username = 'username' in [field.name for field in User._meta.fields]
        logger.info(f"User model requires username: {requires_username}")

        # Create admin user
        logger.info("Creating admin user...")
        try:
            # Try to create user with username if required
            if requires_username:
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',
                    is_active=True,
                    is_staff=True,
                    is_superuser=True
                )
            else:
                admin_user = User.objects.create_superuser(
                    email='admin@example.com',
                    password='admin123',
                    is_active=True,
                    is_staff=True,
                    is_superuser=True
                )

            # Set additional fields if they exist on the User model
            if hasattr(admin_user, 'first_name'):
                admin_user.first_name = 'Admin'
            if hasattr(admin_user, 'last_name'):
                admin_user.last_name = 'User'
            if hasattr(admin_user, 'is_admin'):
                admin_user.is_admin = True

            admin_user.save()
            logger.info("Admin user created successfully.")

            # Create a second admin user with different credentials
            logger.info("Creating second admin user...")
            if requires_username:
                admin_user2 = User.objects.create_superuser(
                    username='admin12',
                    email='admin12@example.com',
                    password='admin1234',
                    is_active=True,
                    is_staff=True,
                    is_superuser=True
                )
            else:
                admin_user2 = User.objects.create_superuser(
                    email='admin12@example.com',
                    password='admin1234',
                    is_active=True,
                    is_staff=True,
                    is_superuser=True
                )

            # Set additional fields if they exist on the User model
            if hasattr(admin_user2, 'first_name'):
                admin_user2.first_name = 'Admin'
            if hasattr(admin_user2, 'last_name'):
                admin_user2.last_name = 'User'
            if hasattr(admin_user2, 'is_admin'):
                admin_user2.is_admin = True

            admin_user2.save()
            logger.info("Second admin user created successfully.")
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
                except Exception as last_e:
                    logger.error(f"All attempts to create admin user failed: {last_e}")

        return True
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

        # Handle signals
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down gracefully...")

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
    if not run_migrations(config.settings_module):
        logger.warning("Database migrations failed. Continuing anyway.")

    # In production mode, also collect static files
    if not config.is_development:
        # Collect static files
        if not collect_static(config.settings_module):
            logger.warning("Static file collection failed. Continuing anyway.")

    # Create admin user if it doesn't exist
    if not create_admin_user(config.settings_module):
        logger.warning("Failed to create admin user. Continuing anyway.")

    # Update admin.txt file with login credentials
    update_admin_txt()

    # Run the server
    run_gunicorn(config)

if __name__ == '__main__':
    main()
