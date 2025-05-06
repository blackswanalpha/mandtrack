from django.urls import path
from . import views
from . import api

app_name = 'dashboard'

urlpatterns = [
    path('', views.user_dashboard, name='user_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('search/', views.search, name='search'),

    # API Endpoints
    path('api/data/', api.dashboard_data, name='api_dashboard_data'),
    path('api/scoring/systems/', api.scoring_systems_data, name='api_scoring_systems'),
    path('api/scoring/systems/<int:system_id>/', api.scoring_system_detail, name='api_scoring_system_detail'),
    path('api/scoring/questionnaire/<uuid:questionnaire_id>/scores/', api.questionnaire_scores, name='api_questionnaire_scores'),
    path('api/scoring/calculate/', api.calculate_score, name='api_calculate_score'),
    path('api/scoring/batch-calculate/', api.batch_calculate_scores, name='api_batch_calculate_scores'),
    path('api/scoring/systems/<int:system_id>/calculate-all/', api.calculate_all_scores, name='api_calculate_all_scores'),
    path('api/scoring/systems/<int:system_id>/export/csv/', api.export_scores_csv, name='api_export_scores_csv'),
    path('api/scoring/systems/<int:system_id>/export/excel/', api.export_scores_excel, name='api_export_scores_excel'),
    path('api/scoring/systems/<int:system_id>/export/pdf/', api.export_scores_pdf, name='api_export_scores_pdf'),

    # Notification URLs
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # Admin Portal Pages
    path('users/', views.user_management, name='user_management'),
    path('scoring/', views.scoring_management, name='scoring_management'),
    path('scoring/<int:system_id>/', views.scoring_detail, name='scoring_detail'),
    path('scoring/create/', views.scoring_create, name='scoring_create'),
]
