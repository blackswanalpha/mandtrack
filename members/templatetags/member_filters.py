from django import template
import math

register = template.Library()

@register.filter
def format_seconds(seconds):
    """
    Format seconds into a human-readable string (e.g., "2 min 30 sec" or "45 seconds")
    """
    if not seconds:
        return "N/A"
    
    try:
        seconds = int(float(seconds))
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        
        if minutes > 0:
            return f"{minutes} min {remaining_seconds} sec"
        else:
            return f"{seconds} seconds"
    except (ValueError, TypeError):
        return "N/A"
