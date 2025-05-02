from django.urls import path
from analytics.views import email_views

urlpatterns = [
    path('reports/<int:report_id>/email/', email_views.email_report_form, name='email_report_form'),
    path('reports/<int:report_id>/email/send/', email_views.send_report_email, name='send_report_email'),
    path('questionnaires/<uuid:questionnaire_id>/email-batch/', email_views.email_batch_form, name='email_batch_form'),
    path('questionnaires/<uuid:questionnaire_id>/email-batch/send/', email_views.send_batch_email, name='send_batch_email'),
    path('reports/<int:report_id>/schedule/', email_views.schedule_report_form, name='schedule_report_form_by_report'),
    path('questionnaires/<uuid:questionnaire_id>/schedule/', email_views.schedule_report_form, name='schedule_report_form_by_questionnaire'),
    path('scheduled-reports/create/', email_views.create_scheduled_report, name='create_scheduled_report'),
    path('scheduled-reports/', email_views.scheduled_reports_list, name='scheduled_reports_list'),
    path('scheduled-reports/<uuid:report_id>/toggle/', email_views.toggle_scheduled_report, name='toggle_scheduled_report'),
    path('scheduled-reports/<uuid:report_id>/delete/', email_views.delete_scheduled_report, name='delete_scheduled_report'),
]
