"""
Custom error handling middleware for MindTrack.

This middleware catches exceptions and provides better error handling
to prevent 500 Internal Server Errors from being shown to users.
"""

import sys
import logging
import traceback
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404

logger = logging.getLogger('error_middleware')

class ErrorHandlingMiddleware:
    """
    Middleware that catches exceptions and provides better error handling.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self.handle_exception(request, e)
    
    def handle_exception(self, request, exception):
        """
        Handle exceptions and return appropriate responses.
        """
        # Get exception info
        exc_type, exc_value, exc_traceback = sys.exc_info()
        stack_trace = traceback.format_exception(exc_type, exc_value, exc_traceback)
        
        # Log the exception
        logger.error(
            f"Unhandled exception: {str(exception)}",
            exc_info=(exc_type, exc_value, exc_traceback),
            extra={
                'request': request,
                'status_code': 500,
            }
        )
        
        # Handle specific exceptions
        if isinstance(exception, Http404):
            return self.handle_404(request, exception)
        elif isinstance(exception, PermissionDenied):
            return self.handle_403(request, exception)
        else:
            return self.handle_500(request, exception, stack_trace)
    
    def handle_404(self, request, exception):
        """Handle 404 Not Found errors."""
        if self.is_api_request(request):
            return JsonResponse({
                'error': 'Not Found',
                'detail': str(exception) or 'The requested resource was not found.',
            }, status=404)
        else:
            return self.render_error_page(request, 404, 'Page Not Found', str(exception))
    
    def handle_403(self, request, exception):
        """Handle 403 Forbidden errors."""
        if self.is_api_request(request):
            return JsonResponse({
                'error': 'Forbidden',
                'detail': str(exception) or 'You do not have permission to access this resource.',
            }, status=403)
        else:
            return self.render_error_page(request, 403, 'Access Denied', str(exception))
    
    def handle_500(self, request, exception, stack_trace):
        """Handle 500 Internal Server Error."""
        error_id = self.generate_error_id()
        error_message = f"Internal Server Error (ID: {error_id})"
        
        # Include stack trace in development
        debug_info = None
        if settings.DEBUG:
            debug_info = {
                'exception_type': exception.__class__.__name__,
                'exception_value': str(exception),
                'stack_trace': stack_trace,
            }
        
        if self.is_api_request(request):
            response_data = {
                'error': 'Internal Server Error',
                'error_id': error_id,
                'detail': 'An unexpected error occurred. Our team has been notified.',
            }
            
            if debug_info:
                response_data['debug'] = debug_info
            
            return JsonResponse(response_data, status=500)
        else:
            return self.render_error_page(
                request, 
                500, 
                'Internal Server Error', 
                'An unexpected error occurred. Our team has been notified.',
                error_id=error_id,
                debug_info=debug_info
            )
    
    def is_api_request(self, request):
        """Check if the request is an API request."""
        return (
            request.path.startswith('/api/') or
            request.headers.get('Accept') == 'application/json' or
            request.headers.get('Content-Type') == 'application/json' or
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        )
    
    def generate_error_id(self):
        """Generate a unique error ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def render_error_page(self, request, status_code, title, message, error_id=None, debug_info=None):
        """Render an error page."""
        try:
            # Try to render a custom error template
            template_name = f"errors/{status_code}.html"
            html = render_to_string(template_name, {
                'title': title,
                'message': message,
                'error_id': error_id,
                'debug_info': debug_info,
                'request': request,
            })
            return HttpResponse(html, status=status_code)
        except Exception:
            # Fallback to a simple error page
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #d9534f; }}
                    .error-container {{ border: 1px solid #ddd; border-radius: 4px; padding: 20px; margin-top: 20px; }}
                    .error-id {{ color: #777; font-size: 0.9em; margin-top: 15px; }}
                    .debug-info {{ background: #f8f9fa; border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin-top: 20px; overflow: auto; }}
                    pre {{ margin: 0; white-space: pre-wrap; }}
                </style>
            </head>
            <body>
                <h1>{title}</h1>
                <div class="error-container">
                    <p>{message}</p>
                    {f'<p class="error-id">Error ID: {error_id}</p>' if error_id else ''}
                </div>
                
                {'''
                <div class="debug-info">
                    <h3>Debug Information</h3>
                    <p><strong>Exception Type:</strong> {debug_info['exception_type']}</p>
                    <p><strong>Exception Value:</strong> {debug_info['exception_value']}</p>
                    <h4>Traceback</h4>
                    <pre>{''.join(debug_info['stack_trace'])}</pre>
                </div>
                ''' if debug_info else ''}
                
                <p><a href="/">Return to Home Page</a></p>
            </body>
            </html>
            """
            return HttpResponse(html, status=status_code)
