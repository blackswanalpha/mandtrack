from django.urls import path, include
from . import test_error
from core.views.toast_demo import toast_demo, enhanced_toast_demo, show_toast
from core import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('test-database/', views.test_database, name='test_database'),
    path('health/', views.health_check, name='health_check'),

    # Toast notification demo
    path('toast-demo/', toast_demo, name='toast_demo'),
    path('toast-demo/enhanced/', enhanced_toast_demo, name='enhanced_toast_demo'),
    path('toast-demo/show/<str:toast_type>/', show_toast, name='show_toast'),

    # Test login with toast notifications
    path('test-login/', views.test_login, name='test_login'),
    path('test-toast/<str:toast_type>/', views.show_toast, name='test_toast'),

    # Test error handling URLs (only available in DEBUG mode)
    path('', include(test_error.urlpatterns)),
]
