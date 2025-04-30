#!/usr/bin/env python
"""
MindTrack Production Server Script for HostPinnacle Deployment

This script provides a convenient way to run the MindTrack application
in a production environment using Gunicorn as the WSGI server.
It is specifically configured for deployment on HostPinnacle servers.

Usage:
    python server.py [options]

Options:
    --host HOST         Host to bind to (default: 0.0.0.0)
    --port PORT         Port to bind to (default: 8000)
    --workers WORKERS   Number of worker processes (default: based on CPU count)
    --timeout TIMEOUT   Worker timeout in seconds (default: 120)
    --reload            Enable auto-reload on code changes (development only)
    --log-level LEVEL   Log level (default: info)
    --access-log FILE   Access log file (default: None)
    --error-log FILE    Error log file (default: None)
    --settings MODULE   Django settings module (default: mindtrack.settings)
    --help              Show this help message and exit
"""

import os
import sys
import argparse
import multiprocessing
import subprocess
import signal
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='MindTrack Production Server for HostPinnacle')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to (default: 8000)')
    parser.add_argument('--workers', type=int, default=None,
                        help='Number of worker processes (default: CPU count * 2 + 1)')
    parser.add_argument('--timeout', type=int, default=120,
                        help='Worker timeout in seconds (default: 120)')
    parser.add_argument('--reload', action='store_true',
                        help='Enable auto-reload on code changes (development only)')
    parser.add_argument('--log-level', default='info',
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='Log level (default: info)')
    parser.add_argument('--access-log', default=None,
                        help='Access log file (default: None)')
    parser.add_argument('--error-log', default=None,
                        help='Error log file (default: None)')
    parser.add_argument('--settings', default='mindtrack.settings',
                        help='Django settings module (default: mindtrack.settings)')

    return parser.parse_args()

def collect_static(settings_module):
    """Collect static files."""
    logger.info("Collecting static files...")
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = settings_module

    try:
        subprocess.run(
            [sys.executable, 'manage.py', 'collectstatic', '--noinput'],
            env=env,
            check=True
        )
        logger.info("Static files collected successfully.")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to collect static files: {e}")
        logger.warning("Continuing anyway, but static files may not be served correctly.")

def run_migrations(settings_module):
    """Run database migrations."""
    logger.info("Running database migrations...")
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = settings_module

    try:
        subprocess.run(
            [sys.executable, 'manage.py', 'migrate', '--noinput'],
            env=env,
            check=True
        )
        logger.info("Database migrations completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run migrations: {e}")
        logger.error("The application may not function correctly without migrations.")
        # Continue anyway, as this might be a deployment where migrations are handled separately

def run_gunicorn(args):
    """Run Gunicorn WSGI server."""
    # Set default number of workers if not specified
    workers = args.workers
    if workers is None:
        workers = (multiprocessing.cpu_count() * 2) + 1

    # Build Gunicorn command
    cmd = [
        'gunicorn',
        'mindtrack.wsgi:application',
        f'--bind={args.host}:{args.port}',
        f'--workers={workers}',
        f'--timeout={args.timeout}',
        f'--log-level={args.log_level}',
    ]

    # Add optional arguments
    if args.reload:
        cmd.append('--reload')

    if args.access_log:
        cmd.extend(['--access-logfile', args.access_log])
    else:
        cmd.append('--access-logfile=-')  # Log to stdout

    if args.error_log:
        cmd.extend(['--error-logfile', args.error_log])
    else:
        cmd.append('--error-logfile=-')  # Log to stderr

    # Add worker class for better performance
    cmd.extend(['--worker-class=gthread'])

    # Add max requests to prevent memory leaks
    cmd.extend(['--max-requests=1000', '--max-requests-jitter=50'])

    # Set environment variables
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = args.settings

    # Log the command
    logger.info(f"Starting Gunicorn with command: {' '.join(cmd)}")
    logger.info(f"Using settings module: {args.settings}")
    logger.info(f"Workers: {workers}")

    # Run Gunicorn
    try:
        process = subprocess.Popen(cmd, env=env)

        # Handle signals
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down gracefully...")
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

        # Wait for process to complete
        process.wait()

    except Exception as e:
        logger.error(f"Failed to start Gunicorn: {e}")
        sys.exit(1)

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import gunicorn
        logger.info("Gunicorn is installed.")
    except ImportError:
        logger.error("Gunicorn is not installed. Please install it with: pip install gunicorn")
        sys.exit(1)

    try:
        import django
        logger.info(f"Django {django.__version__} is installed.")
    except ImportError:
        logger.error("Django is not installed. Please install it with: pip install django")
        sys.exit(1)

def main():
    """Main function."""
    args = parse_args()

    # Set log level
    logger.setLevel(getattr(logging, args.log_level.upper()))

    # Check dependencies
    check_dependencies()

    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', args.settings)

    # Prepare the application (only in production)
    if not args.reload:
        collect_static(args.settings)
        run_migrations(args.settings)

    # Run the server
    run_gunicorn(args)

if __name__ == '__main__':
    main()
