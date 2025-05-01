"""
Test script for error handling.

This script contains a view that deliberately raises an exception
to test the error handling middleware.
"""

from django.http import HttpResponse
from django.urls import path

def test_error(request):
    """
    Test view that deliberately raises an exception.
    
    Access this view at /test-error/ to see the error handling in action.
    """
    # Deliberately raise an exception
    raise Exception("This is a test exception to verify error handling.")

def test_404(request):
    """
    Test view that deliberately raises a 404 error.
    
    Access this view at /test-404/ to see the 404 error handling in action.
    """
    from django.http import Http404
    raise Http404("This is a test 404 error.")

def test_403(request):
    """
    Test view that deliberately raises a 403 error.
    
    Access this view at /test-403/ to see the 403 error handling in action.
    """
    from django.core.exceptions import PermissionDenied
    raise PermissionDenied("This is a test 403 error.")

def test_json_error(request):
    """
    Test view that deliberately raises an exception for JSON requests.
    
    Access this view at /test-json-error/ with Accept: application/json header
    to see the JSON error handling in action.
    """
    # Deliberately raise an exception
    raise Exception("This is a test exception for JSON requests.")

# URL patterns for testing error handling
urlpatterns = [
    path('test-error/', test_error, name='test_error'),
    path('test-404/', test_404, name='test_404'),
    path('test-403/', test_403, name='test_403'),
    path('test-json-error/', test_json_error, name='test_json_error'),
]
