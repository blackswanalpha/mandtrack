import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Import the URL resolver
from django.urls import reverse, NoReverseMatch

# Try to reverse a URL with the users namespace
try:
    url = reverse('users:user_list')
    print(f"Success! The 'users:user_list' URL resolves to: {url}")
except NoReverseMatch as e:
    print(f"Error: {e}")

# Try to reverse a URL without namespace (from accounts app)
try:
    url = reverse('admin_profile')
    print(f"Success! The 'admin_profile' URL resolves to: {url}")
except NoReverseMatch as e:
    print(f"Error: {e}")
