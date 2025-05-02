from django.urls import path
from analytics.views.batch_analysis_views import (
    batch_analysis_select,
    batch_analysis_run,
    batch_analysis_results,
    batch_analysis_aggregate,
    batch_analysis_export
)

urlpatterns = [
    path('batch-analysis/', batch_analysis_select, name='batch_analysis_select'),
    path('batch-analysis/run/', batch_analysis_run, name='batch_analysis_run'),
    path('batch-analysis/results/<int:job_id>/', batch_analysis_results, name='batch_analysis_results'),
    path('batch-analysis/aggregate/<int:job_id>/', batch_analysis_aggregate, name='batch_analysis_aggregate'),
    path('batch-analysis/export/<int:job_id>/', batch_analysis_export, name='batch_analysis_export'),
]
