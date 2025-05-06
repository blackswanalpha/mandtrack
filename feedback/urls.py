from django.urls import path, include
from . import views_new as views
from . import client_views

app_name = 'feedback'

urlpatterns = [
    # Admin/staff routes
    path('', views.response_list, name='response_list'),

    # Client/public routes - Put these first to avoid conflicts with the generic <str:pk> pattern
    path('complete/', views.response_complete, name='response_complete'),
    path('questionnaire/<str:questionnaire_pk>/respond/', views.respond_to_questionnaire, name='respond_to_questionnaire'),
    path('questionnaire/<str:questionnaire_pk>/', views.questionnaire_response_list, name='questionnaire_response_list'),

    # Response detail routes - These should come after more specific routes
    path('<str:pk>/', views.response_detail, name='response_detail'),
    path('<str:pk>/tabs/', views.response_detail_tabs, name='response_detail_tabs'),
    path('<str:pk>/analyze/', views.response_analyze, name='response_analyze'),
    path('<str:pk>/update-notes/', views.update_notes, name='update_notes'),
    path('<str:pk>/generate-analysis/', views.generate_analysis, name='generate_analysis'),
    path('<str:pk>/export/', views.export_response, name='export_response'),

    # New client routes with minimal layout
    path('client/questionnaire/<str:questionnaire_pk>/', client_views.client_questionnaire_response, name='client_questionnaire_response'),

    # Include completion tracking URLs
    path('', include('feedback.urls_completion')),

    # Include email dashboard URLs
    path('', include('feedback.urls_email')),

    # Include email schedule URLs
    path('', include('feedback.urls_schedule')),
]
