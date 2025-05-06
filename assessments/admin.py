from django.contrib import admin
from .models import Assessment, Consultation

class ConsultationInline(admin.TabularInline):
    model = Consultation
    extra = 0
    fields = ('consultant', 'scheduled_date', 'status', 'follow_up_required')
    readonly_fields = ('created_at',)

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_patient_identifier', 'get_risk_level', 'status', 'consultation_recommended', 'assessment_date')
    list_filter = ('status', 'consultation_recommended', 'assessment_date')
    search_fields = ('response__patient_identifier', 'response__patient_email', 'notes', 'concerns')
    readonly_fields = ('id', 'assessment_date', 'updated_at')
    inlines = [ConsultationInline]
    fieldsets = (
        ('Assessment Information', {
            'fields': ('id', 'response', 'assessor', 'status', 'assessment_date', 'updated_at')
        }),
        ('Assessment Details', {
            'fields': ('notes', 'risk_factors', 'strengths', 'concerns')
        }),
        ('Consultation', {
            'fields': ('consultation_recommended', 'consultation_notes', 'consultation_urgency')
        }),
        ('Follow-up', {
            'fields': ('follow_up_date', 'follow_up_notes')
        }),
    )

    def get_patient_identifier(self, obj):
        return obj.response.patient_identifier or 'Anonymous'
    get_patient_identifier.short_description = 'Patient'

    def get_risk_level(self, obj):
        return obj.get_risk_level()
    get_risk_level.short_description = 'Risk Level'

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_patient_identifier', 'consultant', 'scheduled_date', 'status', 'follow_up_required')
    list_filter = ('status', 'scheduled_date', 'follow_up_required')
    search_fields = ('assessment__response__patient_identifier', 'assessment__response__patient_email', 'notes', 'outcome')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Consultation Information', {
            'fields': ('id', 'assessment', 'consultant', 'scheduled_date', 'status')
        }),
        ('Consultation Details', {
            'fields': ('notes', 'outcome', 'follow_up_required')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_patient_identifier(self, obj):
        return obj.assessment.response.patient_identifier or 'Anonymous'
    get_patient_identifier.short_description = 'Patient'
