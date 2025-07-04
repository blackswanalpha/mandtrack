import logging
import traceback
import uuid
from django.shortcuts import redirect
from django.urls import resolve
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from .error_handlers import handle_exception, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)

class RoleBasedRedirectMiddleware:
    """
    Middleware to handle redirects based on user roles
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request before the view is called
        response = self.get_response(request)

        # Process the response after the view is called
        return response

    def process_view(self, request, view_func, *args, **kwargs):
        """
        Called just before Django calls the view.
        Parameters view_func, args, and kwargs are required by Django but not used in this middleware.
        """
        # Check for bypass flag in session
        if request.session.get('bypass_auth_redirect', False):
            # Clear the flag after using it
            request.session['bypass_auth_redirect'] = False
            return None

        # Skip if user is not authenticated
        if not request.user.is_authenticated:
            return None

        # Get the current URL name and namespace
        # Special case for Django admin URLs
        if request.path_info.startswith('/admin/'):
            # This is a Django admin URL, let Django's admin authentication handle it
            return None

        # Skip for client-specific minimal layout views
        if request.path_info.startswith('/responses/client/'):
            return None

        try:
            resolver_match = resolve(request.path_info)
            current_url = getattr(resolver_match, 'url_name', None)
            current_namespace = getattr(resolver_match, 'namespace', None)
        except:
            # If resolution fails, set defaults
            current_url = None
            current_namespace = None

        # Admin portal access control
        if (current_namespace == 'accounts' or
            (current_url is not None and current_url.startswith('admin_')) or
            request.path_info.startswith('/admin-portal/')):
            # Check if user is an admin
            if not hasattr(request.user, 'is_admin_user') or not request.user.is_admin_user():
                messages.error(request, "You don't have permission to access the admin portal.")
                return redirect('client_dashboard')

        # Client portal access control
        if (current_namespace == 'users' or
            (current_url is not None and current_url.startswith('client_')) or
            request.path_info.startswith('/client-portal/')):
            # If user is admin-only (not a client), redirect to admin portal
            if hasattr(request.user, 'is_admin_user') and request.user.is_admin_user() and not request.user.is_client_user():
                messages.info(request, "Admin users should use the admin portal.")
                return redirect('admin_dashboard')

        # Legacy dashboard redirects
        if current_url is not None and current_url == 'user_dashboard':
            if hasattr(request.user, 'is_admin_user') and request.user.is_admin_user():
                # Redirect admin users to admin dashboard
                return redirect('admin_dashboard')
            else:
                # Redirect client users to client dashboard
                return redirect('client_dashboard')

        # Continue with the request
        return None


class QRCodeMiddleware:
    """
    Middleware to handle QR code scanning and anonymous access
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request before the view is called
        response = self.get_response(request)

        # Process the response after the view is called
        return response

    def process_view(self, request, view_func, *args, **kwargs):
        """
        Called just before Django calls the view.
        Parameters view_func, args, and kwargs are required by Django but not used in this middleware.
        """
        # Skip Django admin URLs
        if request.path_info.startswith('/admin/'):
            return None

        # Check if this is a QR code access
        if 'qr_code' in request.GET:
            # Store QR code in session
            request.session['qr_code'] = request.GET.get('qr_code')

            # If user is not authenticated, redirect to email entry page
            if not request.user.is_authenticated:
                try:
                    return redirect('qr_email_entry')
                except:
                    # If redirect fails, just continue
                    pass

        # Continue with the request
        return None


class AdminPortalErrorMiddleware(MiddlewareMixin):
    """
    Middleware to handle errors in the admin portal.
    This middleware adds request IDs and handles exceptions in admin portal routes.
    """
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response

    def process_request(self, request):
        """Add a unique request ID to each request."""
        request.id = str(uuid.uuid4())

        # Check if this is an admin portal request
        if self._is_admin_portal_request(request):
            request.is_admin_portal = True
        else:
            request.is_admin_portal = False

        return None

    def process_exception(self, request, exception):
        """Handle exceptions for admin portal requests."""
        if hasattr(request, 'is_admin_portal') and request.is_admin_portal:
            return handle_exception(request, exception)
        return None

    def _is_admin_portal_request(self, request):
        """Check if the request is for the admin portal."""
        path = request.path_info.lstrip('/')

        # Check if path starts with admin-portal or dashboard/admin
        if path.startswith('admin-portal/') or path.startswith('dashboard/admin'):
            return True

        # Check if this is a Django admin URL
        if path.startswith('admin/'):
            return True

        # Try to resolve the URL and check the namespace
        try:
            resolver_match = resolve(request.path_info)
            if resolver_match.namespace in ['accounts', 'dashboard:admin']:
                return True
            if resolver_match.url_name and resolver_match.url_name.startswith('admin_'):
                return True
        except:
            pass

        return False


class VercelDebugMiddleware:
    """
    Middleware to help debug issues on Vercel.
    Only active when VERCEL_DEBUG is True in settings.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.is_active = getattr(settings, 'VERCEL_DEBUG', False)

    def __call__(self, request):
        if not self.is_active:
            return self.get_response(request)

        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            # Log the full traceback
            logger.error(f"Vercel Debug Exception: {str(e)}")
            logger.error(traceback.format_exc())

            # Only show detailed error in debug mode
            if settings.DEBUG:
                error_message = f"Error: {str(e)}\n\n{traceback.format_exc()}"
                return HttpResponse(f"<pre>{error_message}</pre>", status=500)
            else:
                return HttpResponse("Internal Server Error", status=500)