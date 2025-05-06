from django.urls import path
from questionnaires import views

urlpatterns = [
    # Questionnaire settings
    path('<str:id>/settings/', views.questionnaire_settings, name='questionnaire_settings'),
]
