from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

# Import email schedule models
from surveys.models.email_schedule import EmailSchedule, EmailLog

# Import data for selector features
from surveys.data.selector_data import (
    QUESTIONNAIRE_CATEGORIES,
    QUESTIONNAIRE_TYPES,
    QUESTIONNAIRE_STATUSES,
    QUESTION_TYPES,
    QUESTION_CATEGORIES
)

# Import scoring models - we'll import these at the end of the file to avoid circular imports

class Questionnaire(models.Model):
    """
    Model for questionnaires/surveys
    """
    class Meta:
        db_table = 'surveys_questionnaire'

    # Use imported choices from selector_data.py
    CATEGORY_CHOICES = QUESTIONNAIRE_CATEGORIES
    TYPE_CHOICES = QUESTIONNAIRE_TYPES
    STATUS_CHOICES = QUESTIONNAIRE_STATUSES

    # Use CharField instead of UUIDField to match the database schema
    # The database has a char(32) field, not a UUID field
    # Define a function to generate UUID hex
    def generate_uuid_hex():
        return uuid.uuid4().hex

    id = models.CharField(max_length=32, primary_key=True, default=generate_uuid_hex, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='standard')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='custom')
    estimated_time = models.PositiveIntegerField(help_text="Estimated time to complete in minutes", default=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=True)
    is_adaptive = models.BooleanField(default=False)
    is_qr_enabled = models.BooleanField(default=True)
    is_template = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    allow_anonymous = models.BooleanField(default=True, help_text="Whether to allow anonymous responses")
    requires_auth = models.BooleanField(default=False, help_text="Whether respondents need to be logged in")
    max_responses = models.PositiveIntegerField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    version = models.PositiveIntegerField(default=1)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='versions')
    tags = models.JSONField(default=list)
    language = models.CharField(max_length=10, default='en')
    time_limit = models.PositiveIntegerField(default=0, help_text="Time limit in minutes (0 for no limit)")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_questionnaires')
    organization = models.ForeignKey('groups.Organization', on_delete=models.CASCADE, related_name='questionnaires', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    access_code = models.CharField(max_length=20, blank=True, null=True, unique=True)
    is_template = models.BooleanField(default=False, help_text='Whether this questionnaire is a template that can be used to create new questionnaires')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Questionnaire'
        verbose_name_plural = 'Questionnaires'
        indexes = [
            models.Index(fields=['is_active'], name='surveys_questionnaire_is_active_idx'),
            models.Index(fields=['is_public'], name='surveys_questionnaire_is_public_idx'),
            models.Index(fields=['category'], name='surveys_questionnaire_category_idx'),
            models.Index(fields=['type'], name='surveys_questionnaire_type_idx'),
            models.Index(fields=['created_at'], name='surveys_questionnaire_created_at_idx'),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Generate access code if not provided
        if not self.access_code:
            self.access_code = str(uuid.uuid4())[:8].upper()

        # Generate QR code if not exists
        if not self.qr_code and self.is_qr_enabled:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(f"{settings.SITE_URL}/questionnaires/{self.id}/")
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            self.qr_code.save(f"qr_{self.id}.png", File(buffer), save=False)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"/questionnaires/{self.id}/"

    def get_question_count(self):
        return self.questions.count()

    def get_response_count(self):
        return self.responses.count()

    def get_completion_rate(self):
        """Calculate the completion rate of responses"""
        total_responses = self.responses.count()
        if total_responses == 0:
            return 0
        completed_responses = self.responses.filter(completed_at__isnull=False).count()
        return (completed_responses / total_responses) * 100

    def get_average_score(self):
        """Calculate the average score of completed responses"""
        completed_responses = self.responses.filter(completed_at__isnull=False, score__isnull=False)
        if not completed_responses.exists():
            return 0
        return completed_responses.aggregate(models.Avg('score'))['score__avg'] or 0


class QuestionType(models.Model):
    """
    Model for question types
    """
    class Meta:
        db_table = 'surveys_questiontype'
        ordering = ['display_order', 'name']
        verbose_name = 'Question Type'
        verbose_name_plural = 'Question Types'

    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    has_choices = models.BooleanField(default=False)
    is_numeric = models.BooleanField(default=False)
    is_text = models.BooleanField(default=False)
    is_date = models.BooleanField(default=False)
    is_file = models.BooleanField(default=False)
    is_scorable = models.BooleanField(default=False)
    default_max_score = models.FloatField(default=0)
    default_scoring_weight = models.FloatField(default=1.0)
    display_order = models.PositiveIntegerField(default=0)
    icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_default_types(cls):
        """Return default question types if none exist"""
        # Create a list of default types based on the QUESTION_TYPES from selector_data.py
        default_types = []
        for i, (code, name) in enumerate(QUESTION_TYPES):
            type_data = {
                'code': code,
                'name': name,
                'display_order': i + 1,
                'is_text': code in ['text', 'textarea', 'email'],
                'has_choices': code in ['single_choice', 'multiple_choice', 'dropdown', 'radio', 'checkbox', 'country'],
                'is_numeric': code in ['number', 'scale', 'rating', 'slider'],
                'is_date': code in ['date', 'time'],
                'is_file': code in ['file', 'image'],
                'is_scorable': code in ['single_choice', 'multiple_choice', 'scale', 'number', 'rating'],
            }
            default_types.append(type_data)

        # Ensure country question type is available
        if not any(t['code'] == 'country' for t in default_types):
            default_types.append({
                'code': 'country',
                'name': 'Country',
                'has_choices': True,
                'is_text': False,
                'display_order': len(default_types) + 1
            })

        return default_types


class Question(models.Model):
    """
    Model for questions in a questionnaire
    """
    class Meta:
        db_table = 'surveys_question'

    # Use imported choices from selector_data.py
    TYPE_CHOICES = QUESTION_TYPES
    CATEGORY_CHOICES = QUESTION_CATEGORIES

    id = models.BigAutoField(primary_key=True)
    # Use the correct model reference
    survey = models.ForeignKey('surveys.Questionnaire', on_delete=models.CASCADE, related_name='questions', null=True)
    text = models.TextField()
    description = models.TextField(blank=True)
    # Keep the CharField for backward compatibility
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='text')
    # Add a reference to the QuestionType model
    question_type_obj = models.ForeignKey(QuestionType, on_delete=models.SET_NULL, related_name='questions', null=True, blank=True)
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    options = models.JSONField(blank=True, null=True)
    conditional_logic = models.JSONField(blank=True, null=True)
    validation_rules = models.JSONField(blank=True, null=True)
    # Make scoring_weight nullable with a default value
    scoring_weight = models.FloatField(null=True, blank=True, default=1.0)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True, null=True)
    # Make max_score nullable with a default value
    max_score = models.FloatField(null=True, blank=True, default=0)
    is_scored = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Update the Meta class to include both db_table and other options
    class Meta:
        db_table = 'surveys_question'
        ordering = ['order']
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        indexes = [
            models.Index(fields=['survey'], name='surveys_question_survey_idx'),
            models.Index(fields=['question_type'], name='surveys_question_type_idx'),
            models.Index(fields=['order'], name='surveys_question_order_idx'),
        ]

    def __str__(self):
        return f"{self.text[:50]}..." if len(self.text) > 50 else self.text

    def get_choices(self):
        return self.choices.all()

    def save(self, *args, **kwargs):
        """
        Override save method to ensure proper handling of the survey field
        and to perform any necessary validation
        """
        # Log the save operation for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Saving question with ID: {self.id}, text: {self.text}, type: {self.question_type}")

        # Ensure question_type is valid
        if not self.question_type:
            self.question_type = 'text'
            logger.warning(f"Question type was empty, defaulting to 'text'")

        # Link to QuestionType object if not already set and the field exists
        try:
            if hasattr(self, 'question_type_obj') and not self.question_type_obj:
                try:
                    self.question_type_obj = QuestionType.objects.filter(code=self.question_type).first()
                    if not self.question_type_obj:
                        logger.warning(f"No QuestionType found for code: {self.question_type}")
                except Exception as e:
                    logger.error(f"Error linking to QuestionType: {e}")
        except Exception as e:
            logger.error(f"Error checking question_type_obj field: {e}")

        # Set default values for scoring fields based on question type
        if self.is_scored:
            # If question is scored but scoring_weight is not set, use default
            if self.scoring_weight is None:
                if self.question_type_obj and self.question_type_obj.is_scorable:
                    self.scoring_weight = self.question_type_obj.default_scoring_weight
                else:
                    self.scoring_weight = 1.0
                logger.info(f"Setting default scoring_weight: {self.scoring_weight}")

            # If question is scored but max_score is not set, use default
            if self.max_score is None:
                if self.question_type_obj and self.question_type_obj.is_scorable:
                    self.max_score = self.question_type_obj.default_max_score
                else:
                    self.max_score = 0
                logger.info(f"Setting default max_score: {self.max_score}")
        else:
            # If question is not scored, set scoring fields to default values
            if self.scoring_weight is None:
                self.scoring_weight = 1.0
            if self.max_score is None:
                self.max_score = 0

        # Ensure survey relationship is set
        if not self.survey:
            logger.error(f"Question has no survey relationship")

        # Call the parent save method
        super().save(*args, **kwargs)

        # Log successful save
        logger.info(f"Question saved successfully with ID: {self.id}")

        # For choice-based questions, ensure there are choices
        if self.question_type in ['single_choice', 'multiple_choice'] and not self.choices.exists():
            logger.warning(f"Choice-based question has no choices, consider adding some")


