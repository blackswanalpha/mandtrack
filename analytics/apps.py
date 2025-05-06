from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'

    def ready(self):
        # Import models to register them
        import analytics.models

        # We'll avoid registering model aliases to prevent duplicate model issues
        # This will ensure each model is only registered once with its proper name
