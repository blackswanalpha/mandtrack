from django.urls import path, include
from . import views_new as views
from . import client_views

app_name = 'feedback'

urlpatterns = [
    # Admin/staff routes
    path('', views.response_list, name='response_list'),
    path('<uuid:pk>/', views.response_detail, name='response_detail'),
    path('<uuid:pk>/tabs/', views.response_detail_tabs, name='response_detail_tabs'),
    path('<uuid:pk>/analyze/', views.response_analyze, name='response_analyze'),
    path('<uuid:pk>/update-notes/', views.update_notes, name='update_notes'),
    path('<uuid:pk>/generate-analysis/', views.generate_analysis, name='generate_analysis'),
    path('<uuid:pk>/export/', views.export_response, name='export_response'),
    path('questionnaire/<uuid:questionnaire_pk>/', views.questionnaire_response_list, name='questionnaire_response_list'),

    # Client/public routes
    path('questionnaire/<uuid:questionnaire_pk>/respond/', views.respond_to_questionnaire, name='respond_to_questionnaire'),
    path('complete/', views.response_complete, name='response_complete'),

    # New client routes with minimal layout
    path('client/questionnaire/<uuid:questionnaire_pk>/', client_views.client_questionnaire_response, name='client_questionnaire_response'),

    # Include completion tracking URLs
    path('', include('feedback.urls_completion')),
]
