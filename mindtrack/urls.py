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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
# Import admin
from django.contrib import admin
# Import views for direct questionnaire access
from feedback import views_new

urlpatterns = [
    # Django admin (kept for superusers)
    path('admin/', admin.site.urls),

    # Authentication and user management
    path('accounts/', include('allauth.urls')),  # Third-party auth (kept for compatibility)
    path('admin-portal/', include('accounts.urls')),  # Admin portal
    # Client portal with namespace
    path('client-portal/', include('users.urls', namespace='users')),

    # Main application URLs
    path('', include('core.urls')),
    # Dashboard URLs
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    # Surveys URLs
    path('surveys/', include('surveys.urls', namespace='surveys')),
    # Questionnaires URLs
    path('questionnaires/', include('questionnaires.urls')),
    # path('questionnaires/qr-codes/', include('surveys.urls_qr')),
    path('responses/', include('feedback.urls', namespace='feedback')),
    # path('demo/', include('surveys.urls_enhanced_scoring_demo')),
    path('groups/', include('groups.urls', namespace='groups')),
    # path('organizations/', include('organizations.urls')),
    # Uncommented to fix NoReverseMatch error
    path('analytics/', include('analytics.urls', namespace='analytics')),
    path('members/', include('members.urls', namespace='members')),

    # QR code scanning and direct questionnaire access
    path('qr/', include([
        path('scan/', include('users.urls')),
        path('codes/', include('surveys.urls_qr')),
    ])),

    # Direct questionnaire access (public URLs)
    path('q/', include([
        path('<uuid:pk>/', views_new.direct_questionnaire_access, name='direct_questionnaire_access_uuid'),
        path('<str:pk>/', views_new.direct_questionnaire_access, name='direct_questionnaire_access_str'),
        path('<slug:slug>/', views_new.direct_questionnaire_access, name='direct_questionnaire_access_slug'),
    ])),

    # Keep old URLs for backward compatibility - temporarily commented out
    # path('users/', include('users.urls', namespace='users_old')),
    # path('surveys/', include('surveys.urls', namespace='surveys_old')),
    # path('feedback/', include('feedback.urls', namespace='feedback_old')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
