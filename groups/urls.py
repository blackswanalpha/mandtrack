from django.urls import path
from . import views

app_name = 'groups'

urlpatterns = [
    path('', views.organization_list, name='organization_list'),
    path('create/', views.organization_create, name='organization_create'),
    path('<int:pk>/', views.organization_detail, name='organization_detail'),
    path('<int:pk>/edit/', views.organization_edit, name='organization_edit'),
    path('<int:pk>/delete/', views.organization_delete, name='organization_delete'),
    path('<int:pk>/members/', views.member_list, name='member_list'),
    path('<int:org_pk>/members/add/', views.member_add, name='member_add'),
    path('<int:org_pk>/members/<int:pk>/', views.member_detail, name='member_detail'),
    path('<int:org_pk>/members/<int:pk>/edit/', views.member_edit, name='member_edit'),
    path('<int:org_pk>/members/<int:pk>/remove/', views.member_remove, name='member_remove'),
    path('<int:org_pk>/members/<int:member_pk>/dashboard/', views.view_member_dashboard, name='view_member_dashboard'),
    path('<int:pk>/questionnaires/', views.organization_questionnaires, name='organization_questionnaires'),
]
