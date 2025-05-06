"""
URL patterns for the email system app.
"""
from django.urls import path
from . import views

app_name = 'email_system'

urlpatterns = [
    # Email templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/', views.template_detail, name='template_detail'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
    path('templates/<int:pk>/preview/', views.template_preview, name='template_preview'),

    # Email sending
    path('send/', views.send_email, name='send_email'),

    # Email logs
    path('logs/', views.email_log_list, name='email_log_list'),
    path('logs/<int:pk>/', views.email_log_detail, name='email_log_detail'),
    path('logs/<int:pk>/resend/', views.resend_email, name='resend_email'),

    # Scheduled emails
    path('scheduled/', views.scheduled_email_list, name='scheduled_email_list'),
    path('scheduled/create/', views.scheduled_email_create, name='scheduled_email_create'),
    path('scheduled/<int:pk>/', views.scheduled_email_detail, name='scheduled_email_detail'),
    path('scheduled/<int:pk>/edit/', views.scheduled_email_edit, name='scheduled_email_edit'),
    path('scheduled/<int:pk>/delete/', views.scheduled_email_delete, name='scheduled_email_delete'),
    path('scheduled/<int:pk>/cancel/', views.scheduled_email_cancel, name='scheduled_email_cancel'),
]
