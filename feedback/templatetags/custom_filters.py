from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def divisibleby(value, arg):
    """Return the integer division of value by arg."""
    try:
        return int(float(value)) // int(float(arg))
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def modulo(value, arg):
    """Return the remainder of value divided by arg."""
    try:
        return int(float(value)) % int(float(arg))
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def to_json(value):
    """Convert a Python object to a JSON string."""
    return mark_safe(json.dumps(value))

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary."""
    if dictionary is None:
        return None
    return dictionary.get(key)
