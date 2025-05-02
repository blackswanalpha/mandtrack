# Import models directly from their respective files
from analytics.models.reports import Report, ReportSchedule
from analytics.models.base import AIModel, AIAnalysisConfiguration, AIAnalysisResult, AIInsight, AIFeedback
from analytics.models.dashboard import Dashboard, Widget
from analytics.models.batch import BatchAnalysisJob
from analytics.models.scheduled_reports import ScheduledReport

__all__ = [
    'Report',
    'ReportSchedule',
    'AIModel',
    'AIAnalysisConfiguration',
    'AIAnalysisResult',
    'AIInsight',
    'AIFeedback',
    'Dashboard',
    'Widget',
    'BatchAnalysisJob',
    'ScheduledReport',
]
