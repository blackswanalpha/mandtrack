from django.urls import path
from . import views_trend

urlpatterns = [
    path('trends/member/<int:org_pk>/<int:member_pk>/', views_trend.member_trend_analysis, name='member_trend_analysis'),
    path('trends/organization/<int:org_pk>/', views_trend.organization_trend_analysis, name='organization_trend_analysis'),
]
