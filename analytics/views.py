from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
import json
from datetime import datetime, timedelta
from feedback.models import Response, AIAnalysis
from groups.models import Organization, OrganizationMember
from .services.advanced_ai_service import AdvancedAIService

@login_required
def analytics_dashboard(request):
    """
    Main analytics dashboard
    """
    # In a real app, you'd fetch analytics data from the database
    context = get_dashboard_context(request)
    return render(request, 'analytics/dashboard.html', context)

def test_dashboard(request):
    """
    Test version of the analytics dashboard that doesn't require login
    Used for development and testing purposes only
    """
    context = get_dashboard_context(request)
    return render(request, 'analytics/dashboard.html', context)

def get_dashboard_context(request):
    """
    Generate context data for the dashboard
    """
    # Get filter parameters
    date_range = request.GET.get('date_range', '30')
    selected_organization = request.GET.get('organization', '')
    selected_survey = request.GET.get('survey', '')

    # Try to get real data if available
    try:
        from groups.models import Organization
        from surveys.models import Questionnaire

        # Get organizations
        organizations = Organization.objects.all().values('id', 'name')

        # Get surveys/questionnaires
        surveys = Questionnaire.objects.all().values('id', 'title')

        # If no real data, fall back to mock data
        if not organizations:
            organizations = [
                {'id': 1, 'name': 'General Hospital'},
                {'id': 2, 'name': 'Community Clinic'},
                {'id': 3, 'name': 'Research Institute'},
            ]

        if not surveys:
            surveys = [
                {'id': 1, 'title': 'Anxiety Assessment'},
                {'id': 2, 'title': 'Depression Screening'},
                {'id': 3, 'title': 'Stress Evaluation'},
            ]
    except Exception as e:
        # If there's an error, use mock data
        print(f"Error fetching real data: {e}")
        organizations = [
            {'id': 1, 'name': 'General Hospital'},
            {'id': 2, 'name': 'Community Clinic'},
            {'id': 3, 'name': 'Research Institute'},
        ]

        surveys = [
            {'id': 1, 'title': 'Anxiety Assessment'},
            {'id': 2, 'title': 'Depression Screening'},
            {'id': 3, 'title': 'Stress Evaluation'},
        ]

    # Generate dates for the response trend
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime('%b %d') for i in range(int(date_range) if date_range.isdigit() else 30)]
    dates.reverse()

    # Generate random data for the charts
    response_trend_data = [5, 8, 12, 10, 15, 20, 18, 25, 22, 30, 28, 35, 32, 38, 35, 42, 40, 45, 48, 52, 50, 55, 58, 60, 62, 65, 68, 70, 72, 75]
    risk_distribution_data = [45, 30, 15, 5, 5]
    survey_completion_labels = ['Anxiety Assessment', 'Depression Screening', 'Stress Evaluation', 'PTSD Screening', 'Well-being Check']
    survey_completion_data = [85, 72, 90, 65, 78]
    score_distribution_labels = ['0-5', '6-10', '11-15', '16-20', '21-25', '26-30']
    score_distribution_data = [10, 25, 35, 20, 8, 2]

    # Try to get real responses if available
    try:
        from feedback.models import Response

        # Get recent responses
        real_responses = Response.objects.select_related('survey').order_by('-started_at')[:4]

        if real_responses:
            # Convert to a list of dictionaries
            recent_responses = []
            for resp in real_responses:
                recent_responses.append({
                    'pk': resp.pk,
                    'respondent_name': getattr(resp, 'patient_name', None) or getattr(resp, 'respondent_name', None),
                    'respondent': resp.user,
                    'respondent_email': getattr(resp, 'patient_email', None) or getattr(resp, 'respondent_email', None),
                    'survey': {
                        'pk': resp.survey.pk,
                        'id': resp.survey.pk,
                        'title': resp.survey.title
                    },
                    'completed_at': resp.completed_at,
                    'started_at': resp.started_at,
                    'status': getattr(resp, 'status', 'completed'),
                    'get_status_display': getattr(resp, 'get_status_display', lambda: 'Completed')(),
                    'risk_level': getattr(resp, 'risk_level', 'none'),
                    'get_risk_level_display': getattr(resp, 'get_risk_level_display', lambda: 'None')(),
                    'total_score': getattr(resp, 'score', None)
                })
        else:
            # Use mock data with UUID-like strings
            import uuid
            recent_responses = [
                {
                    'pk': str(uuid.uuid4()),
                    'respondent_name': 'John Doe',
                    'respondent': None,
                    'respondent_email': 'john@example.com',
                    'survey': {'pk': str(uuid.uuid4()), 'id': str(uuid.uuid4()), 'title': 'Anxiety Assessment'},
                    'completed_at': today - timedelta(days=1),
                    'started_at': today - timedelta(days=1),
                    'status': 'completed',
                    'get_status_display': 'Completed',
                    'risk_level': 'medium',
                    'get_risk_level_display': 'Medium',
                    'total_score': 12
                },
                {
                    'pk': str(uuid.uuid4()),
                    'respondent_name': 'Jane Smith',
                    'respondent': None,
                    'respondent_email': 'jane@example.com',
                    'survey': {'pk': str(uuid.uuid4()), 'id': str(uuid.uuid4()), 'title': 'Depression Screening'},
                    'completed_at': today - timedelta(days=2),
                    'started_at': today - timedelta(days=2),
                    'status': 'completed',
                    'get_status_display': 'Completed',
                    'risk_level': 'high',
                    'get_risk_level_display': 'High',
                    'total_score': 18
                },
                {
                    'pk': str(uuid.uuid4()),
                    'respondent_name': 'Bob Johnson',
                    'respondent': None,
                    'respondent_email': 'bob@example.com',
                    'survey': {'pk': str(uuid.uuid4()), 'id': str(uuid.uuid4()), 'title': 'Stress Evaluation'},
                    'completed_at': today - timedelta(days=3),
                    'started_at': today - timedelta(days=3),
                    'status': 'completed',
                    'get_status_display': 'Completed',
                    'risk_level': 'low',
                    'get_risk_level_display': 'Low',
                    'total_score': 7
                },
                {
                    'pk': str(uuid.uuid4()),
                    'respondent_name': None,
                    'respondent': None,
                    'respondent_email': 'alice@example.com',
                    'survey': {'pk': str(uuid.uuid4()), 'id': str(uuid.uuid4()), 'title': 'Anxiety Assessment'},
                    'completed_at': None,
                    'started_at': today - timedelta(days=4),
                    'status': 'in_progress',
                    'get_status_display': 'In Progress',
                    'risk_level': 'none',
                    'get_risk_level_display': 'None',
                    'total_score': None
                },
            ]
    except Exception as e:
        # If there's an error, use mock data with UUID-like strings
        print(f"Error fetching real responses: {e}")
        import uuid
        recent_responses = [
            {
                'pk': str(uuid.uuid4()),
                'respondent_name': 'John Doe',
                'respondent': None,
                'respondent_email': 'john@example.com',
                'survey': {'pk': str(uuid.uuid4()), 'id': str(uuid.uuid4()), 'title': 'Anxiety Assessment'},
                'completed_at': today - timedelta(days=1),
                'started_at': today - timedelta(days=1),
                'status': 'completed',
                'get_status_display': 'Completed',
                'risk_level': 'medium',
                'get_risk_level_display': 'Medium',
                'total_score': 12
            },
            {
                'pk': str(uuid.uuid4()),
                'respondent_name': 'Jane Smith',
                'respondent': None,
                'respondent_email': 'jane@example.com',
                'survey': {'pk': str(uuid.uuid4()), 'id': str(uuid.uuid4()), 'title': 'Depression Screening'},
                'completed_at': today - timedelta(days=2),
                'started_at': today - timedelta(days=2),
                'status': 'completed',
                'get_status_display': 'Completed',
                'risk_level': 'high',
                'get_risk_level_display': 'High',
                'total_score': 18
            },
        ]

    # Calculate statistics
    total_responses = 250
    response_change = 15  # percentage change from previous period
    completion_rate = 85
    average_score = 14.5
    score_change = 2.3
    high_risk_count = 35
    high_risk_percentage = round((high_risk_count / total_responses) * 100)

    context = {
        'total_responses': total_responses,
        'response_change': response_change,
        'completion_rate': completion_rate,
        'average_score': average_score,
        'score_change': score_change,
        'high_risk_count': high_risk_count,
        'high_risk_percentage': high_risk_percentage,
        'organizations': organizations,
        'surveys': surveys,
        'selected_organization': selected_organization,
        'selected_survey': selected_survey,
        'date_range': date_range,
        'recent_responses': recent_responses,
        'response_trend_labels': json.dumps(dates),
        'response_trend_data': json.dumps(response_trend_data[-int(date_range) if date_range.isdigit() else 30:]),
        'risk_distribution_data': json.dumps(risk_distribution_data),
        'survey_completion_labels': json.dumps(survey_completion_labels),
        'survey_completion_data': json.dumps(survey_completion_data),
        'score_distribution_labels': json.dumps(score_distribution_labels),
        'score_distribution_data': json.dumps(score_distribution_data),
    }

    return context

