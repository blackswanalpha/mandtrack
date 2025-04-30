from django import template
import pprint as pp
import json

register = template.Library()

@register.filter
def pprint(value):
    """Pretty print a variable for debugging"""
    try:
        if isinstance(value, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(value)
                return json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                return value
        else:
            # Use pprint for other objects
            return pp.pformat(value, indent=2)
    except Exception as e:
        return f"Error formatting: {str(e)}"
