from django.urls import path
import analytics.views.ai_analysis_views as ai_analysis_views

urlpatterns = [
    # AI Model URLs
    path('ai-models/', ai_analysis_views.ai_model_list, name='ai_model_list'),
    path('ai-models/create/', ai_analysis_views.ai_model_create, name='ai_model_create'),
    path('ai-models/<int:model_id>/', ai_analysis_views.ai_model_detail, name='ai_model_detail'),
    path('ai-models/<int:model_id>/edit/', ai_analysis_views.ai_model_edit, name='ai_model_edit'),
    path('ai-models/<int:model_id>/delete/', ai_analysis_views.ai_model_delete, name='ai_model_delete'),

    # AI Configuration URLs
    path('questionnaires/<int:questionnaire_id>/ai-configurations/', ai_analysis_views.ai_configuration_list, name='ai_configuration_list'),
    path('questionnaires/<int:questionnaire_id>/ai-configurations/create/', ai_analysis_views.ai_configuration_create, name='ai_configuration_create'),
    path('questionnaires/<int:questionnaire_id>/ai-configurations/<int:config_id>/edit/', ai_analysis_views.ai_configuration_edit, name='ai_configuration_edit'),
    path('questionnaires/<int:questionnaire_id>/ai-configurations/<int:config_id>/delete/', ai_analysis_views.ai_configuration_delete, name='ai_configuration_delete'),

    # Analysis URLs
    path('responses/<int:response_id>/analyze/', ai_analysis_views.analyze_response, name='analyze_response'),
    path('analysis-results/<int:result_id>/', ai_analysis_views.analysis_result_detail, name='analysis_result_detail'),
    path('analysis-results/<int:result_id>/feedback/', ai_analysis_views.provide_feedback, name='provide_feedback'),

    # Insight URLs
    path('questionnaires/<uuid:questionnaire_id>/insights/', ai_analysis_views.ai_insights, name='ai_insights'),
    path('insights/<int:insight_id>/', ai_analysis_views.ai_insight_detail, name='ai_insight_detail'),
    path('insights/<int:insight_id>/archive/', ai_analysis_views.archive_insight, name='archive_insight'),
]
