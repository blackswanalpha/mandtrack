from django.urls import path
from . import views_new as views

app_name = 'feedback'

urlpatterns = [
    # Admin/staff routes
    path('', views.response_list, name='response_list'),
    path('<uuid:pk>/', views.response_detail, name='response_detail'),
    path('<uuid:pk>/analyze/', views.response_analyze, name='response_analyze'),
    path('<uuid:pk>/update-notes/', views.update_notes, name='update_notes'),
    path('<uuid:pk>/generate-analysis/', views.generate_analysis, name='generate_analysis'),
    path('<uuid:pk>/export/', views.export_response, name='export_response'),
    path('questionnaire/<uuid:questionnaire_pk>/', views.questionnaire_response_list, name='questionnaire_response_list'),

    # Client/public routes
    path('questionnaire/<uuid:questionnaire_pk>/respond/', views.respond_to_questionnaire, name='respond_to_questionnaire'),
    path('complete/', views.response_complete, name='response_complete'),
]
