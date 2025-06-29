"""
Django settings for mindtrack project on barberianspa.com.

This file contains barberianspa.com-specific settings and overrides the base settings.
"""

from .settings import *
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_DIR, 'barberianspa.log'))
    ]
)
logger = logging.getLogger(__name__)

# Debug should be False in production
DEBUG = False

# Update allowed hosts for barberianspa.com
ALLOWED_HOSTS = [
    'mindtrack.barberianspa.com', '.barberianspa.com',
    '.hostpinnacle.com', 'localhost', '127.0.0.1', '0.0.0.0',
    'localhost:8000', 'localhost:8001', 'localhost:8009',
    '127.0.0.1:8000', '127.0.0.1:8001', '127.0.0.1:8009',
    '0.0.0.0:8000', '0.0.0.0:8001', '0.0.0.0:8009',
    'mandtrack.onrender.com', '.onrender.com'
]

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Database configuration for barberianspa.com
# Use PostgreSQL database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mindtrack_db',
        'USER': 'mindtrack_db_owner',
        'PASSWORD': 'npg_AUV4r3qElnDN',
        'HOST': 'ep-steep-base-a2xkorr1-pooler.eu-central-1.aws.neon.tech',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@mindtrack.barberianspa.com')

# Site URL for generating absolute URLs
SITE_URL = 'https://mindtrack.barberianspa.com'

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400 * 7  # 7 days

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'barberianspa.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'mindtrack': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'error_middleware': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Print configuration information
logger.info("barberianspa.com settings loaded")
logger.info(f"DEBUG: {DEBUG}")
logger.info(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
logger.info(f"DATABASE: {DATABASES['default']['ENGINE']} on {DATABASES['default']['HOST']}")
logger.info(f"STATIC_ROOT: {STATIC_ROOT}")
logger.info(f"MEDIA_ROOT: {MEDIA_ROOT}")
logger.info(f"SITE_URL: {SITE_URL}")
