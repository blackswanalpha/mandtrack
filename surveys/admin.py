from django.contrib import admin
from django.apps import apps
from django.db.models.fields.related import ForeignKey

# Monkey patch the _get_foreign_key function to handle string references
from django.forms.models import _get_foreign_key as original_get_foreign_key

def patched_get_foreign_key(parent_model, model, fk_name=None, can_fail=False):
    """
    Patched version of _get_foreign_key that handles string references
    """
    try:
        return original_get_foreign_key(parent_model, model, fk_name, can_fail)
    except AttributeError:
        # If we get an AttributeError, it might be because the model is a string reference
        if isinstance(model, str):
            # Try to resolve the string reference
            try:
                app_label, model_name = model.split('.')
                resolved_model = apps.get_model(app_label, model_name)
                return original_get_foreign_key(parent_model, resolved_model, fk_name, can_fail)
            except Exception:
                if can_fail:
                    return None
                raise
        raise

# Apply the monkey patch
from django.forms import models
models._get_foreign_key = patched_get_foreign_key

# Get models from the app registry
try:
    # Import models directly to avoid circular imports
    from django.apps import apps

    # Get models from the app registry using the model classes
    from surveys.models import Questionnaire, Question, QuestionChoice, QRCode, ScoringConfig
    EmailTemplate = apps.get_model('surveys', 'EmailTemplate')
    EmailLog = apps.get_model('surveys', 'EmailLog')
    EmailSchedule = apps.get_model('surveys', 'EmailSchedule')
    ScoringSystem = apps.get_model('surveys', 'ScoringSystem')
    ScoreRule = apps.get_model('surveys', 'ScoreRule')
    ScoreRange = apps.get_model('surveys', 'ScoreRange')
    ResponseScore = apps.get_model('surveys', 'ResponseScore')
    OptionScore = apps.get_model('surveys', 'OptionScore')

    # Define admin classes with minimal configurations to avoid errors
    class QuestionAdmin(admin.ModelAdmin):
        list_display = ('id',)
        search_fields = ('id',)
        readonly_fields = ('id',)
        fieldsets = (
            (None, {'fields': ('id',)}),
        )

    class QuestionnaireAdmin(admin.ModelAdmin):
        list_display = ('id',)
        search_fields = ('id',)
        readonly_fields = ('id',)
        fieldsets = (
            (None, {'fields': ('id',)}),
        )

    class QRCodeAdmin(admin.ModelAdmin):
        list_display = ('id',)
        search_fields = ('id',)
        readonly_fields = ('id',)
        fieldsets = (
            (None, {'fields': ('id',)}),
        )

    class ScoringConfigAdmin(admin.ModelAdmin):
        list_display = ('id',)
        search_fields = ('id',)
        readonly_fields = ('id',)
        fieldsets = (
            (None, {'fields': ('id',)}),
        )

    class EmailTemplateAdmin(admin.ModelAdmin):
        list_display = ('id',)
        search_fields = ('id',)
        readonly_fields = ('id',)
        fieldsets = (
            (None, {'fields': ('id',)}),
        )

    class EmailLogAdmin(admin.ModelAdmin):
        list_display = ('id',)
        readonly_fields = ('id',)
        fieldsets = (
            (None, {'fields': ('id',)}),
        )

    # Register admin classes
    admin.site.register(Questionnaire, QuestionnaireAdmin)
    admin.site.register(Question, QuestionAdmin)
    admin.site.register(QRCode, QRCodeAdmin)
    admin.site.register(ScoringConfig, ScoringConfigAdmin)
    admin.site.register(EmailTemplate, EmailTemplateAdmin)
    admin.site.register(EmailLog, EmailLogAdmin)

except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Error registering admin classes: {e}")
