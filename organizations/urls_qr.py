from django.urls import path
import organizations.views.qr_views as qr_views

urlpatterns = [
    path('<int:org_id>/qr-codes/', qr_views.organization_qr_codes, name='organization_qr_codes'),
    path('<int:org_id>/questionnaires/<uuid:questionnaire_id>/generate-qr-code/', qr_views.generate_organization_qr_code, name='generate_organization_qr_code'),
    path('<int:org_id>/qr-codes/<int:qr_code_id>/', qr_views.view_qr_code, name='view_qr_code'),
    path('<int:org_id>/qr-codes/<int:qr_code_id>/download/', qr_views.download_qr_code, name='download_qr_code'),
    path('<int:org_id>/qr-codes/<int:qr_code_id>/delete/', qr_views.delete_qr_code, name='delete_qr_code'),
]
