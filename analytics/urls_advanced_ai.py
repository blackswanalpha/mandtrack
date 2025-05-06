from django.urls import path
from analytics.views import analyze_response, analyze_member_responses

urlpatterns = [
    path('analyze-response/<uuid:response_id>/', analyze_response, name='analyze_response'),
    path('analyze-member/<int:org_pk>/<int:member_pk>/', analyze_member_responses, name='analyze_member_responses'),
]
