from django.urls import path, include
from . import views
from . import test_error

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('test-database/', views.test_database, name='test_database'),
    path('health/', views.health_check, name='health_check'),

    # Test error handling URLs (only available in DEBUG mode)
    path('', include(test_error.urlpatterns)),
]
