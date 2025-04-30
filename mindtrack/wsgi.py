"""
WSGI config for mindtrack project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

# Check if we're running on Vercel
if 'VERCEL' in os.environ or '/var/task' in os.getcwd():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.vercel_settings')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# Vercel deployment handler
app = application
