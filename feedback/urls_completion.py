from django.urls import path
import feedback.views.completion_views as completion_views

urlpatterns = [
    # Tracking endpoints (AJAX)
    path('responses/<uuid:response_id>/track/start/', completion_views.track_response_start, name='track_response_start'),
    path('responses/<uuid:response_id>/track/answer/<int:question_id>/', completion_views.track_answer_submission, name='track_answer_submission'),
    path('responses/<uuid:response_id>/track/navigation/', completion_views.track_navigation, name='track_navigation'),
    path('responses/<uuid:response_id>/track/completion/', completion_views.track_completion, name='track_completion'),
    path('responses/<uuid:response_id>/track/abandonment/', completion_views.track_abandonment, name='track_abandonment'),

    # Statistics views
    path('questionnaires/<uuid:questionnaire_id>/completion-stats/', completion_views.view_completion_stats, name='view_completion_stats'),
    path('completion-trackers/<int:tracker_id>/', completion_views.view_completion_details, name='view_completion_details'),
]