class QuestionChoiceManager(models.Manager):
    """
    Custom manager for QuestionChoice model to handle created_at and updated_at fields
    """
    def create(self, **kwargs):
        # Set created_at and updated_at if not provided
        if 'created_at' not in kwargs:
            kwargs['created_at'] = timezone.now()
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = timezone.now()
        return super().create(**kwargs)

class QuestionChoice(models.Model):
    """
    Model for choices in multiple choice questions
    """
    class Meta:
        db_table = 'surveys_questionchoice'
    id = models.BigAutoField(primary_key=True)
    # Use the correct model reference
    question = models.ForeignKey('surveys.Question', on_delete=models.CASCADE, related_name='choices', null=True)
    text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    score = models.IntegerField(default=0)  # For scoring responses
    is_correct = models.BooleanField(default=False)  # For knowledge questions
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField()  # Removed auto_now_add=True
    updated_at = models.DateTimeField()  # Removed auto_now=True

    # Use the custom manager
    objects = QuestionChoiceManager()

    # Update the Meta class to include both db_table and other options
    class Meta:
        db_table = 'surveys_questionchoice'
        ordering = ['order']
        verbose_name = 'Question Choice'
        verbose_name_plural = 'Question Choices'
        indexes = [
            models.Index(fields=['question'], name='surveys_questionchoice_question_idx'),
            models.Index(fields=['order'], name='surveys_questionchoice_order_idx'),
        ]

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        # Set created_at and updated_at if not set
        if not self.created_at:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class QRCode(models.Model):
    """
    Model for QR codes for questionnaire access
    """
    class Meta:
        db_table = 'surveys_qrcode'
    id = models.BigAutoField(primary_key=True)
    # Keep the original field name for database compatibility
    # Use the correct model reference
    survey = models.ForeignKey('surveys.Questionnaire', on_delete=models.CASCADE, related_name='qr_codes', null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    url = models.URLField()
    access_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_qr_codes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add property for questionnaire to maintain API compatibility
    @property
    def questionnaire(self):
        return self.survey

    @questionnaire.setter
    def questionnaire(self, value):
        self.survey = value

    # Update the Meta class to include both db_table and other options
    class Meta:
        db_table = 'surveys_qrcode'
        ordering = ['-created_at']
        verbose_name = 'QR Code'
        verbose_name_plural = 'QR Codes'
        indexes = [
            models.Index(fields=['survey'], name='surveys_qrcode_survey_idx'),
            models.Index(fields=['is_active'], name='surveys_qrcode_is_active_idx'),
            models.Index(fields=['created_at'], name='surveys_qrcode_created_at_idx'),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Generate QR code image if not exists
        if not self.image:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            self.image.save(f"qr_{self.name.lower().replace(' ', '_')}.png", File(buffer), save=False)

        super().save(*args, **kwargs)

    def increment_access_count(self):
        """Increment the access count when QR code is scanned"""
        self.access_count += 1
        self.save(update_fields=['access_count'])


class ScoringConfig(models.Model):
    """
    Model for questionnaire scoring configurations
    """
    SCORING_METHOD_CHOICES = [
        ('sum', 'Sum of Scores'),
        ('average', 'Average Score'),
        ('weighted_sum', 'Weighted Sum'),
        ('custom', 'Custom Formula'),
    ]

    id = models.BigAutoField(primary_key=True)
    # Use the correct model reference
    survey = models.ForeignKey('surveys.Questionnaire', on_delete=models.CASCADE, related_name='scoring_configs', null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    scoring_method = models.CharField(max_length=20, choices=SCORING_METHOD_CHOICES, default='sum')
    max_score = models.FloatField(default=100)
    passing_score = models.FloatField(default=70)
    rules = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_scoring_configs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Scoring Configuration'
        verbose_name_plural = 'Scoring Configurations'
        indexes = [
            models.Index(fields=['survey'], name='surveys_scoringconfig_survey_idx'),
            models.Index(fields=['is_active'], name='surveys_scoringconfig_is_active_idx'),
            models.Index(fields=['is_default'], name='surveys_scoringconfig_is_default_idx'),
        ]

    def __str__(self):
        return f"{self.name} for {self.survey.title}"

    def calculate_score(self, response):
        """
        Calculate score based on the scoring method and rules
        """
        if self.scoring_method == 'sum':
            return self._calculate_sum_score(response)
        elif self.scoring_method == 'average':
            return self._calculate_average_score(response)
        elif self.scoring_method == 'weighted_sum':
            return self._calculate_weighted_sum_score(response)
        elif self.scoring_method == 'custom':
            return self._calculate_custom_score(response)
        return 0

    def _calculate_sum_score(self, response):
        """Calculate sum of all answer scores"""
        total = 0
        for answer in response.answers.all():
            if hasattr(answer, 'score') and answer.score is not None:
                total += answer.score
        return min(total, self.max_score)

    def _calculate_average_score(self, response):
        """Calculate average of all answer scores"""
        scores = []
        for answer in response.answers.all():
            if hasattr(answer, 'score') and answer.score is not None:
                scores.append(answer.score)
        if not scores:
            return 0
        return min(sum(scores) / len(scores), self.max_score)

    def _calculate_weighted_sum_score(self, response):
        """Calculate weighted sum of all answer scores"""
        total = 0
        for answer in response.answers.all():
            if hasattr(answer, 'score') and answer.score is not None:
                weight = answer.question.scoring_weight if hasattr(answer.question, 'scoring_weight') else 1
                total += answer.score * weight
        return min(total, self.max_score)

    def _calculate_custom_score(self, response):
        """Calculate score using custom rules"""
        # This would implement custom scoring logic based on the rules JSON
        # For now, default to sum scoring
        return self._calculate_sum_score(response)


class EmailTemplate(models.Model):
    """
    Model for email templates
    """
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('welcome', 'Welcome'),
        ('password_reset', 'Password Reset'),
        ('verification', 'Verification'),
        ('response', 'Response'),
        ('analysis', 'Analysis'),
        ('notification', 'Notification'),
        ('reminder', 'Reminder'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    html_content = models.TextField(blank=True)
    variables = models.JSONField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    organization = models.ForeignKey('groups.Organization', on_delete=models.SET_NULL, null=True, blank=True, related_name='surveys_email_templates')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='surveys_created_email_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
        indexes = [
            models.Index(fields=['category'], name='surveys_emailtemplate_category_idx'),
            models.Index(fields=['is_active'], name='surveys_emailtemplate_is_active_idx'),
            models.Index(fields=['is_default'], name='surveys_emailtemplate_is_default_idx'),
            models.Index(fields=['organization'], name='surveys_emailtemplate_org_idx'),
        ]

    def __str__(self):
        return self.name

    def render(self, context):
        """
        Render the template with the given context
        """
        from django.template import Template, Context

        # Render subject
        subject_template = Template(self.subject)
        rendered_subject = subject_template.render(Context(context))

        # Render message
        message_template = Template(self.message)
        rendered_message = message_template.render(Context(context))

        # Render HTML content if available
        rendered_html = None
        if self.html_content:
            html_template = Template(self.html_content)
            rendered_html = html_template.render(Context(context))

        return {
            'subject': rendered_subject,
            'message': rendered_message,
            'html': rendered_html
        }


class EmailLog(models.Model):
    """
    Model for logging emails sent
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    html_content = models.TextField(blank=True)
    recipient_email = models.EmailField()  # Changed from recipient to recipient_email
    recipient_name = models.CharField(max_length=255, blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='sent')
    error_message = models.TextField(blank=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='surveys_sent_emails')
    # Use the correct model reference
    survey = models.ForeignKey('surveys.Questionnaire', on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    response = models.ForeignKey('feedback.Response', on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
        indexes = [
            models.Index(fields=['recipient_email'], name='surveys_emaillog_recipient_idx'),
            models.Index(fields=['sent_at'], name='surveys_emaillog_sent_at_idx'),
            models.Index(fields=['status'], name='surveys_emaillog_status_idx'),
            models.Index(fields=['template'], name='surveys_emaillog_template_idx'),
        ]

    def __str__(self):
        return f"Email to {self.recipient_email} - {self.subject}"


# Create an alias for Questionnaire to maintain backward compatibility
Survey = Questionnaire


class ScoringSystem(models.Model):
    """
    Model for scoring systems that can be applied to questionnaires
    """
    SCORING_TYPE_CHOICES = [
        ('simple_sum', 'Simple Sum'),
        ('weighted', 'Weighted Scoring'),
        ('range_based', 'Range-Based Scoring'),
        ('custom', 'Custom Formula'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    # Use the correct model reference
    questionnaire = models.ForeignKey('surveys.Questionnaire', on_delete=models.CASCADE, related_name='scoring_systems')
    scoring_type = models.CharField(max_length=20, choices=SCORING_TYPE_CHOICES, default='simple_sum')
    formula = models.TextField(blank=True, help_text="For custom scoring, enter a formula or description of the scoring logic")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_scoring_systems')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['questionnaire', 'name']
        verbose_name = 'Scoring System'
        verbose_name_plural = 'Scoring Systems'
        unique_together = ['questionnaire', 'name']

    def __str__(self):
        return f"{self.name} for {self.questionnaire.title}"

    def calculate_score(self, response):
        """
        Calculate the score for a response based on the scoring system
        """
        from feedback.models import Response, Answer

        if not isinstance(response, Response):
            raise ValueError("Response must be a Response instance")

        if response.survey != self.questionnaire:
            raise ValueError("Response is not for the questionnaire associated with this scoring system")

        # Get all answers for this response
        answers = Answer.objects.filter(response=response)

        if self.scoring_type == 'simple_sum':
            return self._calculate_simple_sum(answers)
        elif self.scoring_type == 'weighted':
            return self._calculate_weighted_score(answers)
        elif self.scoring_type == 'range_based':
            return self._calculate_range_based_score(answers)
        elif self.scoring_type == 'custom':
            return self._calculate_custom_score(answers)
        else:
            raise ValueError(f"Unsupported scoring type: {self.scoring_type}")

    def _calculate_simple_sum(self, answers):
        """
        Calculate a simple sum of all answer values
        """
        total = 0
        for answer in answers:
            # Get the score rule for this question
            try:
                score_rule = ScoreRule.objects.get(
                    scoring_system=self,
                    question=answer.question
                )

                # Get the option score for this answer
                if answer.selected_option:
                    option_score = OptionScore.objects.get(
                        score_rule=score_rule,
                        option=answer.selected_option
                    )
                    total += option_score.score
                elif answer.text_value and score_rule.text_score_enabled:
                    # For text answers, use the text_score if enabled
                    total += score_rule.text_score
            except (ScoreRule.DoesNotExist, OptionScore.DoesNotExist):
                # Skip questions without scoring rules or options without scores
                continue

        return total

    def _calculate_weighted_score(self, answers):
        """
        Calculate a weighted score based on question weights
        """
        total = 0
        for answer in answers:
            try:
                score_rule = ScoreRule.objects.get(
                    scoring_system=self,
                    question=answer.question
                )

                if answer.selected_option:
                    option_score = OptionScore.objects.get(
                        score_rule=score_rule,
                        option=answer.selected_option
                    )
                    total += option_score.score * score_rule.weight
                elif answer.text_value and score_rule.text_score_enabled:
                    total += score_rule.text_score * score_rule.weight
            except (ScoreRule.DoesNotExist, OptionScore.DoesNotExist):
                continue

        return total

    def _calculate_range_based_score(self, answers):
        """
        Calculate a score and determine which range it falls into
        """
        # First calculate the raw score (using weighted scoring)
        raw_score = self._calculate_weighted_score(answers)

        # Find which score range this falls into
        try:
            score_range = ScoreRange.objects.filter(
                scoring_system=self,
                min_score__lte=raw_score,
                max_score__gte=raw_score
            ).first()

            if score_range:
                return {
                    'raw_score': raw_score,
                    'range_name': score_range.name,
                    'range_description': score_range.description,
                    'interpretation': score_range.interpretation
                }
            else:
                return {
                    'raw_score': raw_score,
                    'range_name': 'Unknown',
                    'range_description': 'Score does not fall within any defined range',
                    'interpretation': None
                }
        except Exception as e:
            return {
                'raw_score': raw_score,
                'error': str(e)
            }

    def _calculate_custom_score(self, answers):
        """
        Calculate a custom score based on the formula
        """
        # This would typically call a custom scoring function or evaluate a formula
        # For now, we'll just return a placeholder
        # The answers parameter is used in the actual implementation
        _ = answers  # Acknowledge the parameter to avoid linting warnings
        return {
            'raw_score': 0,
            'note': 'Custom scoring requires implementation specific to the formula'
        }


class ScoreRule(models.Model):
    """
    Model for scoring rules for individual questions
    """
    scoring_system = models.ForeignKey(ScoringSystem, on_delete=models.CASCADE, related_name='score_rules')
    # Use the correct model reference with the actual database model name
    question = models.ForeignKey('surveys.SurveysQuestion', on_delete=models.CASCADE, related_name='score_rules')
    weight = models.FloatField(default=1.0, help_text="Weight to apply to this question's score")
    text_score_enabled = models.BooleanField(default=False, help_text="Enable scoring for text answers")
    text_score = models.FloatField(default=0.0, help_text="Score to apply to text answers if enabled")
    notes = models.TextField(blank=True)

    class Meta:
        # Fix the ordering issue by removing the reference to question__order
        ordering = ['scoring_system', 'id']
        verbose_name = 'Score Rule'
        verbose_name_plural = 'Score Rules'
        unique_together = ['scoring_system', 'question']

    def __str__(self):
        return f"Scoring for {self.question.text} in {self.scoring_system.name}"


class OptionScore(models.Model):
    """
    Model for scores assigned to individual answer options
    """
    score_rule = models.ForeignKey(ScoreRule, on_delete=models.CASCADE, related_name='option_scores')
    # Use the correct model reference with the actual database model name
    option = models.ForeignKey('surveys.SurveysQuestionchoice', on_delete=models.CASCADE, related_name='scores')
    score = models.FloatField(default=0.0)

    class Meta:
        # Fix the ordering issue by removing the reference to option__order
        ordering = ['score_rule', 'id']
        verbose_name = 'Option Score'
        verbose_name_plural = 'Option Scores'
        unique_together = ['score_rule', 'option']

    def __str__(self):
        return f"Score for '{self.option.text}': {self.score}"


class ScoreRange(models.Model):
    """
    Model for defining score ranges and their interpretations
    """
    scoring_system = models.ForeignKey(ScoringSystem, on_delete=models.CASCADE, related_name='score_ranges')
    name = models.CharField(max_length=100)
    min_score = models.FloatField()
    max_score = models.FloatField()
    description = models.TextField(blank=True)
    interpretation = models.TextField(blank=True, help_text="Clinical interpretation or meaning of this score range")
    color = models.CharField(max_length=20, default='gray', help_text="Color code for visual representation (e.g., 'red', 'yellow', 'green')")

    class Meta:
        ordering = ['scoring_system', 'min_score']
        verbose_name = 'Score Range'
        verbose_name_plural = 'Score Ranges'

    def __str__(self):
        return f"{self.name}: {self.min_score} to {self.max_score}"


class ResponseScore(models.Model):
    """
    Model for storing calculated scores for responses
    """
    # Use the correct model reference with the actual database model name
    response = models.ForeignKey('feedback.Response', on_delete=models.CASCADE, related_name='scores')
    scoring_system = models.ForeignKey(ScoringSystem, on_delete=models.CASCADE, related_name='response_scores')
    raw_score = models.FloatField()
    score_range = models.ForeignKey(ScoreRange, on_delete=models.SET_NULL, null=True, blank=True, related_name='responses')
    calculated_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-calculated_at']
        verbose_name = 'Response Score'
        verbose_name_plural = 'Response Scores'
        unique_together = ['response', 'scoring_system']

    def __str__(self):
        return f"Score for {self.response}: {self.raw_score}"


# Create alias for backward compatibility
Survey = Questionnaire

# Import scoring models at the end to avoid circular imports
from surveys.models.scoring import (
    ScoringSystem, ScoreRule, ScoreRange, ResponseScore, OptionScore
)
