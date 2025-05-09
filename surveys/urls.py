from django.urls import path, include
from django.views.generic import RedirectView
from . import views_new as views
from . import qr_views
from . import qr_download
from .views.email_tracking import track_email_open, track_email_click
from .views.email_analytics import email_analytics_dashboard, email_template_analytics
from .views.selector_views import selector_data_view

app_name = 'surveys'

urlpatterns = [
    # Email Template URLs - moved to the top to avoid conflicts with survey_respond
    path('email-templates/', views.email_template_list, name='email_template_list'),
    path('email-templates/create/', views.email_template_create, name='email_template_create'),
    path('email-templates/<uuid:pk>/', views.email_template_detail, name='email_template_detail'),
    path('email-templates/<uuid:pk>/edit/', views.email_template_edit, name='email_template_edit'),
    path('email-templates/<uuid:pk>/delete/', views.email_template_delete, name='email_template_delete'),

    # Questionnaire URLs
    path('', views.survey_list, name='survey_list'),
    path('create/', views.survey_create, name='survey_create'),
    path('templates/', views.survey_templates, name='survey_templates'),
    path('archive/', views.survey_archive_list, name='survey_archive_list'),
    # Use string path converter to accept any format of primary key
    path('<str:pk>/', views.survey_detail, name='survey_detail'),
    path('<str:pk>/preview/', views.survey_preview, name='survey_preview'),
    path('<str:pk>/edit/', views.survey_edit, name='survey_edit'),
    path('<str:pk>/delete/', views.survey_delete, name='survey_delete'),
    path('<str:pk>/archive/', views.survey_archive, name='survey_archive'),
    path('<str:pk>/restore/', views.survey_restore, name='survey_restore'),
    path('<str:pk>/respond/', views.survey_respond, name='survey_respond'),

    # Question URLs
    path('<str:pk>/questions/', views.question_list, name='question_list'),
    path('<str:survey_pk>/questions/create/', views.question_create, name='question_create'),
    path('<str:survey_pk>/questions/create/country/', views.country_question_create, name='country_question_create'),
    path('<str:survey_pk>/questions/<int:pk>/', views.question_detail, name='question_detail'),
    path('<str:survey_pk>/questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('<str:survey_pk>/questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
    path('<str:survey_pk>/questions/reorder/', views.question_reorder, name='question_reorder'),

    # QR Code URLs - Order matters! Put more specific patterns first
    path('qr-codes/', qr_views.qr_code_list_redirect, name='qr_code_list_redirect'),
    path('qr-codes/list/', qr_views.qr_code_list, name='qr_code_list'),
    path('qr-codes/create/', qr_views.qr_code_create, name='qr_code_create'),
    path('qr-codes/<int:pk>/', qr_views.qr_code_detail, name='qr_code_detail'),
    path('<str:pk>/qr-code/', views.generate_qr_code, name='generate_qr_code'),
    path('<str:pk>/qr-code/download/', qr_download.download_qr_code, name='download_qr_code'),
    path('<str:pk>/generate-qr-code/', qr_views.generate_survey_qr_code, name='generate_survey_qr_code'),

    # Scoring Config URLs
    path('<str:questionnaire_pk>/scoring/', views.scoring_config_list, name='scoring_config_list'),
    path('<str:questionnaire_pk>/scoring/create/', views.scoring_config_create, name='scoring_config_create'),
    path('<str:questionnaire_pk>/scoring/<str:pk>/', views.scoring_config_detail, name='scoring_config_detail'),
    path('<str:questionnaire_pk>/scoring/<str:pk>/edit/', views.scoring_config_edit, name='scoring_config_edit'),
    path('<str:questionnaire_pk>/scoring/<str:pk>/delete/', views.scoring_config_delete, name='scoring_config_delete'),

    # Template Questionnaires (moved to the top of the file)

    # Include Scoring URLs
    path('', include('surveys.urls_scoring')),

    # Include Enhanced Scoring URLs
    path('', include('surveys.urls_enhanced_scoring', namespace='enhanced_scoring')),

    # Email Tracking URLs
    path('emails/track/open/<str:tracking_id>/', track_email_open, name='track_email_open'),
    path('emails/track/click/<str:tracking_id>/', track_email_click, name='track_email_click'),

    # Email Analytics URLs
    path('email-analytics/', email_analytics_dashboard, name='email_analytics_dashboard'),
    path('email-analytics/template/<uuid:template_id>/', email_template_analytics, name='email_template_analytics'),

    # Selector Data URL
    path('selector-data/', selector_data_view, name='selector_data'),

    # Email Schedule URLs - temporarily commented out
    # path('email-schedules/', views.email_schedule_list, name='email_schedule_list'),
    # path('email-schedules/create/', views.email_schedule_create, name='email_schedule_create'),
    # path('email-schedules/<uuid:pk>/', views.email_schedule_detail, name='email_schedule_detail'),
    # path('email-schedules/<uuid:pk>/edit/', views.email_schedule_edit, name='email_schedule_edit'),
    # path('email-schedules/<uuid:pk>/cancel/', views.email_schedule_cancel, name='email_schedule_cancel'),
]
