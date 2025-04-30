"""
WSGI config for mindtrack project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

# Check if we're running on Vercel
is_vercel = 'VERCEL' in os.environ or '/var/task' in os.getcwd()

if is_vercel:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.vercel_settings')

    # Run build script on Vercel during cold start
    try:
        import vercel_build
        vercel_build.main()
    except Exception as e:
        print(f"Error running build script: {str(e)}")
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# Test database connection on Vercel
if is_vercel:
    try:
        from django.db import connection

        # Test the connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"WSGI Database connection test result: {result}")

        print("WSGI Database connection test successful!")
    except Exception as e:
        print(f"WSGI Error testing database connection: {str(e)}")
        import traceback
        print(traceback.format_exc())

# Vercel deployment handler
app = application
