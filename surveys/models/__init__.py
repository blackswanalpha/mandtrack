# Import from the main models.py file
# We'll use lazy imports to avoid circular imports
from django.apps import apps
from django.db.utils import OperationalError

def get_model(app_label, model_name):
    """Get a model from the app registry"""
    try:
        return apps.get_model(app_label, model_name)
    except (LookupError, OperationalError):
        return None

# Define lazy model getters with fallbacks to actual database model names
def get_questionnaire():
    """Get the Questionnaire model"""
    # Try all possible model names
    for model_name in ['Questionnaire', 'Survey', 'questionnaire', 'survey', 'SurveysQuestionnaire']:
        model = get_model('surveys', model_name)
        if model is not None:
            return model
    return None

def get_question():
    """Get the Question model"""
    # Try all possible model names
    for model_name in ['Question', 'question', 'SurveysQuestion']:
        model = get_model('surveys', model_name)
        if model is not None:
            return model
    return None

def get_question_choice():
    """Get the QuestionChoice model"""
    # Try all possible model names
    for model_name in ['QuestionChoice', 'questionchoice', 'SurveysQuestionchoice']:
        model = get_model('surveys', model_name)
        if model is not None:
            return model
    return None

def get_qr_code():
    """Get the QRCode model"""
    # Try all possible model names
    for model_name in ['QRCode', 'qrcode', 'SurveysQrcode']:
        model = get_model('surveys', model_name)
        if model is not None:
            return model
    return None

def get_scoring_config():
    """Get the ScoringConfig model"""
    # Try all possible model names
    for model_name in ['ScoringConfig', 'scoringconfig', 'SurveysScoringconfig']:
        model = get_model('surveys', model_name)
        if model is not None:
            return model
    return None

# Import from email_schedule.py
from surveys.models.email_schedule import EmailSchedule, EmailLog, EmailTemplate

# Import from scoring.py
from surveys.models.scoring import (
    ScoringSystem, ScoreRule, OptionScore, ScoreRange, ResponseScore
)

# Import from feedback.py
from surveys.models.feedback import EnhancedScoringFeedback

# Import from question_type.py
from surveys.models.question_type import QuestionType, get_icon_for_type

# Import from main models.py
# This is done after the other imports to avoid circular imports
from surveys.models.main import (
    get_questionnaire, get_question, get_question_choice, get_qr_code, get_scoring_config, get_question_type
)

