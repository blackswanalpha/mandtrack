from django.urls import path
from . import views

urlpatterns = [
    # Admin authentication
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    
    # Admin dashboard and profile
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('profile/', views.admin_profile, name='admin_profile'),
    path('change-password/', views.admin_change_password, name='admin_change_password'),
    
    # Admin user management
    path('users/', views.admin_users, name='admin_users'),
    path('users/create/', views.admin_create_user, name='admin_create_user'),
    path('users/<uuid:user_id>/edit/', views.admin_edit_user, name='admin_edit_user'),
]
