from django.urls import path
from analytics.views import gemini_analysis_views

urlpatterns = [
    # Gemini AI Analysis
    path('gemini/', gemini_analysis_views.gemini_analysis_dashboard, name='gemini_analysis_dashboard'),
    path('gemini/questionnaire/<uuid:questionnaire_id>/', gemini_analysis_views.analyze_questionnaire, name='analyze_questionnaire'),
    path('gemini/response/<uuid:response_id>/', gemini_analysis_views.analyze_response, name='analyze_response'),
    path('gemini/text/', gemini_analysis_views.analyze_text, name='analyze_text'),
]
