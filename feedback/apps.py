from django.apps import AppConfig


class FeedbackConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feedback'

    def ready(self):
        # Import signals
        import feedback.signals

        # Import models to register them
        import feedback.models

        # We'll avoid registering model aliases to prevent duplicate model issues
        # This will ensure each model is only registered once with its proper name
