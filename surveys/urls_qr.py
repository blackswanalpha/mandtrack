from django.urls import path
from . import qr_views

urlpatterns = [
    path('', qr_views.qr_code_list_redirect, name='qr_code_list_redirect'),
    path('list/', qr_views.qr_code_list, name='qr_code_list'),
    path('create/', qr_views.qr_code_create, name='qr_code_create'),
    path('<int:pk>/', qr_views.qr_code_detail, name='qr_code_detail'),
]
