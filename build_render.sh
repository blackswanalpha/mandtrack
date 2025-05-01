#!/bin/bash

# Build script for Render.com deployment

# Make script executable
chmod +x build_render.sh

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput --settings=mindtrack.render_settings

# Run migrations
python manage.py migrate --settings=mindtrack.render_settings

# Create superuser (will be skipped if user already exists)
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.render_settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@example.com').exists():
    User.objects.create_superuser('admin@example.com', 'admin123')
    print('Superuser created successfully!')
else:
    print('Superuser already exists.')
"

echo "Build completed successfully!"
