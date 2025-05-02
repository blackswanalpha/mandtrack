from django.contrib import admin
from .models import Questionnaire, Question, QuestionChoice, QRCode, ScoringConfig, EmailTemplate, EmailLog

class QuestionChoiceInline(admin.TabularInline):
    model = QuestionChoice
    extra = 2

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'survey', 'question_type', 'required', 'order', 'is_scored', 'is_visible')
    list_filter = ('survey', 'question_type', 'required', 'is_scored', 'is_visible')
    search_fields = ('text', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [QuestionChoiceInline]
    fieldsets = (
        (None, {'fields': ('id', 'survey', 'text', 'description')}),
        ('Configuration', {'fields': ('question_type', 'required', 'order', 'is_visible')}),
        ('Scoring', {'fields': ('is_scored', 'scoring_weight', 'max_score')}),
        ('Advanced', {'fields': ('options', 'conditional_logic', 'validation_rules', 'category')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True
    fields = ('text', 'question_type', 'required', 'order', 'is_scored')

class ScoringConfigInline(admin.TabularInline):
    model = ScoringConfig
    extra = 1
    show_change_link = True
    fields = ('name', 'scoring_method', 'max_score', 'passing_score', 'is_active', 'is_default')

class QRCodeInline(admin.TabularInline):
    model = QRCode
    extra = 0
    show_change_link = True
    fields = ('name', 'url', 'access_count', 'is_active', 'expires_at')
    readonly_fields = ('access_count',)
    fk_name = 'survey'

class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'category', 'status', 'is_active', 'is_public', 'created_by', 'created_at', 'get_question_count')
    list_filter = ('type', 'category', 'status', 'is_active', 'is_public', 'is_template', 'created_at')
    search_fields = ('title', 'description', 'instructions')
    readonly_fields = ('id', 'slug', 'qr_code', 'access_code', 'created_at', 'updated_at')
    inlines = [QuestionInline, ScoringConfigInline, QRCodeInline]
    fieldsets = (
        (None, {'fields': ('id', 'title', 'slug', 'description', 'instructions')}),
        ('Classification', {'fields': ('type', 'category', 'tags', 'language')}),
        ('Configuration', {'fields': ('status', 'is_active', 'is_template', 'is_public', 'version', 'parent')}),
        ('Access Control', {'fields': ('requires_auth', 'allow_anonymous', 'max_responses', 'expires_at')}),
        ('Features', {'fields': ('is_adaptive', 'is_qr_enabled', 'estimated_time', 'time_limit')}),
        ('QR Code', {'fields': ('qr_code', 'access_code')}),
        ('Ownership', {'fields': ('created_by', 'organization')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def get_question_count(self, obj):
        return obj.get_question_count()
    get_question_count.short_description = 'Questions'

class QRCodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'survey', 'url', 'access_count', 'is_active', 'expires_at', 'created_by')
    list_filter = ('is_active', 'created_at', 'expires_at')
    search_fields = ('name', 'description', 'url')
    readonly_fields = ('id', 'image', 'access_count', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('id', 'survey', 'name', 'description')}),
        ('QR Code', {'fields': ('url', 'image', 'access_count')}),
        ('Configuration', {'fields': ('is_active', 'expires_at')}),
        ('Ownership', {'fields': ('created_by',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

class ScoringConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'survey', 'scoring_method', 'max_score', 'passing_score', 'is_active', 'is_default')
    list_filter = ('scoring_method', 'is_active', 'is_default', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('id', 'survey', 'name', 'description')}),
        ('Scoring', {'fields': ('scoring_method', 'max_score', 'passing_score', 'rules')}),
        ('Configuration', {'fields': ('is_active', 'is_default')}),
        ('Ownership', {'fields': ('created_by',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'subject', 'is_active', 'is_default', 'organization', 'created_by')
    list_filter = ('category', 'is_active', 'is_default', 'created_at', 'organization')
    search_fields = ('name', 'description', 'subject', 'message')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('id', 'name', 'description', 'category')}),
        ('Content', {'fields': ('subject', 'message', 'html_content', 'variables')}),
        ('Configuration', {'fields': ('is_active', 'is_default', 'organization')}),
        ('Ownership', {'fields': ('created_by',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'subject', 'sent_at', 'status', 'template', 'sent_by')
    list_filter = ('status', 'sent_at', 'template__category')
    search_fields = ('recipient', 'recipient_name', 'subject', 'message')
    readonly_fields = ('id', 'sent_at', 'template', 'subject', 'message', 'html_content', 'recipient', 'recipient_name', 'status', 'error_message', 'sent_by', 'survey', 'response')
    fieldsets = (
        (None, {'fields': ('id', 'template', 'subject')}),
        ('Recipient', {'fields': ('recipient', 'recipient_name')}),
        ('Content', {'fields': ('message', 'html_content')}),
        ('Status', {'fields': ('status', 'error_message', 'sent_at')}),
        ('Related', {'fields': ('sent_by', 'survey', 'response')}),
        ('Metadata', {'fields': ('metadata',)}),
    )

admin.site.register(Questionnaire, QuestionnaireAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QRCode, QRCodeAdmin)
admin.site.register(ScoringConfig, ScoringConfigAdmin)
admin.site.register(EmailTemplate, EmailTemplateAdmin)
admin.site.register(EmailLog, EmailLogAdmin)
