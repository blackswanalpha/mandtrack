from django import template
from django.template.defaultfilters import floatformat
from django.db.models import Avg

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary using a key
    """
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """
    Multiply the value by the argument
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def div(value, arg):
    """
    Divide the value by the argument
    """
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def get_day_name(day_number):
    """
    Get the name of the day from a day number (0-6)
    """
    days = {
        '0': 'Monday',
        '1': 'Tuesday',
        '2': 'Wednesday',
        '3': 'Thursday',
        '4': 'Friday',
        '5': 'Saturday',
        '6': 'Sunday'
    }

    try:
        return days.get(str(day_number), 'Unknown')
    except (ValueError, TypeError):
        return 'Unknown'

@register.filter
def filter_by_status(responses, status):
    """
    Filter responses by status
    """
    return [r for r in responses if r.status == status]

@register.filter
def filter_by_risk_level(responses, risk_levels):
    """
    Filter responses by risk level
    """
    risk_level_list = risk_levels.split(',')
    return [r for r in responses if r.risk_level in risk_level_list]

@register.filter
def filter_scores(responses):
    """
    Filter out responses with no score
    """
    return [r.score for r in responses if r.score is not None]

@register.filter
def avg(values):
    """
    Calculate the average of a list of values
    """
    try:
        if not values:
            return 0
        return sum(values) / len(values)
    except (ValueError, TypeError):
        return 0
