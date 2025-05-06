from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import json
import traceback
import datetime
import os

def home(request):
    """
    Home page view
    Always shows the landing page regardless of authentication status
    Uses a custom landing page template with a simplified navbar
    """
    return render(request, 'core/landing_page.html')

def about(request):
    """
    About page view
    """
    return render(request, 'core/about.html')

def contact(request):
    """
    Contact page view
    """
    if request.method == 'POST':
        # Process the form data (in a real app, you'd save this to the database or send an email)
        # Commented out to avoid unused variable warnings
        # name = request.POST.get('name')
        # email = request.POST.get('email')
        # subject = request.POST.get('subject')
        # message = request.POST.get('message')

        # In a real app, you would validate the data and save it to the database or send an email

        # Check if this is an HTMX request
        if request.headers.get('HX-Request'):
            # Return just the success message for HTMX
            return render(request, 'core/partials/contact_success.html')
        else:
            # Add a success message for traditional form submission
            messages.success(request, 'Your message has been sent. We will get back to you soon!')

    return render(request, 'core/contact.html')

@login_required
def dashboard(request):
    """
    Dashboard view (requires login)
    Redirects to the new dashboard app based on user role
    """
    # Use direct URL to avoid namespace issues
    if hasattr(request.user, 'is_admin_user') and request.user.is_admin_user():
        return redirect('/admin-portal/dashboard/')
    else:
        # For regular users or if is_admin_user doesn't exist
        return redirect('/client-portal/dashboard/')

@csrf_exempt
def test_database(request):
    """
    Test database connection and operations
    """
    response_data = {
        'status': 'success',
        'message': 'Database test completed',
        'tests': []
    }

    try:
        # Test 1: Basic connection
        test1 = {'name': 'Basic Connection', 'status': 'success', 'details': ''}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                test1['details'] = f"Connection successful, result: {result}"
        except Exception as e:
            test1['status'] = 'error'
            test1['details'] = f"Error: {str(e)}"
        response_data['tests'].append(test1)

        # Test 2: Create a test table
        test2 = {'name': 'Create Test Table', 'status': 'success', 'details': ''}
        try:
            with connection.cursor() as cursor:
                cursor.execute("CREATE TABLE IF NOT EXISTS db_test (id serial PRIMARY KEY, test_value varchar(100), created_at timestamp DEFAULT NOW())")
                test2['details'] = "Table created or already exists"
        except Exception as e:
            test2['status'] = 'error'
            test2['details'] = f"Error: {str(e)}"
        response_data['tests'].append(test2)

        # Test 3: Insert data
        test3 = {'name': 'Insert Data', 'status': 'success', 'details': ''}
        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO db_test (test_value) VALUES (%s) RETURNING id", ["Test value " + request.method])
                result = cursor.fetchone()
                test3['details'] = f"Data inserted, ID: {result[0]}"
        except Exception as e:
            test3['status'] = 'error'
            test3['details'] = f"Error: {str(e)}"
        response_data['tests'].append(test3)

        # Test 4: Query data
        test4 = {'name': 'Query Data', 'status': 'success', 'details': ''}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, test_value, created_at FROM db_test ORDER BY created_at DESC LIMIT 5")
                results = cursor.fetchall()
                test4['details'] = f"Retrieved {len(results)} rows: {results}"
        except Exception as e:
            test4['status'] = 'error'
            test4['details'] = f"Error: {str(e)}"
        response_data['tests'].append(test4)

    except Exception as e:
        response_data['status'] = 'error'
        response_data['message'] = f"Overall test failed: {str(e)}"
        response_data['traceback'] = traceback.format_exc()

    return JsonResponse(response_data)

def health_check(request):
    """
    Health check endpoint for Render.com
    Returns a 200 OK response with basic system information
    """
    data = {
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'service': 'MindTrack',
        'environment': os.environ.get('DJANGO_SETTINGS_MODULE', 'unknown'),
        'python_version': os.environ.get('PYTHON_VERSION', 'unknown'),
    }

    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            data['database'] = 'connected'
    except Exception as e:
        data['database'] = f'error: {str(e)}'

    return JsonResponse(data)

def test_login(request):
    """
    Test login page with toast notifications
    """
    return render(request, 'test_login.html')

def show_toast(request, toast_type='info'):
    """
    Show a toast notification and redirect back
    """
    if toast_type == 'success':
        messages.success(request, 'This is a success message')
    elif toast_type == 'error':
        messages.error(request, 'This is an error message')
    elif toast_type == 'warning':
        messages.warning(request, 'This is a warning message')
    else:
        messages.info(request, 'This is an info message')

    # Redirect back to the previous page or home
    return redirect(request.META.get('HTTP_REFERER', '/'))
