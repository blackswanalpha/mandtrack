from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    # Member access and questionnaire response
    path('access/', views.member_access_form, name='member_access_form'),
    path('access/qr/<uuid:qr_code_id>/', views.qr_member_access, name='qr_member_access'),
    path('questionnaire/', views.questionnaire_response, name='questionnaire_response'),
    path('complete/', views.response_complete, name='response_complete'),

    # Analytics and reports
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('reports/', views.reports, name='reports'),
    path('risk-assessment/', views.risk_assessment, name='risk_assessment'),
    path('analysis/', views.analysis, name='analysis'),

    # Detailed views
    path('response/<int:pk>/', views.response_detail, name='response_detail'),

    # Comparative reports
    path('progress-report/', views.progress_report, name='progress_report'),
    path('trend-analysis/', views.trend_analysis, name='trend_analysis'),
    path('ai-insights/', views.ai_insights, name='ai_insights'),

    # Downloads
    path('download/report/<int:pk>/', views.download_report, name='download_report'),
    path('download/analysis/<int:pk>/', views.download_analysis, name='download_analysis'),
    path('download/risk-report/', views.download_risk_report, name='download_risk_report'),
]
