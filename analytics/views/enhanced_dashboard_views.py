"""
Enhanced views for analytics dashboards with data visualization.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Sum, Q, F
from django.http import HttpResponse
from django.utils import timezone
from surveys.models import Questionnaire, Question
from feedback.models import Response, Answer, AIAnalysis
from analytics.models import AIInsight
from analytics.utils.chart_generators import (
    generate_response_distribution_chart,
    generate_score_distribution_chart,
    generate_response_trend_chart,
    generate_question_response_chart,
    generate_ai_sentiment_chart,
    generate_ai_recommendations_chart,
    generate_demographic_analysis_chart,
    generate_completion_time_chart,
    generate_comparative_analysis_chart
)
import csv
import io
import zipfile
from datetime import datetime, timedelta

@login_required
def questionnaire_dashboard(request, questionnaire_id):
    """
    Display a dashboard with analytics for a specific questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    
    # Check if user has permission to view this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to view this questionnaire's analytics.")
        return redirect('dashboard:index')
    
    # Get responses for this questionnaire
    responses = Response.objects.filter(survey=questionnaire)
    total_responses = responses.count()
    
    # Calculate statistics
    completed_responses = responses.filter(status='completed')
    completion_rate = (completed_responses.count() / total_responses * 100) if total_responses > 0 else 0
    
    # Calculate average score
    responses_with_scores = responses.exclude(score__isnull=True)
    avg_score = responses_with_scores.aggregate(avg=Avg('score'))['avg'] or 0
    
    # Calculate high risk percentage
    high_risk_responses = responses.filter(risk_level__in=['high', 'critical']).count()
    high_risk_percentage = (high_risk_responses / total_responses * 100) if total_responses > 0 else 0
    
    # Generate charts
    risk_distribution_chart = generate_response_distribution_chart(questionnaire_id)
    score_distribution_chart = generate_score_distribution_chart(questionnaire_id)
    response_trend_chart = generate_response_trend_chart(questionnaire_id)
    completion_time_chart = generate_completion_time_chart(questionnaire_id)
    
    # Get other questionnaires in the same category for comparison
    similar_questionnaires = Questionnaire.objects.filter(
        category=questionnaire.category
    ).exclude(id=questionnaire_id)[:5]
    
    if similar_questionnaires.exists():
        comparative_analysis_chart = generate_comparative_analysis_chart(
            [questionnaire_id] + [q.id for q in similar_questionnaires]
        )
    else:
        comparative_analysis_chart = None
    
    # Generate charts for each question
    questions = Question.objects.filter(survey=questionnaire).order_by('order')
    question_charts = []
    
    for question in questions:
        if question.question_type in ['single_choice', 'multiple_choice', 'scale']:
            chart = generate_question_response_chart(question.id)
            question_charts.append({
                'question': question,
                'chart': chart
            })
    
    # Generate demographic charts
    age_distribution_chart = generate_demographic_analysis_chart(questionnaire_id, 'patient_age')
    gender_distribution_chart = generate_demographic_analysis_chart(questionnaire_id, 'patient_gender')
    
    # Generate AI analysis charts
    sentiment_chart = generate_ai_sentiment_chart(questionnaire_id)
    recommendations_chart = generate_ai_recommendations_chart(questionnaire_id)
    
    # Get AI insights
    ai_insights = AIInsight.objects.filter(
        questionnaire=questionnaire,
        is_archived=False
    ).order_by('-created_at')[:10]
    
    context = {
        'questionnaire': questionnaire,
        'total_responses': total_responses,
        'completion_rate': completion_rate,
        'avg_score': avg_score,
        'high_risk_percentage': high_risk_percentage,
        'risk_distribution_chart': risk_distribution_chart,
        'score_distribution_chart': score_distribution_chart,
        'response_trend_chart': response_trend_chart,
        'completion_time_chart': completion_time_chart,
        'comparative_analysis_chart': comparative_analysis_chart,
        'question_charts': question_charts,
        'age_distribution_chart': age_distribution_chart,
        'gender_distribution_chart': gender_distribution_chart,
        'sentiment_chart': sentiment_chart,
        'recommendations_chart': recommendations_chart,
        'ai_insights': ai_insights,
    }
    
    return render(request, 'analytics/dashboard/questionnaire_dashboard.html', context)

