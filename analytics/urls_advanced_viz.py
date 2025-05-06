from django.urls import path
from . import views_advanced_viz

urlpatterns = [
    path('visualizations/advanced/<int:org_pk>/', views_advanced_viz.advanced_visualizations, name='advanced_visualizations'),
    path('visualizations/radar/<int:org_pk>/<int:member_pk>/', views_advanced_viz.member_radar_chart, name='member_radar_chart'),
    path('visualizations/heatmap/<int:org_pk>/', views_advanced_viz.organization_heatmap, name='organization_heatmap'),
    path('visualizations/bubble/<int:org_pk>/', views_advanced_viz.bubble_chart, name='bubble_chart'),
    path('visualizations/timeline/<int:org_pk>/<int:member_pk>/', views_advanced_viz.timeline_chart, name='timeline_chart'),
]
