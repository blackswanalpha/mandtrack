from django.urls import path
from . import views_email

urlpatterns = [
    path('organization/<int:org_pk>/email-dashboard/', views_email.email_dashboard, name='email_dashboard'),
    path('organization/<int:org_pk>/send-high-risk-notifications/', views_email.send_high_risk_notifications, name='send_high_risk_notifications'),
    path('organization/<int:org_pk>/send-member-reports/', views_email.send_member_reports, name='send_member_reports'),
]
