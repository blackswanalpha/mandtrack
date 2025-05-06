from django.urls import path
from analytics.views import comparative_views
from analytics.views_comparative import compare_members, organization_overview

urlpatterns = [
    path('comparative/time-period/<uuid:questionnaire_id>/', comparative_views.time_period_comparison, name='time_period_comparison'),
    path('comparative/demographic/<uuid:questionnaire_id>/', comparative_views.demographic_comparison, name='demographic_comparison'),
    path('comparative/questionnaires/', comparative_views.questionnaire_comparison, name='questionnaire_comparison'),

    # New comparative analytics URLs
    path('comparative/members/<int:org_pk>/', compare_members, name='compare_members'),
    path('comparative/organization/<int:org_pk>/', organization_overview, name='organization_overview'),
]
