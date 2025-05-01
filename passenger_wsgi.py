#!/usr/bin/env python
"""
Passenger WSGI configuration for MindTrack on HostPinnacle.

This file is required for deploying Django applications on HostPinnacle
using Phusion Passenger.

For more information, see:
https://www.phusionpassenger.com/library/walkthroughs/deploy/python/
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'passenger_wsgi.log'))
    ]
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("Initializing Passenger WSGI application for MindTrack")

# Add the project directory to the Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
logger.info(f"Current directory: {CURRENT_DIR}")

# Add the virtualenv site-packages to the path if it exists
VENV_PATH = os.path.join(CURRENT_DIR, 'venv', 'lib', 'python3.10', 'site-packages')
if os.path.exists(VENV_PATH):
    logger.info(f"Adding virtualenv site-packages to path: {VENV_PATH}")
    sys.path.insert(0, VENV_PATH)
else:
    logger.warning(f"Virtualenv site-packages not found at: {VENV_PATH}")

# Add the current directory to the path
sys.path.insert(0, CURRENT_DIR)

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')

# Check if we're in a production environment
if 'PASSENGER_APP_ENV' in os.environ:
    logger.info(f"Running in Passenger environment: {os.environ['PASSENGER_APP_ENV']}")
    # Set production-specific settings
    os.environ['DEBUG'] = 'False'
    os.environ['ALLOWED_HOSTS'] = '.hostpinnacle.com,.barberianspa.com,mindtrack.barberianspa.com,localhost,127.0.0.1'

try:
    # Import Django and get the WSGI application
    from django.core.wsgi import get_wsgi_application

    # This is the WSGI application object that Passenger will use
    application = get_wsgi_application()

    # Log successful initialization
    logger.info("Django WSGI application initialized successfully")

except Exception as e:
    logger.error(f"Error initializing Django WSGI application: {e}")
    import traceback
    logger.error(traceback.format_exc())

    # Provide a fallback application that returns an error message
    def application(environ, start_response):
        status = '500 Internal Server Error'
        output = b'Error initializing Django application. Please check the logs.'
        response_headers = [('Content-type', 'text/plain'),
                           ('Content-Length', str(len(output)))]
        start_response(status, response_headers)
        return [output]