@login_required
def survey_analytics(request):
    """
    Survey-specific analytics
    """
    # In a real app, you'd fetch survey analytics data from the database
    surveys = [
        {'id': 1, 'title': 'Anxiety Assessment', 'responses': 120, 'avg_score': 10.2},
        {'id': 2, 'title': 'Depression Screening', 'responses': 85, 'avg_score': 8.7},
        {'id': 3, 'title': 'Stress Evaluation', 'responses': 45, 'avg_score': 15.3},
    ]
    return render(request, 'analytics/survey_analytics.html', {'surveys': surveys})

@login_required
def response_analytics(request):
    """
    Response analytics
    """
    # In a real app, you'd fetch response analytics data from the database
    context = {
        'total_responses': 250,
        'responses_by_month': [15, 22, 30, 25, 35, 40, 45, 38],
        'responses_by_category': {
            'Anxiety': 120,
            'Depression': 85,
            'Stress': 45,
        },
    }
    return render(request, 'analytics/response_analytics.html', context)

@login_required
def user_analytics(request):
    """
    User analytics
    """
    # In a real app, you'd fetch user analytics data from the database
    context = {
        'total_users': 50,
        'active_users': 35,
        'users_by_role': {
            'Admin': 5,
            'Provider': 30,
            'Staff': 15,
        },
    }
    return render(request, 'analytics/user_analytics.html', context)

