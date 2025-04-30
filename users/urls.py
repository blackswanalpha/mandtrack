from django.urls import path
from . import views
from . import qr_views

app_name = 'users'

urlpatterns = [
    # Client authentication
    path('login/', views.client_login, name='client_login'),
    path('register/', views.client_register, name='client_register'),
    path('logout/', views.client_logout, name='client_logout'),

    # Client dashboard and profile
    path('dashboard/', views.client_dashboard, name='client_dashboard'),
    path('profile/', views.client_profile, name='client_profile'),
    path('profile/edit/', views.client_profile_edit, name='client_profile_edit'),
    path('profile/change-password/', views.client_change_password, name='client_change_password'),

    # QR code functionality
    path('qr-scan/', qr_views.qr_scan, name='qr_scan'),
    path('qr-email-entry/', qr_views.qr_email_entry, name='qr_email_entry'),

    # Legacy URLs for backward compatibility
    path('profile/', views.client_profile, name='profile'),
    path('profile/edit/', views.client_profile_edit, name='profile_edit'),
    path('profile/change-password/', views.client_change_password, name='change_password'),

    # Admin redirects (for backward compatibility)
    path('users/', views.user_list, name='user_list'),
    path('users/<uuid:pk>/', views.user_detail, name='user_detail'),
    path('users/<uuid:pk>/edit/', views.user_edit, name='user_edit'),
]
