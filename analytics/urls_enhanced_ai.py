from django.urls import path
from analytics.views import enhanced_ai_views

urlpatterns = [
    path('ai/enhanced/<uuid:response_id>/', enhanced_ai_views.enhanced_ai_analysis, name='enhanced_ai_analysis'),
    path('ai/enhanced/<uuid:response_id>/generate/', enhanced_ai_views.generate_enhanced_analysis, name='generate_enhanced_analysis'),
    path('ai/batch/<uuid:questionnaire_id>/', enhanced_ai_views.batch_analysis, name='batch_analysis'),
    path('ai/batch/<uuid:questionnaire_id>/generate/', enhanced_ai_views.generate_batch_analysis, name='generate_batch_analysis'),
    path('ai/visualizations/<uuid:questionnaire_id>/', enhanced_ai_views.visualization_recommendations, name='visualization_recommendations'),
    path('ai/visualizations/<uuid:questionnaire_id>/generate/', enhanced_ai_views.generate_visualization_recommendations, name='generate_visualization_recommendations'),
    path('ai/report/<uuid:response_id>/', enhanced_ai_views.generate_report, name='generate_report'),
    path('ai/report/<uuid:response_id>/create/', enhanced_ai_views.create_report, name='create_report'),
    path('ai/email/<uuid:response_id>/', enhanced_ai_views.send_analysis_email, name='send_analysis_email'),
]
