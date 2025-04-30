from django.shortcuts import redirect
from django.urls import resolve
from django.contrib import messages

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
        # Skip if user is not authenticated
        if not request.user.is_authenticated:
            return None

        # Get the current URL name and namespace
        # Special case for Django admin URLs
        if request.path_info.startswith('/admin/'):
            # This is a Django admin URL, let Django's admin authentication handle it
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
