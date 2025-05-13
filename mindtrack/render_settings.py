"""
Django settings for mindtrack project on Render.com.

This file contains Render.com-specific settings and overrides the base settings.
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
        logging.FileHandler(os.path.join(BASE_DIR, 'render.log'))
    ]
)

logger = logging.getLogger(__name__)

# Debug should be False in production
DEBUG = False

# Update allowed hosts for Render.com
ALLOWED_HOSTS = [
    'mandtrack.onrender.com', '.onrender.com',
    '.barberianspa.com', '.hostpinnacle.com',
    'localhost', '127.0.0.1', '0.0.0.0',
    'localhost:8000', 'localhost:8001', 'localhost:8009',
    '127.0.0.1:8000', '127.0.0.1:8001', '127.0.0.1:8009',
    '0.0.0.0:8000', '0.0.0.0:8001', '0.0.0.0:8009',
    'mindtrack.barberianspa.com'
]

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise configuration for static files in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000  # 1 year in seconds
WHITENOISE_MIMETYPES = {
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.html': 'text/html',
    '.txt': 'text/plain',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.eot': 'application/vnd.ms-fontobject',
}

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Database configuration for Render.com
# Use dj_database_url to parse the DATABASE_URL environment variable
import dj_database_url

# Default to the Neon PostgreSQL database
DATABASE_URL = os.environ.get('DATABASE_URL',
    "postgresql://mindtrack_db_owner:npg_AUV4r3qElnDN@ep-steep-base-a2xkorr1-pooler.eu-central-1.aws.neon.tech/mindtrack_db?sslmode=require")

# Configure the database
DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=True
    )
}

# Security settings
SECURE_SSL_REDIRECT = False  # Render.com handles SSL termination
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Render.com specific settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Required for Render.com SSL

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@mindtrack.com')

# Site URL for generating absolute URLs
SITE_URL = 'https://mandtrack.onrender.com'

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

# Authentication settings
LOGIN_URL = '/admin-portal/login/'
LOGIN_REDIRECT_URL = '/dashboard/admin/'
LOGOUT_REDIRECT_URL = '/'

# Print configuration information
logger.info("Render.com settings loaded")
logger.info(f"DEBUG: {DEBUG}")
logger.info(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
logger.info(f"DATABASE: {DATABASES['default']['ENGINE']} on {DATABASES['default']['HOST']}")
logger.info(f"STATIC_ROOT: {STATIC_ROOT}")
logger.info(f"MEDIA_ROOT: {MEDIA_ROOT}")
