from django.urls import path
from . import views_new as views
from . import qr_views

app_name = 'surveys'

urlpatterns = [
    # Questionnaire URLs
    path('', views.survey_list, name='survey_list'),
    path('create/', views.survey_create, name='survey_create'),
    path('<uuid:pk>/', views.survey_detail, name='survey_detail'),
    path('<uuid:pk>/preview/', views.survey_preview, name='survey_preview'),
    path('<uuid:pk>/edit/', views.survey_edit, name='survey_edit'),
    path('<uuid:pk>/delete/', views.survey_delete, name='survey_delete'),
    path('<uuid:pk>/archive/', views.survey_archive, name='survey_archive'),
    path('<uuid:pk>/restore/', views.survey_restore, name='survey_restore'),
    path('archive/', views.survey_archive_list, name='survey_archive_list'),
    path('<uuid:pk>/respond/', views.survey_respond, name='survey_respond'),
    path('<slug:slug>/', views.survey_respond, name='survey_respond_slug'),

    # Question URLs
    path('<uuid:pk>/questions/', views.question_list, name='question_list'),
    path('<uuid:survey_pk>/questions/create/', views.question_create, name='question_create'),
    path('<uuid:survey_pk>/questions/<int:pk>/', views.question_detail, name='question_detail'),
    path('<uuid:survey_pk>/questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('<uuid:survey_pk>/questions/<int:pk>/delete/', views.question_delete, name='question_delete'),

    # QR Code URLs
    path('<uuid:pk>/qr-code/', views.generate_qr_code, name='generate_qr_code'),
    path('qr-codes/', qr_views.qr_code_list, name='qr_code_list'),
    path('qr-codes/create/', qr_views.qr_code_create, name='qr_code_create'),
    path('qr-codes/<uuid:pk>/', qr_views.qr_code_detail, name='qr_code_detail'),
    path('<uuid:pk>/generate-qr-code/', qr_views.generate_survey_qr_code, name='generate_survey_qr_code'),

    # Scoring Config URLs
    path('<uuid:questionnaire_pk>/scoring/', views.scoring_config_list, name='scoring_config_list'),
    path('<uuid:questionnaire_pk>/scoring/create/', views.scoring_config_create, name='scoring_config_create'),
    path('<uuid:questionnaire_pk>/scoring/<uuid:pk>/', views.scoring_config_detail, name='scoring_config_detail'),
    path('<uuid:questionnaire_pk>/scoring/<uuid:pk>/edit/', views.scoring_config_edit, name='scoring_config_edit'),
    path('<uuid:questionnaire_pk>/scoring/<uuid:pk>/delete/', views.scoring_config_delete, name='scoring_config_delete'),

    # Email Template URLs
    path('email-templates/', views.email_template_list, name='email_template_list'),
    path('email-templates/create/', views.email_template_create, name='email_template_create'),
    path('email-templates/<uuid:pk>/', views.email_template_detail, name='email_template_detail'),
    path('email-templates/<uuid:pk>/edit/', views.email_template_edit, name='email_template_edit'),
    path('email-templates/<uuid:pk>/delete/', views.email_template_delete, name='email_template_delete'),
]
