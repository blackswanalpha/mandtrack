from django.apps import AppConfig

class SurveysConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'surveys'

    def ready(self):
        """
        Import models to register them with the app registry
        """
        # Import models to register them
        from surveys.models import Questionnaire, Question, QuestionChoice, QRCode, ScoringConfig
        from surveys.models.scoring import ScoringSystem, ScoreRule, ScoreRange, ResponseScore, OptionScore
        from surveys.models.email_schedule import EmailSchedule, EmailLog
