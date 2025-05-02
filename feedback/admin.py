from django.contrib import admin
from .models import Response, Answer
from .models.base import AIAnalysis

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('id', 'question', 'get_answer_display', 'score', 'created_at', 'updated_at')
    fields = ('id', 'question', 'get_answer_display', 'score')
    can_delete = False
    show_change_link = True

    def get_answer_display(self, obj):
        return obj.get_answer_display()
    get_answer_display.short_description = 'Answer'

class AIAnalysisInline(admin.StackedInline):
    model = AIAnalysis
    extra = 0
    readonly_fields = ('id', 'created_by', 'created_at', 'updated_at')
    fields = ('id', 'summary', 'recommendations', 'confidence_score', 'model_used', 'created_by', 'created_at')
    can_delete = False
    show_change_link = True

class ResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'survey', 'patient_name', 'patient_email', 'status', 'created_at', 'completed_at', 'risk_level', 'score', 'flagged_for_review')
    list_filter = ('survey', 'status', 'risk_level', 'flagged_for_review', 'created_at', 'organization')
    search_fields = ('patient_name', 'patient_email', 'patient_identifier', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'ip_address', 'user_agent')
    inlines = [AnswerInline, AIAnalysisInline]
    actions = ['mark_as_completed', 'flag_for_review', 'unflag_for_review']

    fieldsets = (
        ('Response Information', {
            'fields': ('id', 'survey', 'status', 'created_at', 'completed_at', 'completion_time')
        }),
        ('Patient Information', {
            'fields': ('user', 'patient_identifier', 'patient_name', 'patient_email', 'patient_age', 'patient_gender')
        }),
        ('Analysis', {
            'fields': ('score', 'risk_level', 'flagged_for_review', 'notes')
        }),
        ('Metadata', {
            'fields': ('organization', 'ip_address', 'user_agent', 'metadata')
        }),
    )

    def mark_as_completed(self, request, queryset):
        for response in queryset:
            response.mark_as_completed()
        self.message_user(request, f"{queryset.count()} responses marked as completed.")
    mark_as_completed.short_description = "Mark selected responses as completed"

    def flag_for_review(self, request, queryset):
        for response in queryset:
            response.flag_for_review(True)
        self.message_user(request, f"{queryset.count()} responses flagged for review.")
    flag_for_review.short_description = "Flag selected responses for review"

    def unflag_for_review(self, request, queryset):
        for response in queryset:
            response.flag_for_review(False)
        self.message_user(request, f"{queryset.count()} responses unflagged.")
    unflag_for_review.short_description = "Remove review flag from selected responses"

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'response', 'get_answer_display', 'score')
    list_filter = ('question__survey', 'question__question_type', 'created_at')
    search_fields = ('text_answer', 'question__text', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Answer Information', {
            'fields': ('id', 'response', 'question', 'score')
        }),
        ('Answer Values', {
            'fields': ('text_answer', 'selected_choice', 'numeric_value', 'date_value', 'time_value', 'file_upload')
        }),
        ('Multiple Choices', {
            'fields': ('multiple_choices',)
        }),
        ('Advanced', {
            'fields': ('value', 'created_at', 'updated_at')
        }),
    )

    def get_answer_display(self, obj):
        return obj.get_answer_display()
    get_answer_display.short_description = 'Answer'

class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'response', 'model_used', 'confidence_score', 'created_by', 'created_at')
    list_filter = ('model_used', 'created_at', 'created_by')
    search_fields = ('summary', 'detailed_analysis', 'recommendations', 'id')
    readonly_fields = ('id', 'response', 'created_at', 'updated_at')
    fieldsets = (
        ('Analysis Information', {
            'fields': ('id', 'response', 'model_used', 'confidence_score')
        }),
        ('Analysis Content', {
            'fields': ('summary', 'detailed_analysis', 'recommendations')
        }),
        ('Advanced', {
            'fields': ('insights', 'raw_data', 'created_by', 'created_at', 'updated_at')
        }),
    )

admin.site.register(Response, ResponseAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(AIAnalysis, AIAnalysisAdmin)
