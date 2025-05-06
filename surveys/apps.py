from django.apps import AppConfig


class SurveysConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'surveys'

    def ready(self):
        """
        Import models to register them with the app registry
        """
        # Import models to register them
        import surveys.models

        # Import specific model modules to ensure they're registered
        import surveys.models.email_schedule
        import surveys.models.scoring

        # We'll avoid registering model aliases to prevent duplicate model issues
        # This will ensure each model is only registered once with its proper name

        # Register admin classes
        import surveys.admin

        # Apply the QuestionnaireSelectorMixin to the Questionnaire model
        try:
            from surveys.models.mixins import QuestionnaireSelectorMixin
            from surveys.models import Questionnaire
            QuestionnaireSelectorMixin.add_to_class(Questionnaire)
        except (ImportError, AttributeError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error applying QuestionnaireSelectorMixin: {e}")
