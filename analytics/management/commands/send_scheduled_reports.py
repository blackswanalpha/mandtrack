"""
Management command to send scheduled reports.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from analytics.models import ScheduledReport, Report
from surveys.models import Questionnaire
from feedback.models import Response
from analytics.utils.email_service import (
    send_clinical_report_email,
    send_dashboard_report_email,
    send_batch_report_email
)
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send scheduled reports that are due'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting scheduled reports check...'))
        
        # Get all active scheduled reports
        scheduled_reports = ScheduledReport.objects.filter(is_active=True)
        
        if not scheduled_reports.exists():
            self.stdout.write(self.style.SUCCESS('No active scheduled reports found.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found {scheduled_reports.count()} active scheduled reports.'))
        
        # Check each scheduled report
        for scheduled_report in scheduled_reports:
            if scheduled_report.is_due():
                self.stdout.write(f'Processing scheduled report: {scheduled_report}')
                
                try:
                    # Process the report based on its type
                    if scheduled_report.report_type == 'clinical':
                        self.send_clinical_report(scheduled_report)
                    elif scheduled_report.report_type == 'dashboard':
                        self.send_dashboard_report(scheduled_report)
                    elif scheduled_report.report_type == 'batch':
                        self.send_batch_report(scheduled_report)
                    else:
                        self.stdout.write(self.style.WARNING(f'Unsupported report type: {scheduled_report.report_type}'))
                        continue
                    
                    # Mark as sent
                    scheduled_report.mark_as_sent()
                    self.stdout.write(self.style.SUCCESS(f'Successfully sent scheduled report: {scheduled_report}'))
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error sending scheduled report: {str(e)}'))
                    logger.error(f'Error sending scheduled report {scheduled_report.id}: {str(e)}')
            else:
                self.stdout.write(f'Scheduled report not due yet: {scheduled_report}')
        
        self.stdout.write(self.style.SUCCESS('Finished processing scheduled reports.'))
    
    def send_clinical_report(self, scheduled_report):
        """
        Send a clinical report
        """
        parameters = scheduled_report.parameters
        
        # Get report
        report_id = parameters.get('report_id')
        if not report_id:
            raise ValueError('Report ID not found in parameters')
        
        report = Report.objects.get(id=report_id)
        
        # Get user
        user_id = parameters.get('user')
        user = User.objects.get(id=user_id) if user_id else None
        
        # Send email
        success = send_clinical_report_email(
            report=report,
            recipient_email=scheduled_report.recipient_email,
            sender_name=user.get_full_name() if user else 'MindTrack',
            additional_message=f'This is an automated report sent as scheduled ({scheduled_report.schedule.get("frequency", "daily")}).'
        )
        
        if not success:
            raise ValueError('Failed to send clinical report email')
    
    def send_dashboard_report(self, scheduled_report):
        """
        Send a dashboard report
        """
        parameters = scheduled_report.parameters
        
        # Get questionnaire
        questionnaire_id = parameters.get('questionnaire_id')
        if not questionnaire_id:
            raise ValueError('Questionnaire ID not found in parameters')
        
        questionnaire = Questionnaire.objects.get(id=questionnaire_id)
        
        # Get user
        user_id = parameters.get('user')
        user = User.objects.get(id=user_id) if user_id else None
        
        # Generate dashboard report
        from analytics.utils.pdf_generator import generate_dashboard_report_pdf
        from django.core.files.base import ContentFile
        
        # Create a report object
        report = Report.objects.create(
            title=f"Dashboard Report - {questionnaire.title}",
            description=f"Dashboard report for {questionnaire.title} generated on {timezone.now().strftime('%Y-%m-%d')}",
            report_type='dashboard',
            report_format='pdf',
            questionnaire=questionnaire,
            organization=questionnaire.organization,
            created_by=user,
            status='completed'
        )
        
        # Get data for dashboard report
        from analytics.views.enhanced_dashboard_views import questionnaire_dashboard
        from django.http import HttpRequest
        
        # Create a dummy request
        request = HttpRequest()
        request.user = user
        
        # Get dashboard data
        context = questionnaire_dashboard(request, questionnaire.id, return_context=True)
        
        if not context:
            raise ValueError('Failed to generate dashboard data')
        
        # Prepare data for PDF generation
        questionnaire_data = {
            'id': str(questionnaire.id),
            'title': questionnaire.title,
            'description': questionnaire.description,
            'category': questionnaire.category
        }
        
        stats_data = {
            'total_responses': context.get('total_responses', 0),
            'completion_rate': context.get('completion_rate', 0),
            'avg_score': context.get('avg_score', 0),
            'high_risk_percentage': context.get('high_risk_percentage', 0)
        }
        
        charts_data = {
            'risk_distribution_chart': context.get('risk_distribution_chart', ''),
            'score_distribution_chart': context.get('score_distribution_chart', ''),
            'response_trend_chart': context.get('response_trend_chart', ''),
            'completion_time_chart': context.get('completion_time_chart', ''),
            'comparative_analysis_chart': context.get('comparative_analysis_chart', ''),
            'age_distribution_chart': context.get('age_distribution_chart', ''),
            'gender_distribution_chart': context.get('gender_distribution_chart', ''),
            'sentiment_chart': context.get('sentiment_chart', ''),
            'recommendations_chart': context.get('recommendations_chart', '')
        }
        
        # Generate PDF
        pdf_data = generate_dashboard_report_pdf(
            questionnaire_data=questionnaire_data,
            stats_data=stats_data,
            charts_data=charts_data
        )
        
        # Save PDF to report object
        report.pdf_file.save(
            f"dashboard_report_{questionnaire.id}.pdf",
            ContentFile(pdf_data),
            save=True
        )
        
        # Send email
        success = send_dashboard_report_email(
            report=report,
            recipient_email=scheduled_report.recipient_email,
            sender_name=user.get_full_name() if user else 'MindTrack',
            additional_message=f'This is an automated report sent as scheduled ({scheduled_report.schedule.get("frequency", "daily")}).'
        )
        
        if not success:
            raise ValueError('Failed to send dashboard report email')
    
    def send_batch_report(self, scheduled_report):
        """
        Send a batch report
        """
        parameters = scheduled_report.parameters
        
        # Get questionnaire
        questionnaire_id = parameters.get('questionnaire_id')
        if not questionnaire_id:
            raise ValueError('Questionnaire ID not found in parameters')
        
        questionnaire = Questionnaire.objects.get(id=questionnaire_id)
        
        # Get responses
        responses = Response.objects.filter(survey=questionnaire)
        
        if not responses.exists():
            raise ValueError('No responses found for this questionnaire')
        
        # Get user
        user_id = parameters.get('user')
        user = User.objects.get(id=user_id) if user_id else None
        
        # Send email
        success = send_batch_report_email(
            responses=responses,
            recipient_email=scheduled_report.recipient_email,
            sender_name=user.get_full_name() if user else 'MindTrack',
            additional_message=f'This is an automated report sent as scheduled ({scheduled_report.schedule.get("frequency", "daily")}).'
        )
        
        if not success:
            raise ValueError('Failed to send batch report email')
