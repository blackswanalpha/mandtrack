from django.urls import path
from . import views_schedule

urlpatterns = [
    path('organization/<int:org_pk>/schedule-dashboard/', views_schedule.schedule_dashboard, name='schedule_dashboard'),
    path('organization/<int:org_pk>/create-high-risk-schedule/', views_schedule.create_high_risk_schedule, name='create_high_risk_schedule'),
    path('organization/<int:org_pk>/create-member-reports-schedule/', views_schedule.create_member_reports_schedule, name='create_member_reports_schedule'),
    path('schedule/<uuid:schedule_id>/toggle/', views_schedule.toggle_schedule, name='toggle_schedule'),
    path('schedule/<uuid:schedule_id>/delete/', views_schedule.delete_schedule, name='delete_schedule'),
]
