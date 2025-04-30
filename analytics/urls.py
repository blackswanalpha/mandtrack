from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('test/', views.test_dashboard, name='test_dashboard'),
    path('surveys/', views.survey_analytics, name='survey_analytics'),
    path('responses/', views.response_analytics, name='response_analytics'),
    path('users/', views.user_analytics, name='user_analytics'),
    path('organizations/', views.organization_analytics, name='organization_analytics'),
    path('ai-analysis/', views.ai_analysis, name='ai_analysis'),
    path('ai-analysis/<int:response_pk>/', views.response_ai_analysis, name='response_ai_analysis'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
]