@login_required
def organization_analytics(request):
    """
    Organization analytics
    """
    # In a real app, you'd fetch organization analytics data from the database
    organizations = [
        {'id': 1, 'name': 'General Hospital', 'surveys': 8, 'responses': 150},
        {'id': 2, 'name': 'Community Clinic', 'surveys': 5, 'responses': 75},
        {'id': 3, 'name': 'Research Institute', 'surveys': 2, 'responses': 25},
    ]
    return render(request, 'analytics/organization_analytics.html', {'organizations': organizations})

@login_required
def ai_analysis(request):
    """
    AI analysis dashboard
    """
    # In a real app, you'd fetch AI analysis data from the database
    analyses = [
        {'id': 1, 'response_id': 1, 'survey': 'Anxiety Assessment', 'date': '2023-05-15', 'summary': 'Moderate anxiety detected'},
        {'id': 2, 'response_id': 2, 'survey': 'Depression Screening', 'date': '2023-05-14', 'summary': 'Mild depression detected'},
        {'id': 3, 'response_id': 3, 'survey': 'Stress Evaluation', 'date': '2023-05-13', 'summary': 'High stress levels detected'},
    ]
    return render(request, 'analytics/ai_analysis.html', {'analyses': analyses})

@login_required
def response_ai_analysis(request, response_pk):
    """
    AI analysis for a specific response
    """
    # In a real app, you'd fetch the response and its AI analysis from the database
    response = {'id': response_pk, 'survey': 'Sample Survey', 'date': '2023-05-15', 'score': 12}
    analysis = {
        'summary': 'Moderate anxiety detected',
        'recommendations': 'Consider follow-up assessment',
        'risk_level': 'Medium',
        'detailed_analysis': 'The response indicates moderate levels of anxiety with particular concerns in social situations. The patient reported feeling nervous or anxious several days a week and having trouble relaxing almost daily.',
    }
    return render(request, 'analytics/response_ai_analysis.html', {'response': response, 'analysis': analysis})

