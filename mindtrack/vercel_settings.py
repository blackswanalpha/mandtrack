"""
Django settings for mindtrack project on Vercel.

This file contains Vercel-specific settings and overrides the base settings.
"""

from .settings import *

# Debug should be False in production
DEBUG = False

# Enable Vercel debug middleware
VERCEL_DEBUG = True

# Update allowed hosts
ALLOWED_HOSTS = ['.vercel.app', 'localhost', '127.0.0.1']

# Add Vercel debug middleware
MIDDLEWARE = [
    'core.middleware.VercelDebugMiddleware',  # Add this first to catch all exceptions
] + MIDDLEWARE

# Configure the database for Vercel
import dj_database_url

# Use Neon PostgreSQL database
DATABASE_URL = "postgresql://mindtrack_db_owner:npg_AUV4r3qElnDN@ep-steep-base-a2xkorr1-pooler.eu-central-1.aws.neon.tech/mindtrack_db?sslmode=require"

# Print the database URL for debugging (will be visible in Vercel logs)
print(f"Using database URL: {DATABASE_URL}")
# URL path for static assets
STATIC_URL = '/static/'

# Where collectstatic will put files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Configure the database
DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=True
    )
}

# Simplified logging configuration for Vercel
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# Authentication settings
LOGIN_URL = '/admin-portal/login/'
LOGIN_REDIRECT_URL = '/dashboard/admin/'
LOGOUT_REDIRECT_URL = '/'

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400 * 7  # 7 days
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Security settings for production
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = False  # Vercel handles SSL

# HSTS settings
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
