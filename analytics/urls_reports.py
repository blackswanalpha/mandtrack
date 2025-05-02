from django.urls import path
from analytics.views import report_views

urlpatterns = [
    # Report Dashboard
    path('reports/', report_views.report_dashboard, name='report_dashboard'),
    path('reports/list/', report_views.report_list, name='report_list'),
    path('reports/<int:pk>/', report_views.report_detail, name='report_detail'),
    path('reports/<int:pk>/delete/', report_views.report_delete, name='report_delete'),
    
    # Report Generation
    path('reports/response-summary/', report_views.report_response_summary, name='report_response_summary'),
    path('reports/trend-analysis/', report_views.report_trend_analysis, name='report_trend_analysis'),
    path('reports/ai-insights/', report_views.report_ai_insights, name='report_ai_insights'),
    path('reports/demographic-analysis/', report_views.report_demographic_analysis, name='report_demographic_analysis'),
    path('reports/risk-assessment/', report_views.report_risk_assessment, name='report_risk_assessment'),
    path('reports/custom-export/', report_views.report_custom_export, name='report_custom_export'),
    
    # Report Schedules
    path('report-schedules/', report_views.report_schedule_list, name='report_schedule_list'),
    path('report-schedules/create/', report_views.report_schedule_create, name='report_schedule_create'),
    path('report-schedules/<int:pk>/edit/', report_views.report_schedule_edit, name='report_schedule_edit'),
    path('report-schedules/<int:pk>/delete/', report_views.report_schedule_delete, name='report_schedule_delete'),
]
