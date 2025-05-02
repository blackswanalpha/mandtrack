from django.urls import path
from analytics.views import enhanced_dashboard_views

urlpatterns = [
    path('dashboards/questionnaire/<uuid:questionnaire_id>/', enhanced_dashboard_views.questionnaire_dashboard, name='questionnaire_dashboard'),
    path('dashboards/user/', enhanced_dashboard_views.user_dashboard, name='user_dashboard'),
    path('dashboards/user/<int:user_id>/', enhanced_dashboard_views.user_dashboard, name='user_dashboard_detail'),
    path('dashboards/organization/<int:organization_id>/', enhanced_dashboard_views.organization_dashboard, name='organization_dashboard'),
    path('dashboards/export/<uuid:questionnaire_id>/', enhanced_dashboard_views.export_dashboard, name='export_dashboard'),
]
