from django import template

register = template.Library()

@register.filter
def filter_by_range(scores, range_id):
    """
    Filter scores by score range ID
    """
    return [score for score in scores if score.score_range and score.score_range.id == range_id]

@register.filter
def percentage(value, total):
    """
    Calculate percentage
    """
    try:
        return round((value / total) * 100, 1)
    except (ValueError, ZeroDivisionError):
        return 0
