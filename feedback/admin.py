from django.contrib import admin
from .models import Response, Answer
from .models.base import AIAnalysis

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('id',)
    fields = ('id', 'question', 'text_answer')
    can_delete = False
    show_change_link = True

class AIAnalysisInline(admin.StackedInline):
    model = AIAnalysis
    extra = 0
    readonly_fields = ('id',)
    fields = ('id', 'summary')
    can_delete = False
    show_change_link = True

class ResponseAdmin(admin.ModelAdmin):
    list_display = ('id',)
    search_fields = ('id',)
    readonly_fields = ('id',)

    fieldsets = (
        ('Response Information', {
            'fields': ('id',)
        }),
    )

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id',)
    search_fields = ('id',)
    readonly_fields = ('id',)
    fieldsets = (
        ('Answer Information', {
            'fields': ('id', 'response', 'question')
        }),
        ('Answer Values', {
            'fields': ('text_answer',)
        }),
    )

class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id',)
    search_fields = ('id',)
    readonly_fields = ('id',)
    fieldsets = (
        ('Analysis Information', {
            'fields': ('id', 'response')
        }),
        ('Analysis Content', {
            'fields': ('summary',)
        }),
    )

admin.site.register(Response, ResponseAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(AIAnalysis, AIAnalysisAdmin)
