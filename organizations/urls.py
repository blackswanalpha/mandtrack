from django.urls import path, include
from . import views

app_name = 'organizations'

urlpatterns = [
    # Include QR code URLs
    path('', include('organizations.urls_qr')),
]
