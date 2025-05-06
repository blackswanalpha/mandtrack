from django.urls import path, include
from . import test_error
from core.views.toast_demo import toast_demo, show_toast
from core.views import home, about, contact, dashboard, test_database, health_check

app_name = 'core'

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('test-database/', test_database, name='test_database'),
    path('health/', health_check, name='health_check'),

    # Toast notification demo
    path('toast-demo/', toast_demo, name='toast_demo'),
    path('toast-demo/show/<str:toast_type>/', show_toast, name='show_toast'),

    # Test error handling URLs (only available in DEBUG mode)
    path('', include(test_error.urlpatterns)),
]
