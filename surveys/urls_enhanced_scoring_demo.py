"""
URL patterns for enhanced scoring demo.
"""
from django.urls import path
from surveys.views.enhanced_scoring_view import enhanced_scoring_results

app_name = 'enhanced_scoring_demo'

urlpatterns = [
    path('enhanced-scoring-results/', enhanced_scoring_results, name='results'),
]
