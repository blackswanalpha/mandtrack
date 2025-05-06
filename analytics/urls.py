from django.urls import path, include
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

    # Include AI Analysis URLs
    path('', include('analytics.urls_ai')),

    # Include Reports URLs
    path('', include('analytics.urls_reports')),

    # Include Gemini AI Analysis URLs
    path('', include('analytics.urls_gemini')),

    # Include Batch Analysis URLs
    path('', include('analytics.urls_batch')),

    # Include Enhanced Dashboard URLs
    path('', include('analytics.urls_dashboard')),

    # Include Enhanced AI Analysis URLs
    path('', include('analytics.urls_enhanced_ai')),

    # Include PDF URLs
    path('', include('analytics.urls_pdf')),

    # Include Comparative Analytics URLs
    path('', include('analytics.urls_comparative')),

    # Include Email Reports URLs
    path('', include('analytics.urls_email')),

    # Include Advanced AI Analysis URLs
    path('', include('analytics.urls_advanced_ai')),

    # Include Advanced Visualization URLs
    path('', include('analytics.urls_advanced_viz')),

    # Include Trend Analysis URLs
    path('', include('analytics.urls_trend')),
]
