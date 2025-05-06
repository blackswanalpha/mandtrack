from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    # Patient Portal
    path('patient-portal/', views.patient_portal, name='patient_portal'),
    path('patient-progress/', views.patient_progress, name='patient_progress'),
    # Assessment URLs
    path('', views.assessment_dashboard, name='dashboard'),
    path('list/', views.assessment_list, name='assessment_list'),
    path('<uuid:pk>/', views.assessment_detail, name='assessment_detail'),
    path('create/', views.assessment_create, name='assessment_create'),
    path('create/<uuid:response_id>/', views.assessment_create, name='assessment_create_from_response'),
    path('<uuid:pk>/update/', views.assessment_update, name='assessment_update'),
    path('<uuid:assessment_id>/flag-consultation/', views.flag_for_consultation, name='flag_for_consultation'),
    path('<uuid:pk>/export-pdf/', views.export_assessment_pdf, name='export_assessment_pdf'),

    # Consultation URLs
    path('<uuid:assessment_id>/consultation/create/', views.consultation_create, name='consultation_create'),
    path('consultation/<uuid:pk>/update/', views.consultation_update, name='consultation_update'),
    path('consultation/calendar/', views.consultation_calendar, name='consultation_calendar'),
    path('consultation/events/', views.consultation_events, name='consultation_events'),
    path('consultation/<uuid:pk>/details/', views.consultation_details, name='consultation_details'),
    path('consultation/create-ajax/', views.consultation_create_ajax, name='consultation_create_ajax'),
]