@login_required
def user_dashboard(request, user_id=None):
    """
    Display a dashboard with analytics for a specific user or the current user
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # If user_id is not provided, use the current user
    if user_id is None:
        user = request.user
    else:
        user = get_object_or_404(User, id=user_id)
        
        # Check if the current user has permission to view this user's dashboard
        if user != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to view this user's dashboard.")
            return redirect('dashboard:index')
    
    # Get responses for this user
    responses = Response.objects.filter(user=user)
    
    # Get questionnaires this user has responded to
    questionnaires = Questionnaire.objects.filter(responses__user=user).distinct()
    
    # Calculate statistics
    total_responses = responses.count()
    completed_responses = responses.filter(status='completed').count()
    completion_rate = (completed_responses / total_responses * 100) if total_responses > 0 else 0
    
    # Calculate average scores by questionnaire
    questionnaire_stats = []
    
    for questionnaire in questionnaires:
        q_responses = responses.filter(survey=questionnaire)
        q_responses_with_scores = q_responses.exclude(score__isnull=True)
        
        if q_responses_with_scores.exists():
            avg_score = q_responses_with_scores.aggregate(avg=Avg('score'))['avg'] or 0
            latest_score = q_responses_with_scores.order_by('-created_at').first().score
            
            # Get scoring config to determine risk level
            from surveys.models import ScoringConfig
            scoring_config = ScoringConfig.objects.filter(survey=questionnaire, is_active=True).first()
            
            risk_level = "Unknown"
            if scoring_config and scoring_config.rules:
                for rule in scoring_config.rules:
                    if rule['min'] <= latest_score <= rule['max']:
                        risk_level = rule['label']
                        break
            
            questionnaire_stats.append({
                'questionnaire': questionnaire,
                'responses': q_responses.count(),
                'avg_score': avg_score,
                'latest_score': latest_score,
                'risk_level': risk_level
            })
    
    # Sort by most recent response
    questionnaire_stats.sort(key=lambda x: x['questionnaire'].responses.filter(user=user).order_by('-created_at').first().created_at, reverse=True)
    
    context = {
        'user_profile': user,
        'total_responses': total_responses,
        'completion_rate': completion_rate,
        'questionnaire_stats': questionnaire_stats,
    }
    
    return render(request, 'analytics/dashboard/user_dashboard.html', context)

@login_required
def organization_dashboard(request, organization_id):
    """
    Display a dashboard with analytics for a specific organization
    """
    from groups.models import Organization
    
    organization = get_object_or_404(Organization, id=organization_id)
    
    # Check if user has permission to view this organization's dashboard
    if not organization.members.filter(user=request.user).exists() and not request.user.is_staff:
        messages.error(request, "You don't have permission to view this organization's dashboard.")
        return redirect('dashboard:index')
    
    # Get questionnaires for this organization
    questionnaires = Questionnaire.objects.filter(organization=organization)
    
    # Get responses for these questionnaires
    responses = Response.objects.filter(survey__in=questionnaires)
    
    # Calculate statistics
    total_questionnaires = questionnaires.count()
    total_responses = responses.count()
    
    # Calculate response statistics by questionnaire
    questionnaire_stats = []
    
    for questionnaire in questionnaires:
        q_responses = responses.filter(survey=questionnaire)
        q_responses_with_scores = q_responses.exclude(score__isnull=True)
        
        if q_responses.exists():
            avg_score = q_responses_with_scores.aggregate(avg=Avg('score'))['avg'] or 0
            
            # Calculate risk level distribution
            risk_distribution = q_responses.values('risk_level').annotate(count=Count('id'))
            risk_levels = {item['risk_level']: item['count'] for item in risk_distribution}
            
            questionnaire_stats.append({
                'questionnaire': questionnaire,
                'responses': q_responses.count(),
                'avg_score': avg_score,
                'risk_levels': risk_levels
            })
    
    # Sort by number of responses
    questionnaire_stats.sort(key=lambda x: x['responses'], reverse=True)
    
    context = {
        'organization': organization,
        'total_questionnaires': total_questionnaires,
        'total_responses': total_responses,
        'questionnaire_stats': questionnaire_stats,
    }
    
    return render(request, 'analytics/dashboard/organization_dashboard.html', context)

@login_required
def export_dashboard(request, questionnaire_id):
    """
    Export dashboard data and charts for a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    
    # Check if user has permission to export this questionnaire's data
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to export this questionnaire's data.")
        return redirect('analytics:questionnaire_dashboard', questionnaire_id=questionnaire_id)
    
    # Create a ZIP file in memory
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Export response data as CSV
        responses = Response.objects.filter(survey=questionnaire)
        
        # Create CSV file for responses
        response_csv = io.StringIO()
        writer = csv.writer(response_csv)
        
        # Write header row
        writer.writerow([
            'Response ID', 'Patient Name', 'Patient Email', 'Patient Age', 'Patient Gender',
            'Score', 'Risk Level', 'Completion Time (seconds)', 'Status', 'Created At'
        ])
        
        # Write data rows
        for response in responses:
            writer.writerow([
                response.id,
                response.patient_name,
                response.patient_email,
                response.patient_age,
                response.patient_gender,
                response.score,
                response.risk_level,
                response.completion_time,
                response.status,
                response.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # Add CSV to ZIP
        zip_file.writestr('responses.csv', response_csv.getvalue())
        
        # Export answers as CSV
        answers = Answer.objects.filter(response__survey=questionnaire)
        
        # Create CSV file for answers
        answer_csv = io.StringIO()
        writer = csv.writer(answer_csv)
        
        # Write header row
        writer.writerow([
            'Response ID', 'Question ID', 'Question Text', 'Answer Value', 'Selected Choice'
        ])
        
        # Write data rows
        for answer in answers:
            writer.writerow([
                answer.response.id,
                answer.question.id,
                answer.question.text,
                answer.text_answer or (answer.value if isinstance(answer.value, str) else str(answer.value)),
                answer.selected_choice.text if answer.selected_choice else ''
            ])
        
        # Add CSV to ZIP
        zip_file.writestr('answers.csv', answer_csv.getvalue())
        
        # Export AI analyses as CSV
        analyses = AIAnalysis.objects.filter(response__survey=questionnaire)
        
        # Create CSV file for AI analyses
        analysis_csv = io.StringIO()
        writer = csv.writer(analysis_csv)
        
        # Write header row
        writer.writerow([
            'Response ID', 'Summary', 'Detailed Analysis', 'Recommendations', 'Confidence Score'
        ])
        
        # Write data rows
        for analysis in analyses:
            writer.writerow([
                analysis.response.id,
                analysis.summary,
                analysis.detailed_analysis,
                analysis.recommendations,
                analysis.confidence_score
            ])
        
        # Add CSV to ZIP
        zip_file.writestr('ai_analyses.csv', analysis_csv.getvalue())
        
        # Generate and add charts
        # Risk distribution chart
        risk_chart = generate_response_distribution_chart(questionnaire_id)
        if risk_chart:
            import base64
            risk_chart_data = base64.b64decode(risk_chart)
            zip_file.writestr('charts/risk_distribution.png', risk_chart_data)
        
        # Score distribution chart
        score_chart = generate_score_distribution_chart(questionnaire_id)
        if score_chart:
            score_chart_data = base64.b64decode(score_chart)
            zip_file.writestr('charts/score_distribution.png', score_chart_data)
        
        # Response trend chart
        trend_chart = generate_response_trend_chart(questionnaire_id)
        if trend_chart:
            trend_chart_data = base64.b64decode(trend_chart)
            zip_file.writestr('charts/response_trend.png', trend_chart_data)
        
        # AI sentiment chart
        sentiment_chart = generate_ai_sentiment_chart(questionnaire_id)
        if sentiment_chart:
            sentiment_chart_data = base64.b64decode(sentiment_chart)
            zip_file.writestr('charts/ai_sentiment.png', sentiment_chart_data)
        
        # AI recommendations chart
        recommendations_chart = generate_ai_recommendations_chart(questionnaire_id)
        if recommendations_chart:
            recommendations_chart_data = base64.b64decode(recommendations_chart)
            zip_file.writestr('charts/ai_recommendations.png', recommendations_chart_data)
    
    # Prepare response
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{questionnaire.title}_dashboard_export.zip"'
    
    return response
