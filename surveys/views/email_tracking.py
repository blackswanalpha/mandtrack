from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import base64
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def track_email_open(request, tracking_id):
    """
    Track email opens
    
    Args:
        request: HTTP request
        tracking_id: Tracking ID for the email
    
    Returns:
        1x1 transparent pixel
    """
    try:
        from surveys.models.email_schedule import EmailLog
        
        # Find the email log
        log = EmailLog.objects.filter(tracking_id=tracking_id).first()
        
        if log:
            # Mark as opened
            log.mark_as_opened()
            
            logger.info(f"Email {tracking_id} opened by {log.recipient_email}")
        
        # Return a 1x1 transparent pixel
        pixel = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        return HttpResponse(pixel, content_type='image/gif')
    
    except Exception as e:
        logger.error(f"Error tracking email open: {str(e)}")
        return HttpResponse(status=500)

@csrf_exempt
def track_email_click(request, tracking_id):
    """
    Track email clicks
    
    Args:
        request: HTTP request
        tracking_id: Tracking ID for the email
    
    Returns:
        Redirect to the original URL
    """
    try:
        from surveys.models.email_schedule import EmailLog
        
        # Get the original URL
        encoded_url = request.GET.get('url', '')
        if not encoded_url:
            raise Http404("URL not found")
        
        # Decode the URL
        try:
            original_url = base64.urlsafe_b64decode(encoded_url.encode()).decode()
        except Exception:
            raise Http404("Invalid URL")
        
        # Find the email log
        log = EmailLog.objects.filter(tracking_id=tracking_id).first()
        
        if log:
            # Mark as clicked
            log.mark_as_clicked()
            
            logger.info(f"Email {tracking_id} link clicked by {log.recipient_email}")
        
        # Redirect to the original URL
        return redirect(original_url)
    
    except Exception as e:
        logger.error(f"Error tracking email click: {str(e)}")
        return HttpResponse(status=500)
