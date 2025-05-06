from django.urls import path
import surveys.views.scoring_views as scoring_views

urlpatterns = [
    # Scoring System URLs
    path('<int:questionnaire_id>/scoring/', scoring_views.scoring_list, name='scoring_list'),
    path('<int:questionnaire_id>/scoring/create/', scoring_views.scoring_create, name='scoring_create'),
    path('<int:questionnaire_id>/scoring/<int:scoring_id>/', scoring_views.scoring_detail, name='scoring_detail'),
    path('<int:questionnaire_id>/scoring/<int:scoring_id>/edit/', scoring_views.scoring_edit, name='scoring_edit'),
    path('<int:questionnaire_id>/scoring/<int:scoring_id>/delete/', scoring_views.scoring_delete, name='scoring_delete'),

    # Score Rule URLs
    path('<int:questionnaire_id>/scoring/<int:scoring_id>/rules/create/', scoring_views.score_rule_create, name='score_rule_create'),
    path('<int:questionnaire_id>/scoring/<int:scoring_id>/rules/<int:rule_id>/edit/', scoring_views.score_rule_edit, name='score_rule_edit'),
    path('<int:questionnaire_id>/scoring/<int:scoring_id>/rules/<int:rule_id>/delete/', scoring_views.score_rule_delete, name='score_rule_delete'),

    # Score Range URLs
    path('<int:questionnaire_id>/scoring/<int:scoring_id>/ranges/create/', scoring_views.score_range_create, name='score_range_create'),
    path('<int:questionnaire_id>/scoring/<int:scoring_id>/ranges/<int:range_id>/edit/', scoring_views.score_range_edit, name='score_range_edit'),
    path('<int:questionnaire_id>/scoring/<int:scoring_id>/ranges/<int:range_id>/delete/', scoring_views.score_range_delete, name='score_range_delete'),

    # Response Scoring URLs
    path('<int:questionnaire_id>/responses/<int:response_id>/calculate-score/', scoring_views.calculate_response_score, name='calculate_response_score'),
    path('<int:questionnaire_id>/responses/<int:response_id>/enhanced-score/', scoring_views.enhanced_calculate_score, name='enhanced_calculate_score'),
    path('<int:questionnaire_id>/response-scores/', scoring_views.response_scores, name='response_scores'),
]
