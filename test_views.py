"""
Script to test if the views work with the new models.
"""
import os
import django
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

from users.models import User
from dashboard.views import user_dashboard, admin_dashboard

def test_dashboard_views():
    """Test the dashboard views with the new models."""
    # Create a request factory
    factory = RequestFactory()
    
    # Try to get an existing user
    try:
        user = User.objects.filter(is_staff=True).first()
        if not user:
            print("No staff user found. Using first available user.")
            user = User.objects.first()
            
        if not user:
            print("No users found in the database.")
            return
            
        print(f"Using user: {user.username}")
        
        # Create a request for the user dashboard
        request = factory.get('/dashboard/')
        request.user = user
        
        # Call the user dashboard view
        print("Testing user dashboard view...")
        response = user_dashboard(request)
        
        # Check if the view returned a response
        if response:
            print(f"User dashboard view returned a response with status code: {response.status_code}")
            if hasattr(response, 'content'):
                content_length = len(response.content)
                print(f"Response content length: {content_length} bytes")
                
                # Check if the response contains expected content
                if b'Total Questionnaires' in response.content:
                    print("Response contains 'Total Questionnaires'")
                else:
                    print("Response does not contain 'Total Questionnaires'")
                    
                if b'Recent Responses' in response.content:
                    print("Response contains 'Recent Responses'")
                else:
                    print("Response does not contain 'Recent Responses'")
        else:
            print("User dashboard view did not return a response.")
        
        # Test admin dashboard view if user is staff
        if user.is_staff:
            print("\nTesting admin dashboard view...")
            request = factory.get('/dashboard/admin/')
            request.user = user
            
            response = admin_dashboard(request)
            
            if response:
                print(f"Admin dashboard view returned a response with status code: {response.status_code}")
                if hasattr(response, 'content'):
                    content_length = len(response.content)
                    print(f"Response content length: {content_length} bytes")
                    
                    # Check if the response contains expected content
                    if b'Admin Dashboard' in response.content:
                        print("Response contains 'Admin Dashboard'")
                    else:
                        print("Response does not contain 'Admin Dashboard'")
            else:
                print("Admin dashboard view did not return a response.")
        
    except Exception as e:
        print(f"Error testing dashboard views: {e}")

if __name__ == "__main__":
    print("Starting view test...")
    try:
        test_dashboard_views()
        print("\nView test completed.")
    except Exception as e:
        print(f"Error in main: {e}")
