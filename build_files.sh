#!/bin/bash

# Build script for Vercel deployment

# Make script executable
chmod +x build_files.sh

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations with Vercel settings
DJANGO_SETTINGS_MODULE=mindtrack.vercel_settings python manage.py migrate

# Create superuser
python create_vercel_superuser.py

echo "Build completed successfully!"
