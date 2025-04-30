"""
Error handling utilities for MindTrack.
This module contains functions and classes for handling errors in a consistent way.
"""

import logging
import traceback
import json
import sys
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.utils import timezone

# Configure logger
logger = logging.getLogger('error_handlers')

# Error severity levels
class ErrorSeverity:
    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'

# Error categories
class ErrorCategory:
    AUTHENTICATION = 'authentication'
    AUTHORIZATION = 'authorization'
    VALIDATION = 'validation'
    DATABASE = 'database'
    NETWORK = 'network'
    EXTERNAL_SERVICE = 'external_service'
    INTERNAL = 'internal'
    UNKNOWN = 'unknown'

class ErrorResponse:
    """
    Standardized error response class.
    """
    def __init__(self, message, status_code=500, error_code=None, 
                 category=ErrorCategory.UNKNOWN, severity=ErrorSeverity.ERROR, 
                 details=None, request=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERR{status_code}"
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.timestamp = timezone.now().isoformat()
        self.request_id = getattr(request, 'id', None)
        self.user_id = request.user.id if request and request.user.is_authenticated else None
        
        # Log the error
        self._log_error(request)
    
    def _log_error(self, request):
        """Log the error with appropriate severity level."""
        log_data = {
            'message': self.message,
            'status_code': self.status_code,
            'error_code': self.error_code,
            'category': self.category,
            'timestamp': self.timestamp,
            'request_id': self.request_id,
            'user_id': self.user_id,
        }
        
        # Add request details if available
        if request:
            log_data.update({
                'method': request.method,
                'path': request.path,
                'ip': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT'),
            })
        
        # Add details if not empty
        if self.details:
            log_data['details'] = self.details
        
        # Log with appropriate level
        log_message = f"{self.error_code}: {self.message}"
        if self.severity == ErrorSeverity.DEBUG:
            logger.debug(log_message, extra=log_data)
        elif self.severity == ErrorSeverity.INFO:
            logger.info(log_message, extra=log_data)
        elif self.severity == ErrorSeverity.WARNING:
            logger.warning(log_message, extra=log_data)
        elif self.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra=log_data)
        else:  # Default to ERROR
            logger.error(log_message, extra=log_data)
    
    def to_dict(self):
        """Convert error response to dictionary."""
        result = {
            'status': 'error',
            'message': self.message,
            'error_code': self.error_code,
            'category': self.category,
            'timestamp': self.timestamp,
        }
        
        # Add request_id if available
        if self.request_id:
            result['request_id'] = self.request_id
        
        # Add details if not empty
        if self.details:
            result['details'] = self.details
        
        # Add stack trace in debug mode
        if settings.DEBUG and 'stack_trace' in self.details:
            result['stack_trace'] = self.details['stack_trace']
        
        return result
    
    def to_json_response(self):
        """Convert to Django JsonResponse."""
        return JsonResponse(self.to_dict(), status=self.status_code)
    
    def to_html_response(self, request):
        """Render HTML error page."""
        template_name = f"errors/{self.status_code}.html"
        
        # Fallback to generic error template if specific one doesn't exist
        try:
            return render(request, template_name, {
                'error': self.to_dict(),
                'status_code': self.status_code,
                'message': self.message,
                'error_code': self.error_code,
                'category': self.category,
                'details': self.details,
                'timestamp': self.timestamp,
                'request_id': self.request_id,
                'debug': settings.DEBUG,
            })
        except:
            # If specific template doesn't exist, use generic error template
            return render(request, "errors/error.html", {
                'error': self.to_dict(),
                'status_code': self.status_code,
                'message': self.message,
                'error_code': self.error_code,
                'category': self.category,
                'details': self.details,
                'timestamp': self.timestamp,
                'request_id': self.request_id,
                'debug': settings.DEBUG,
            })

def handle_exception(request, exception):
    """
    Global exception handler that creates appropriate error responses.
    """
    # Get exception details
    exc_type, exc_value, exc_traceback = sys.exc_info()
    stack_trace = traceback.format_exception(exc_type, exc_value, exc_traceback)
    
    # Default values
    status_code = 500
    message = str(exception) or "Internal Server Error"
    category = ErrorCategory.INTERNAL
    severity = ErrorSeverity.ERROR
    error_code = "ERR500"
    details = {'stack_trace': stack_trace}
    
    # Handle specific exception types
    if hasattr(exception, 'status_code'):
        status_code = exception.status_code
    
    # Create error response
    error_response = ErrorResponse(
        message=message,
        status_code=status_code,
        error_code=error_code,
        category=category,
        severity=severity,
        details=details,
        request=request
    )
    
    # Return appropriate response based on request type
    if request.headers.get('Accept') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return error_response.to_json_response()
    else:
        return error_response.to_html_response(request)

# Common error response generators
def validation_error(request, message, details=None):
    """Generate a validation error response."""
    return ErrorResponse(
        message=message,
        status_code=400,
        error_code="ERR400",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.WARNING,
        details=details,
        request=request
    )

def permission_error(request, message="You don't have permission to perform this action"):
    """Generate a permission error response."""
    return ErrorResponse(
        message=message,
        status_code=403,
        error_code="ERR403",
        category=ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.WARNING,
        request=request
    )

def not_found_error(request, message="The requested resource was not found"):
    """Generate a not found error response."""
    return ErrorResponse(
        message=message,
        status_code=404,
        error_code="ERR404",
        category=ErrorCategory.UNKNOWN,
        severity=ErrorSeverity.WARNING,
        request=request
    )

def server_error(request, message="Internal server error", exception=None):
    """Generate a server error response."""
    details = None
    if exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        stack_trace = traceback.format_exception(exc_type, exc_value, exc_traceback)
        details = {'stack_trace': stack_trace, 'exception': str(exception)}
    
    return ErrorResponse(
        message=message,
        status_code=500,
        error_code="ERR500",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        details=details,
        request=request
    )
