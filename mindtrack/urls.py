"""
URL configuration for mindtrack project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from feedback import views_new

urlpatterns = [
    # Django admin (kept for superusers)
    path('admin/', admin.site.urls),

    # Authentication and user management
    path('accounts/', include('allauth.urls')),  # Third-party auth (kept for compatibility)
    path('admin-portal/', include('accounts.urls')),  # Admin portal
    path('client-portal/', include('users.urls')),  # Client portal

    # Main application URLs
    path('', include('core.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('questionnaires/', include('surveys.urls')),
    path('questionnaires/qr-codes/', include('surveys.urls_qr')),
    path('responses/', include('feedback.urls')),
    path('groups/', include('groups.urls')),
    path('organizations/', include('organizations.urls')),
    path('analytics/', include('analytics.urls')),

    # QR code scanning and direct questionnaire access
    path('qr/', include([
        path('scan/', include('users.urls', namespace='qr_scan')),
        path('codes/', include('surveys.urls_qr')),
    ])),

    # Direct questionnaire access (public URLs)
    path('q/', include([
        path('<uuid:pk>/', views_new.direct_questionnaire_access, name='direct_questionnaire_access_uuid'),
        path('<slug:slug>/', views_new.direct_questionnaire_access, name='direct_questionnaire_access_slug'),
    ])),

    # Keep old URLs for backward compatibility
    path('users/', include('users.urls', namespace='users_old')),
    path('surveys/', include('surveys.urls', namespace='surveys_old')),
    path('feedback/', include('feedback.urls', namespace='feedback_old')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
