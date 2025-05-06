from django.urls import path
from .views.enhanced_scoring_views import (
    enhanced_scoring_detail, enhanced_scoring_feedback, calculate_enhanced_score
)

app_name = 'enhanced_scoring'

urlpatterns = [
    # Enhanced Scoring URLs
    path('responses/<int:response_id>/enhanced-scoring/', enhanced_scoring_detail, name='detail'),
    path('responses/<int:response_id>/enhanced-scoring/<int:scoring_system_id>/', enhanced_scoring_detail, name='detail_with_system'),
    path('responses/<int:response_id>/enhanced-scoring/<int:scoring_system_id>/feedback/', enhanced_scoring_feedback, name='feedback'),
    path('responses/<int:response_id>/enhanced-scoring/<int:scoring_system_id>/calculate/', calculate_enhanced_score, name='calculate'),
    path('enhanced-scoring/feedback/', enhanced_scoring_feedback, name='feedback_form'),
]