@login_required
def export_csv(request):
    """
    Export data as CSV
    """
    # In a real app, you'd generate a CSV file with the requested data
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="mindtrack_export.csv"'

    # Add CSV data to the response
    response.write('id,survey,date,score\n')
    response.write('1,Anxiety Assessment,2023-05-15,12\n')
    response.write('2,Depression Screening,2023-05-14,8\n')
    response.write('3,Stress Evaluation,2023-05-13,15\n')

    return response

@login_required
def export_pdf(request):
    """
    Export data as PDF
    """
    # In a real app, you'd generate a PDF file with the requested data
    # For now, we'll just return a message
    messages.info(request, 'PDF export functionality is coming soon!')
    return redirect('analytics:dashboard')

@login_required
def analyze_response(request, response_id):
    """
    Analyze a response using the advanced AI service
    """
    response = get_object_or_404(Response, pk=response_id)

    # Check if user has permission to analyze this response
    if response.organization:
        try:
            user_membership = OrganizationMember.objects.get(
                organization=response.organization,
                user=request.user,
                is_active=True
            )
            is_admin = user_membership.role == 'admin'
            can_view_responses = user_membership.can_view_responses()
        except OrganizationMember.DoesNotExist:
            # If user is staff, allow access even if not a member
            if request.user.is_staff:
                is_admin = True
                can_view_responses = True
            else:
                messages.error(request, "You don't have permission to analyze this response.")
                return redirect('feedback:response_detail', pk=response_id)

        # If user is not admin and can't view responses, deny access
        if not is_admin and not can_view_responses:
            messages.error(request, "You don't have permission to analyze this response.")
            return redirect('feedback:response_detail', pk=response_id)

    # If this is an AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            # Analyze the response
            analysis = AdvancedAIService.analyze_response(response)

            # Return the analysis as JSON
            return JsonResponse({
                'success': True,
                'analysis': {
                    'summary': analysis.summary,
                    'detailed_analysis': analysis.detailed_analysis,
                    'recommendations': analysis.recommendations,
                    'risk_level': analysis.risk_level,
                    'risk_justification': analysis.risk_justification,
                    'trends': analysis.trends,
                    'follow_up_areas': analysis.follow_up_areas
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    # If this is a regular request, analyze and redirect
    try:
        # Analyze the response
        analysis = AdvancedAIService.analyze_response(response)
        messages.success(request, "Response analyzed successfully.")
    except Exception as e:
        messages.error(request, f"Error analyzing response: {str(e)}")

    # Redirect to the response detail page
    return redirect('feedback:response_detail', pk=response_id)

@login_required
def analyze_member_responses(request, org_pk, member_pk):
    """
    Analyze all responses from a member to identify trends and patterns
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    member = get_object_or_404(OrganizationMember, pk=member_pk, organization=organization)

    # Check if user has permission to view member dashboard
    try:
        user_membership = OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            is_active=True
        )
        is_admin = user_membership.role == 'admin'
        can_view_responses = user_membership.can_view_responses()
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not a member
        if request.user.is_staff:
            is_admin = True
            can_view_responses = True
        else:
            messages.error(request, "You don't have permission to analyze this member's responses.")
            return redirect('groups:organization_list')

    # If user is not admin and can't view responses, deny access
    if not is_admin and not can_view_responses:
        messages.error(request, "You don't have permission to analyze this member's responses.")
        return redirect('groups:member_detail', org_pk=org_pk, pk=member_pk)

    # If this is an AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            # Analyze the member's responses
            analysis = AdvancedAIService.analyze_member_responses(member, organization)

            # Return the analysis as JSON
            return JsonResponse({
                'success': True,
                'analysis': analysis
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    # If this is a regular request, analyze and redirect
    try:
        # Analyze the member's responses
        analysis = AdvancedAIService.analyze_member_responses(member, organization)

        # Store the analysis in the session for display
        request.session['member_analysis'] = analysis

        messages.success(request, "Member responses analyzed successfully.")
    except Exception as e:
        messages.error(request, f"Error analyzing member responses: {str(e)}")

    # Redirect to the member dashboard
    return redirect('groups:view_member_dashboard', org_pk=org_pk, member_pk=member_pk)
