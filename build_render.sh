#!/bin/bash

# Build script for Render.com deployment

# Make script executable
chmod +x build_render.sh

# Install dependencies
pip install -r requirements.txt

# Check if npm is installed
if command -v npm &> /dev/null; then
    echo "npm is installed, building Tailwind CSS..."

    # Install npm dependencies
    npm install

    # Build Tailwind CSS
    npm run build

    echo "Tailwind CSS built successfully!"
else
    echo "npm is not installed, skipping Tailwind CSS build."

    # Create fallback CSS directory if it doesn't exist
    mkdir -p static/css

    # Check if tailwind-custom.css exists
    if [ ! -f static/css/tailwind-custom.css ]; then
        echo "Creating empty tailwind-custom.css file..."
        echo "/* Auto-generated empty file */" > static/css/tailwind-custom.css
    fi
fi

# Collect static files
python manage.py collectstatic --noinput --settings=mindtrack.render_settings

# Ensure CSS files are in staticfiles
mkdir -p staticfiles/css
mkdir -p staticfiles/js

# Copy CSS files if they exist in static directory
for css_file in tailwind-custom.css styles.css enhanced-styles.css animations.css admin-portal.css modern-sidebar.css sidebar-animations.css toast.css; do
    if [ -f static/css/$css_file ]; then
        cp static/css/$css_file staticfiles/css/
        echo "Copied $css_file to staticfiles/css/"
    fi
done

# Copy JS files if they exist in static directory
for js_file in main.js admin-portal.js dashboard-charts.js modern-sidebar.js notifications.js search.js sidebar.js theme-switcher.js toast.js; do
    if [ -f static/js/$js_file ]; then
        cp static/js/$js_file staticfiles/js/
        echo "Copied $js_file to staticfiles/js/"
    fi
done

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
