from django.conf import settings

def debug_processor(request):
    """
    Add debug variable to all template contexts.
    """
    return {'debug': settings.DEBUG}
