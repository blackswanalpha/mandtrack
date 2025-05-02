from django.urls import path
from analytics.views import pdf_views

urlpatterns = [
    path('reports/<int:report_id>/download-pdf/', pdf_views.download_report_pdf, name='download_report_pdf'),
    path('dashboards/<uuid:questionnaire_id>/download-pdf/', pdf_views.download_dashboard_pdf, name='download_dashboard_pdf'),
    path('comparative/download-pdf/', pdf_views.download_comparative_pdf, name='download_comparative_pdf'),
]
