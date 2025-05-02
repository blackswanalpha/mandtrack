"""
Views for PDF generation and download.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, FileResponse
from django.views.decorators.http import require_GET
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile

from surveys.models import Questionnaire
from feedback.models import Response, Answer, AIAnalysis
from analytics.models import Report, AIInsight
from analytics.utils.pdf_generator import (
    generate_clinical_report_pdf,
    generate_dashboard_report_pdf,
    generate_comparative_report_pdf
)

import json
import logging
import os

# Set up logger
logger = logging.getLogger(__name__)

@login_required
@require_GET
def download_report_pdf(request, report_id):
    """
    Download a report as PDF
    """
    report = get_object_or_404(Report, id=report_id)
    
    # Check if user has permission to download this report
    if report.created_by != request.user and (
        not report.questionnaire or 
        not report.questionnaire.organization or 
        not report.questionnaire.organization.members.filter(user=request.user).exists()
    ):
        messages.error(request, "You don't have permission to download this report.")
        return redirect('dashboard:index')
    
    # Check if PDF file exists
    if report.pdf_file:
        # Return the PDF file
        return FileResponse(report.pdf_file, as_attachment=True, filename=f"{report.title}.pdf")
    
    # If PDF file doesn't exist, generate it
    try:
        # Parse report content
        if isinstance(report.content, str):
            content = json.loads(report.content)
        else:
            content = report.content
        
        # Get response and questionnaire
        response_obj = report.response
        questionnaire = report.questionnaire
        
        if not response_obj or not questionnaire:
            messages.error(request, "Report is missing required data.")
            return redirect('analytics:report_detail', pk=report.id)
        
        # Generate PDF
        pdf_data = generate_clinical_report_pdf(
            report_data=content,
            response_data=response_obj,
            questionnaire_data=questionnaire,
            user_data=request.user
        )
        
        # Save PDF to report object
        report.pdf_file.save(
            f"clinical_report_{response_obj.id}.pdf",
            ContentFile(pdf_data),
            save=True
        )
        
        # Return the PDF file
        return FileResponse(report.pdf_file, as_attachment=True, filename=f"{report.title}.pdf")
    
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('analytics:report_detail', pk=report.id)

@login_required
@require_GET
def download_dashboard_pdf(request, questionnaire_id):
    """
    Download a dashboard report as PDF
    """
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    
    # Check if user has permission to view this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to download this dashboard report.")
        return redirect('dashboard:index')
    
    try:
        from analytics.views.enhanced_dashboard_views import questionnaire_dashboard
        
        # Get the same data used for the dashboard view
        context = questionnaire_dashboard(request, questionnaire_id, return_context=True)
        
        if not context:
            messages.error(request, "Error generating dashboard data.")
            return redirect('analytics:questionnaire_dashboard', questionnaire_id=questionnaire_id)
        
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
        
        # Create a report object to store the PDF
        report = Report.objects.create(
            title=f"Dashboard Report - {questionnaire.title}",
            description=f"Dashboard report for {questionnaire.title} generated on {timezone.now().strftime('%Y-%m-%d')}",
            report_type='dashboard',
            report_format='pdf',
            questionnaire=questionnaire,
            organization=questionnaire.organization,
            created_by=request.user,
            status='completed'
        )
        
        # Save PDF to report object
        report.pdf_file.save(
            f"dashboard_report_{questionnaire.id}.pdf",
            ContentFile(pdf_data),
            save=True
        )
        
        # Return the PDF file
        return FileResponse(report.pdf_file, as_attachment=True, filename=f"Dashboard Report - {questionnaire.title}.pdf")
    
    except Exception as e:
        logger.error(f"Error generating dashboard PDF: {str(e)}")
        messages.error(request, f"Error generating dashboard PDF: {str(e)}")
        return redirect('analytics:questionnaire_dashboard', questionnaire_id=questionnaire_id)

@login_required
@require_GET
def download_comparative_pdf(request):
    """
    Download a comparative analysis report as PDF
    """
    # Get questionnaire IDs from query parameters
    questionnaire_ids = request.GET.getlist('questionnaire_ids')
    
    if not questionnaire_ids:
        messages.error(request, "No questionnaires selected for comparison.")
        return redirect('dashboard:index')
    
    try:
        # Get questionnaires
        questionnaires = Questionnaire.objects.filter(id__in=questionnaire_ids)
        
        # Check if user has permission to view these questionnaires
        for questionnaire in questionnaires:
            if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
                messages.error(request, f"You don't have permission to view {questionnaire.title}.")
                return redirect('dashboard:index')
        
        # Prepare data for PDF generation
        title = f"Comparative Analysis - {questionnaires.count()} Questionnaires"
        description = f"Comparative analysis of {', '.join([q.title for q in questionnaires])}"
        
        # Get comparison data
        from analytics.utils.chart_generators import generate_comparative_analysis_chart
        
        # Generate comparative chart
        comparative_chart = generate_comparative_analysis_chart([q.id for q in questionnaires])
        
        # Prepare comparison data
        comparison_data = {
            'summary': f"This report compares {questionnaires.count()} questionnaires: {', '.join([q.title for q in questionnaires])}.",
            'table_headers': ['Questionnaire', 'Category', 'Responses', 'Avg Score', 'High Risk %'],
            'table_data': [],
            'key_findings': [
                "Comparative analysis helps identify patterns across different questionnaires.",
                "Different questionnaire categories may show varying response patterns.",
                "Response rates and completion times can vary by questionnaire type."
            ],
            'recommendations': "Review questionnaires with higher risk levels for potential improvements. Consider standardizing question formats across similar questionnaires for better comparison."
        }
        
        # Add data for each questionnaire
        for questionnaire in questionnaires:
            # Get responses for this questionnaire
            responses = Response.objects.filter(survey=questionnaire)
            total_responses = responses.count()
            
            # Calculate average score
            responses_with_scores = responses.exclude(score__isnull=True)
            avg_score = responses_with_scores.aggregate(models.Avg('score'))['score__avg'] or 0
            
            # Calculate high risk percentage
            high_risk_responses = responses.filter(risk_level__in=['high', 'critical']).count()
            high_risk_percentage = (high_risk_responses / total_responses * 100) if total_responses > 0 else 0
            
            # Add to table data
            comparison_data['table_data'].append([
                questionnaire.title,
                questionnaire.category,
                total_responses,
                f"{avg_score:.1f}",
                f"{high_risk_percentage:.1f}%"
            ])
        
        # Prepare charts data
        charts_data = [
            {
                'title': 'Comparative Analysis',
                'description': 'Comparison of average scores across questionnaires',
                'data': comparative_chart
            }
        ]
        
        # Generate PDF
        pdf_data = generate_comparative_report_pdf(
            title=title,
            description=description,
            comparison_data=comparison_data,
            charts_data=charts_data
        )
        
        # Create a report object to store the PDF
        report = Report.objects.create(
            title=title,
            description=description,
            report_type='comparative',
            report_format='pdf',
            parameters={'questionnaire_ids': questionnaire_ids},
            created_by=request.user,
            status='completed'
        )
        
        # Save PDF to report object
        report.pdf_file.save(
            f"comparative_report_{timezone.now().strftime('%Y%m%d')}.pdf",
            ContentFile(pdf_data),
            save=True
        )
        
        # Return the PDF file
        return FileResponse(report.pdf_file, as_attachment=True, filename=f"{title}.pdf")
    
    except Exception as e:
        logger.error(f"Error generating comparative PDF: {str(e)}")
        messages.error(request, f"Error generating comparative PDF: {str(e)}")
        return redirect('dashboard:index')