# Define model aliases - use direct database model names for reliability
try:
    # Use the actual model classes directly
    from django.db import models
    from django.conf import settings
    import uuid

    class SurveysQuestionnaire(models.Model):
        """
        Model for questionnaires
        """
        # Use CharField instead of BigAutoField to match the database schema
        # The database has a char(32) field, not a BigAutoField
        # Define a function to generate UUID hex
        def generate_uuid_hex():
            return uuid.uuid4().hex

        id = models.CharField(max_length=32, primary_key=True, default=generate_uuid_hex, editable=False)
        title = models.CharField(max_length=255)
        slug = models.SlugField(max_length=255, unique=True)
        description = models.TextField(blank=True, null=True)
        instructions = models.TextField(blank=True, null=True)
        category = models.CharField(max_length=50, blank=True, null=True)
        type = models.CharField(max_length=50, default='standard')
        estimated_time = models.PositiveIntegerField(help_text="Estimated time to complete in minutes", default=10)
        status = models.CharField(max_length=20, default='draft')
        is_active = models.BooleanField(default=True)
        is_adaptive = models.BooleanField(default=False)
        is_qr_enabled = models.BooleanField(default=True)
        is_public = models.BooleanField(default=False)
        allow_anonymous = models.BooleanField(default=True)
        requires_auth = models.BooleanField(default=False)
        version = models.PositiveIntegerField(default=1)
        tags = models.JSONField(default=list)
        language = models.CharField(max_length=10, default='en')
        time_limit = models.PositiveIntegerField(default=0, help_text="Time limit in minutes (0 for no limit)")
        organization = models.ForeignKey('groups.Organization', on_delete=models.CASCADE, null=True, blank=True, related_name='questionnaires')
        created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_questionnaires')
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
        access_code = models.CharField(max_length=20, blank=True, null=True, unique=True)
        is_template = models.BooleanField(default=False)

        class Meta:
            app_label = 'surveys'
            db_table = 'surveys_questionnaire'

    class SurveysQuestion(models.Model):
        """
        Model for questions
        """
        survey = models.ForeignKey(SurveysQuestionnaire, on_delete=models.CASCADE, related_name='questions')
        text = models.TextField()
        description = models.TextField(blank=True, null=True)
        question_type = models.CharField(max_length=50, default='text')
        # Add a reference to the QuestionType model
        question_type_obj = models.ForeignKey('surveys.QuestionType', on_delete=models.SET_NULL, related_name='questions', null=True, blank=True)
        required = models.BooleanField(default=True)
        order = models.IntegerField(default=0)
        is_scored = models.BooleanField(default=False)
        is_visible = models.BooleanField(default=True)
        scoring_weight = models.FloatField(default=1.0)
        max_score = models.IntegerField(default=0)
        category = models.CharField(max_length=50, blank=True, null=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

        # Define choices for question_type
        TYPE_CHOICES = [
            ('text', 'Text'),
            ('textarea', 'Text Area'),
            ('single_choice', 'Single Choice'),
            ('multiple_choice', 'Multiple Choice'),
            ('scale', 'Scale'),
            ('date', 'Date'),
            ('time', 'Time'),
            ('email', 'Email'),
            ('number', 'Number'),
            ('phone', 'Phone'),
            ('file', 'File Upload'),
            ('image', 'Image Upload'),
            ('signature', 'Signature'),
            ('location', 'Location'),
            ('rating', 'Rating'),
            ('matrix', 'Matrix'),
            ('slider', 'Slider'),
            ('dropdown', 'Dropdown'),
            ('checkbox', 'Checkbox'),
            ('radio', 'Radio Button'),
            ('hidden', 'Hidden'),
        ]

        class Meta:
            app_label = 'surveys'
            db_table = 'surveys_question'

    class SurveysQuestionchoice(models.Model):
        """
        Model for question choices
        """
        question = models.ForeignKey(SurveysQuestion, on_delete=models.CASCADE, related_name='choices')
        text = models.CharField(max_length=255)
        order = models.IntegerField(default=0)
        score = models.IntegerField(default=0)
        is_correct = models.BooleanField(default=False)

        class Meta:
            app_label = 'surveys'
            db_table = 'surveys_questionchoice'

    class SurveysQrcode(models.Model):
        """
        Model for QR codes
        """
        survey = models.ForeignKey(SurveysQuestionnaire, on_delete=models.CASCADE, related_name='qr_codes')
        name = models.CharField(max_length=255)
        description = models.TextField(blank=True, null=True)
        code = models.CharField(max_length=255, unique=True)
        is_active = models.BooleanField(default=True)
        expires_at = models.DateTimeField(blank=True, null=True)

        class Meta:
            app_label = 'surveys'
            db_table = 'surveys_qrcode'

    class SurveysScoringconfig(models.Model):
        """
        Model for scoring configurations
        """
        survey = models.ForeignKey(SurveysQuestionnaire, on_delete=models.CASCADE, related_name='scoring_configs')
        name = models.CharField(max_length=255)
        description = models.TextField(blank=True, null=True)
        scoring_method = models.CharField(max_length=50, default='sum')
        max_score = models.IntegerField(default=100)
        passing_score = models.IntegerField(default=60)
        rules = models.JSONField(default=dict, blank=True)
        is_active = models.BooleanField(default=True)
        is_default = models.BooleanField(default=False)

        class Meta:
            app_label = 'surveys'
            db_table = 'surveys_scoringconfig'

    class SurveysEmailtemplate(models.Model):
        """
        Model for email templates
        """
        name = models.CharField(max_length=255)
        description = models.TextField(blank=True, null=True)
        subject = models.CharField(max_length=255)
        message = models.TextField()
        html_content = models.TextField(blank=True, null=True)
        variables = models.JSONField(default=list, blank=True)
        category = models.CharField(max_length=50, default='notification')
        is_active = models.BooleanField(default=True)
        is_default = models.BooleanField(default=False)
        organization = models.ForeignKey('groups.Organization', on_delete=models.CASCADE, null=True, blank=True, related_name='surveys_email_templates')

        class Meta:
            app_label = 'surveys'
            db_table = 'surveys_emailtemplate_proxy'

    # Set up aliases
    Questionnaire = SurveysQuestionnaire
    Question = SurveysQuestion
    QuestionChoice = SurveysQuestionchoice
    QRCode = SurveysQrcode
    ScoringConfig = SurveysScoringconfig
    EmailTemplate = SurveysEmailtemplate

    # Create aliases for backward compatibility
    Survey = Questionnaire
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Error setting up model aliases: {e}")

    # Fallback to getter functions if direct access fails
    Questionnaire = get_questionnaire()
    Question = get_question()
    QuestionChoice = get_question_choice()
    QRCode = get_qr_code()
    ScoringConfig = get_scoring_config()
    EmailTemplate = None  # Fallback for EmailTemplate

    # Create aliases for backward compatibility
    Survey = Questionnaire

# Define all exported symbols
__all__ = [
    'get_questionnaire', 'get_question', 'get_question_choice', 'get_qr_code', 'get_scoring_config', 'get_question_type',
    'Questionnaire', 'Question', 'QuestionChoice', 'QRCode', 'ScoringConfig', 'Survey', 'QuestionType',
    'ScoringSystem', 'ScoreRule', 'ScoreRange', 'ResponseScore', 'OptionScore',
    'EmailSchedule', 'EmailLog', 'EmailTemplate', 'SurveysEmailtemplate',
    'EnhancedScoringFeedback', 'get_icon_for_type'
]
