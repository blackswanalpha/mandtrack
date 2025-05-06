import os
import tempfile
from django.template.loader import render_to_string
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from weasyprint import HTML, CSS
from feedback.models import Response, Answer
from surveys.models import Questionnaire
from django.db.models import Avg

class PDFService:
    """
    Service for generating PDF reports
    """
    
    @staticmethod
    def generate_member_report(member, organization, responses=None):
        """
        Generate a comprehensive PDF report for a member
        
        Args:
            member: OrganizationMember instance
            organization: Organization instance
            responses: Optional QuerySet of Response objects (if None, all responses for the member will be used)
            
        Returns:
            HttpResponse with PDF content
        """
        # Get all responses for this member if not provided
        if responses is None:
            responses = Response.objects.filter(
                user=member.user,
                survey__organization=organization
            ).select_related('survey').order_by('-created_at')
        
        # Calculate statistics
        total_responses = responses.count()
        completed_responses = responses.filter(status='completed').count()
        average_score = responses.aggregate(Avg('score'))['score__avg'] or 0
        
        # Get high risk responses
        high_risk_responses = responses.filter(risk_level='high')
        has_high_risk_responses = high_risk_responses.exists()
        
        # Get questionnaires for this organization
        questionnaires = Questionnaire.objects.filter(organization=organization)
        
        # Get response count by questionnaire
        response_counts = []
        for questionnaire in questionnaires:
            count = Response.objects.filter(
                user=member.user,
                survey=questionnaire
            ).count()
            if count > 0:
                response_counts.append({
                    'questionnaire': questionnaire,
                    'count': count
                })
        
        # Determine risk level based on average score
        risk_level = 'low'
        risk_description = "Based on responses, this member appears to be at low risk. Continue with current practices and monitor regularly."
        
        if average_score < 50:
            risk_level = 'high'
            risk_description = "Responses indicate a higher level of risk. We recommend reviewing the detailed assessment and considering the suggested actions."
        elif average_score < 70:
            risk_level = 'medium'
            risk_description = "Responses indicate a moderate level of risk. Consider implementing some of the recommendations to improve the situation."
        
        # Get recent responses for detailed analysis
        recent_responses = responses[:5]
        
        # Get AI analyses for recent responses
        for response in recent_responses:
            try:
                response.ai_analysis = response.analysis
            except:
                response.ai_analysis = None
        
        # Prepare context for the template
        context = {
            'member': member,
            'organization': organization,
            'total_responses': total_responses,
            'completed_responses': completed_responses,
            'average_score': average_score,
            'risk_level': risk_level,
            'risk_description': risk_description,
            'has_high_risk_responses': has_high_risk_responses,
            'high_risk_responses': high_risk_responses,
            'recent_responses': recent_responses,
            'response_counts': response_counts,
            'report_date': timezone.now(),
            'report_type': 'Comprehensive Member Report'
        }
        
        # Render HTML content
        html_string = render_to_string('reports/member_report.html', context)
        
        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as output:
            # Generate PDF
            HTML(string=html_string).write_pdf(
                output,
                stylesheets=[
                    CSS(string='@page { size: letter; margin: 1cm }')
                ]
            )
            output_path = output.name
        
        # Read the PDF file
        with open(output_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{member.user.get_full_name()}_report.pdf"'
        
        # Clean up the temporary file
        os.unlink(output_path)
        
        return response
    
    @staticmethod
    def generate_response_report(response):
        """
        Generate a PDF report for a single response
        
        Args:
            response: Response instance
            
        Returns:
            HttpResponse with PDF content
        """
        # Get the questionnaire and organization
        questionnaire = response.survey
        organization = questionnaire.organization if hasattr(questionnaire, 'organization') else None
        
        # Get all answers for this response
        answers = Answer.objects.filter(response=response).select_related('question', 'selected_choice').prefetch_related('multiple_choices')
        
        # Get AI analysis if available
        try:
            ai_analysis = response.analysis
        except:
            ai_analysis = None
        
        # Prepare context for the template
        context = {
            'response': response,
            'questionnaire': questionnaire,
            'organization': organization,
            'answers': answers,
            'ai_analysis': ai_analysis,
            'report_date': timezone.now(),
            'report_type': 'Response Report'
        }
        
        # Render HTML content
        html_string = render_to_string('reports/response_report.html', context)
        
        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as output:
            # Generate PDF
            HTML(string=html_string).write_pdf(
                output,
                stylesheets=[
                    CSS(string='@page { size: letter; margin: 1cm }')
                ]
            )
            output_path = output.name
        
        # Read the PDF file
        with open(output_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="response_{response.id}_report.pdf"'
        
        # Clean up the temporary file
        os.unlink(output_path)
        
        return response
