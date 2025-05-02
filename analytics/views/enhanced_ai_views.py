"""
Enhanced views for AI analysis using the Gemini API.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings
from surveys.models import Questionnaire, Question
from feedback.models import Response, Answer, AIAnalysis
from analytics.models import AIModel, AIAnalysisResult, AIInsight
from analytics.services.enhanced_gemini_service import EnhancedGeminiService
import json
import logging
import tempfile
import os
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np

# Set up logger
logger = logging.getLogger(__name__)

@login_required
def enhanced_ai_analysis(request, response_id):
    """
    Generate enhanced AI analysis for a specific response
    """
    response = get_object_or_404(Response, id=response_id)
    questionnaire = response.survey

    # Check if user has permission to view this response
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to view this response.")
        return redirect('dashboard:index')

    # Get all answers for this response
    answers = Answer.objects.filter(response=response)

    # Check if AI analysis already exists
    existing_analysis = AIAnalysis.objects.filter(response=response).first()

    # Generate visualization charts if analysis exists
    answer_distribution_chart = None
    sentiment_analysis_chart = None
    completion_time_chart = None
    keywords_chart = None
    radar_chart = None

    if existing_analysis:
        # Import visualization utilities
        from analytics.utils.response_visualizations import (
            generate_response_answer_distribution,
            generate_response_sentiment_analysis,
            generate_response_completion_time_comparison,
            generate_ai_keywords_chart,
            generate_response_radar_chart
        )

        # Generate charts
        answer_distribution_chart = generate_response_answer_distribution(response_id)
        sentiment_analysis_chart = generate_response_sentiment_analysis(response_id)
        completion_time_chart = generate_response_completion_time_comparison(response_id)
        keywords_chart = generate_ai_keywords_chart(response_id)
        radar_chart = generate_response_radar_chart(response_id)

    context = {
        'response': response,
        'questionnaire': questionnaire,
        'answers': answers,
        'existing_analysis': existing_analysis,
        'answer_distribution_chart': answer_distribution_chart,
        'sentiment_analysis_chart': sentiment_analysis_chart,
        'completion_time_chart': completion_time_chart,
        'keywords_chart': keywords_chart,
        'radar_chart': radar_chart,
    }

    return render(request, 'analytics/ai/enhanced_analysis.html', context)

@login_required
@require_POST
def generate_enhanced_analysis(request, response_id):
    """
    Generate enhanced AI analysis for a specific response using Gemini API
    """
    response_obj = get_object_or_404(Response, id=response_id)
    questionnaire = response_obj.survey

    # Check if user has permission
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        return JsonResponse({'error': "You don't have permission to analyze this response."}, status=403)

    try:
        # Get all answers for this response
        answers = Answer.objects.filter(response=response_obj)

        # Prepare response data for analysis
        response_data = {
            'id': str(response_obj.id),
            'patient_name': response_obj.patient_name,
            'patient_email': response_obj.patient_email,
            'patient_age': response_obj.patient_age,
            'patient_gender': response_obj.patient_gender,
            'score': response_obj.score,
            'risk_level': response_obj.risk_level,
            'status': response_obj.status,
            'completion_time': response_obj.completion_time,
            'created_at': response_obj.created_at.isoformat(),
            'answers': []
        }

        # Add answers to response data
        for answer in answers:
            answer_data = {
                'question_id': str(answer.question.id),
                'question_text': answer.question.text,
                'question_type': answer.question.question_type,
                'text_answer': answer.text_answer,
                'value': answer.value
            }

            if answer.selected_choice:
                answer_data['selected_choice'] = {
                    'id': str(answer.selected_choice.id),
                    'text': answer.selected_choice.text,
                    'score': answer.selected_choice.score
                }

            response_data['answers'].append(answer_data)

        # Prepare questionnaire info
        questionnaire_info = {
            'id': str(questionnaire.id),
            'title': questionnaire.title,
            'description': questionnaire.description,
            'category': questionnaire.category,
            'estimated_time': questionnaire.estimated_time,
            'version': questionnaire.version,
            'language': questionnaire.language,
            'tags': questionnaire.tags
        }

        # Get scoring config
        from surveys.models import ScoringConfig
        scoring_config = ScoringConfig.objects.filter(survey=questionnaire, is_active=True).first()

        if scoring_config:
            questionnaire_info['scoring'] = {
                'name': scoring_config.name,
                'description': scoring_config.description,
                'scoring_method': scoring_config.scoring_method,
                'max_score': scoring_config.max_score,
                'passing_score': scoring_config.passing_score,
                'rules': scoring_config.rules
            }

        # Initialize Gemini service
        gemini_service = EnhancedGeminiService(api_key=settings.GEMINI_API_KEY)

        # Generate analysis
        analysis_result = gemini_service.analyze_response(response_data, questionnaire_info)

        if 'error' in analysis_result:
            return JsonResponse({'error': analysis_result['error']}, status=500)

        # Get or create AI model
        ai_model, created = AIModel.objects.get_or_create(
            name="Gemini Pro Enhanced",
            defaults={
                'description': "Enhanced Google Gemini Pro AI model for sophisticated clinical analysis",
                'model_type': "nlp",
                'version': "1.5",
                'is_active': True
            }
        )

        # Create or update AI analysis
        ai_analysis, created = AIAnalysis.objects.update_or_create(
            response=response_obj,
            defaults={
                'summary': analysis_result.get('summary', ''),
                'detailed_analysis': analysis_result.get('detailed_analysis', ''),
                'recommendations': analysis_result.get('recommendations', ''),
                'insights': {
                    'key_points': [insight.get('title', '') for insight in analysis_result.get('key_insights', [])],
                    'risk_factors': analysis_result.get('risk_assessment', '').split('\n') if isinstance(analysis_result.get('risk_assessment', ''), str) else [],
                    'protective_factors': []
                },
                'model_used': "Gemini Pro Enhanced",
                'confidence_score': analysis_result.get('confidence', 0.85)
            }
        )

        # Create AI analysis result
        AIAnalysisResult.objects.update_or_create(
            response=response_obj,
            ai_model=ai_model,
            defaults={
                'result_data': analysis_result,
                'summary': analysis_result.get('summary', ''),
                'confidence_score': analysis_result.get('confidence', 0.85)
            }
        )

        # Create AI insights
        for insight in analysis_result.get('key_insights', []):
            AIInsight.objects.create(
                questionnaire=questionnaire,
                response=response_obj,
                title=insight.get('title', ''),
                description=insight.get('description', ''),
                source='gemini',
                confidence_score=analysis_result.get('confidence', 0.85),
                is_archived=False,
                created_by=request.user
            )

        return JsonResponse({
            'success': True,
            'analysis': {
                'id': ai_analysis.id,
                'summary': ai_analysis.summary,
                'detailed_analysis': ai_analysis.detailed_analysis,
                'recommendations': ai_analysis.recommendations,
                'insights': ai_analysis.insights,
                'confidence_score': ai_analysis.confidence_score
            }
        })

    except Exception as e:
        logger.error(f"Error generating enhanced analysis: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def batch_analysis(request, questionnaire_id):
    """
    Analyze multiple responses for a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)

    # Check if user has permission
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to analyze this questionnaire's responses.")
        return redirect('dashboard:index')

    # Get responses for this questionnaire
    responses = Response.objects.filter(survey=questionnaire, status='completed')

    context = {
        'questionnaire': questionnaire,
        'response_count': responses.count()
    }

    return render(request, 'analytics/ai/batch_analysis.html', context)

@login_required
@require_POST
def generate_batch_analysis(request, questionnaire_id):
    """
    Generate batch analysis for multiple responses using Gemini API
    """
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)

    # Check if user has permission
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        return JsonResponse({'error': "You don't have permission to analyze this questionnaire's responses."}, status=403)

    try:
        # Get limit parameter (default to 20)
        limit = int(request.POST.get('limit', 20))

        # Get responses for this questionnaire
        responses = Response.objects.filter(
            survey=questionnaire,
            status='completed'
        ).order_by('-created_at')[:limit]

        if not responses.exists():
            return JsonResponse({'error': "No completed responses found for this questionnaire."}, status=404)

        # Prepare response data for analysis
        responses_data = []

        for response_obj in responses:
            # Get answers for this response
            answers = Answer.objects.filter(response=response_obj)

            response_data = {
                'id': str(response_obj.id),
                'patient_name': response_obj.patient_name,
                'patient_email': response_obj.patient_email,
                'patient_age': response_obj.patient_age,
                'patient_gender': response_obj.patient_gender,
                'score': response_obj.score,
                'risk_level': response_obj.risk_level,
                'status': response_obj.status,
                'completion_time': response_obj.completion_time,
                'created_at': response_obj.created_at.isoformat(),
                'answers': []
            }

            # Add answers to response data
            for answer in answers:
                answer_data = {
                    'question_id': str(answer.question.id),
                    'question_text': answer.question.text,
                    'question_type': answer.question.question_type,
                    'text_answer': answer.text_answer,
                    'value': answer.value
                }

                if answer.selected_choice:
                    answer_data['selected_choice'] = {
                        'id': str(answer.selected_choice.id),
                        'text': answer.selected_choice.text,
                        'score': answer.selected_choice.score
                    }

                response_data['answers'].append(answer_data)

            responses_data.append(response_data)

        # Prepare questionnaire info
        questionnaire_info = {
            'id': str(questionnaire.id),
            'title': questionnaire.title,
            'description': questionnaire.description,
            'category': questionnaire.category,
            'estimated_time': questionnaire.estimated_time,
            'version': questionnaire.version,
            'language': questionnaire.language,
            'tags': questionnaire.tags
        }

        # Get scoring config
        from surveys.models import ScoringConfig
        scoring_config = ScoringConfig.objects.filter(survey=questionnaire, is_active=True).first()

        if scoring_config:
            questionnaire_info['scoring'] = {
                'name': scoring_config.name,
                'description': scoring_config.description,
                'scoring_method': scoring_config.scoring_method,
                'max_score': scoring_config.max_score,
                'passing_score': scoring_config.passing_score,
                'rules': scoring_config.rules
            }

        # Initialize Gemini service
        gemini_service = EnhancedGeminiService(api_key=settings.GEMINI_API_KEY)

        # Generate batch analysis
        analysis_result = gemini_service.analyze_multiple_responses(responses_data, questionnaire_info)

        if 'error' in analysis_result:
            return JsonResponse({'error': analysis_result['error']}, status=500)

        # Get or create AI model
        ai_model, created = AIModel.objects.get_or_create(
            name="Gemini Pro Batch Analysis",
            defaults={
                'description': "Google Gemini Pro AI model for batch analysis of multiple responses",
                'model_type': "nlp",
                'version': "1.5",
                'is_active': True
            }
        )

        # Create AI insights from batch analysis
        insights_created = []

        # Create a general insight for the batch analysis
        batch_insight = AIInsight.objects.create(
            questionnaire=questionnaire,
            response=None,  # Batch analysis doesn't apply to a specific response
            title=f"Batch Analysis of {len(responses_data)} Responses",
            description=analysis_result.get('summary', ''),
            source='gemini_batch',
            confidence_score=analysis_result.get('confidence', 0.85),
            is_archived=False,
            created_by=request.user,
            metadata={
                'response_count': len(responses_data),
                'analysis_timestamp': timezone.now().isoformat(),
                'pattern_analysis': analysis_result.get('pattern_analysis', ''),
                'demographic_insights': analysis_result.get('demographic_insights', ''),
                'risk_distribution': analysis_result.get('risk_distribution', ''),
                'statistical_summary': analysis_result.get('statistical_summary', '')
            }
        )

        insights_created.append({
            'id': batch_insight.id,
            'title': batch_insight.title,
            'description': batch_insight.description
        })

        # Create individual insights from key insights
        for insight in analysis_result.get('key_insights', []):
            insight_obj = AIInsight.objects.create(
                questionnaire=questionnaire,
                response=None,  # Batch insights don't apply to a specific response
                title=insight.get('title', ''),
                description=insight.get('description', ''),
                source='gemini_batch',
                confidence_score=analysis_result.get('confidence', 0.85),
                is_archived=False,
                created_by=request.user,
                metadata={
                    'supporting_data': insight.get('supporting_data', ''),
                    'response_count': len(responses_data),
                    'analysis_timestamp': timezone.now().isoformat()
                }
            )

            insights_created.append({
                'id': insight_obj.id,
                'title': insight_obj.title,
                'description': insight_obj.description
            })

        return JsonResponse({
            'success': True,
            'analysis': {
                'summary': analysis_result.get('summary', ''),
                'pattern_analysis': analysis_result.get('pattern_analysis', ''),
                'demographic_insights': analysis_result.get('demographic_insights', ''),
                'risk_distribution': analysis_result.get('risk_distribution', ''),
                'recommendations': analysis_result.get('recommendations', ''),
                'statistical_summary': analysis_result.get('statistical_summary', ''),
                'confidence': analysis_result.get('confidence', 0.85)
            },
            'insights_created': insights_created,
            'response_count': len(responses_data)
        })

    except Exception as e:
        logger.error(f"Error generating batch analysis: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def visualization_recommendations(request, questionnaire_id):
    """
    Generate visualization recommendations for a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)

    # Check if user has permission
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to analyze this questionnaire.")
        return redirect('dashboard:index')

    # Get responses for this questionnaire
    responses = Response.objects.filter(survey=questionnaire, status='completed')

    context = {
        'questionnaire': questionnaire,
        'response_count': responses.count()
    }

    return render(request, 'analytics/ai/visualization_recommendations.html', context)

@login_required
@require_POST
def generate_visualization_recommendations(request, questionnaire_id):
    """
    Generate visualization recommendations using Gemini API
    """
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)

    # Check if user has permission
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        return JsonResponse({'error': "You don't have permission to analyze this questionnaire."}, status=403)

    try:
        # Get responses for this questionnaire
        responses = Response.objects.filter(
            survey=questionnaire,
            status='completed'
        ).order_by('-created_at')[:20]  # Limit to 20 most recent responses

        if not responses.exists():
            return JsonResponse({'error': "No completed responses found for this questionnaire."}, status=404)

        # Prepare response data
        responses_data = []

        for response_obj in responses:
            # Get answers for this response
            answers = Answer.objects.filter(response=response_obj)

            response_data = {
                'id': str(response_obj.id),
                'patient_age': response_obj.patient_age,
                'patient_gender': response_obj.patient_gender,
                'score': response_obj.score,
                'risk_level': response_obj.risk_level,
                'completion_time': response_obj.completion_time,
                'created_at': response_obj.created_at.isoformat(),
                'answers': []
            }

            # Add answers to response data
            for answer in answers:
                answer_data = {
                    'question_id': str(answer.question.id),
                    'question_text': answer.question.text,
                    'question_type': answer.question.question_type,
                    'value': answer.value
                }

                if answer.selected_choice:
                    answer_data['selected_choice'] = {
                        'text': answer.selected_choice.text,
                        'score': answer.selected_choice.score
                    }

                response_data['answers'].append(answer_data)

            responses_data.append(response_data)

        # Prepare questionnaire info
        questionnaire_info = {
            'id': str(questionnaire.id),
            'title': questionnaire.title,
            'description': questionnaire.description,
            'category': questionnaire.category,
            'questions': [
                {
                    'id': str(q.id),
                    'text': q.text,
                    'question_type': q.question_type,
                    'is_scored': q.is_scored
                } for q in Question.objects.filter(survey=questionnaire).order_by('order')
            ]
        }

        # Get scoring config
        from surveys.models import ScoringConfig
        scoring_config = ScoringConfig.objects.filter(survey=questionnaire, is_active=True).first()

        if scoring_config:
            questionnaire_info['scoring'] = {
                'name': scoring_config.name,
                'scoring_method': scoring_config.scoring_method,
                'max_score': scoring_config.max_score,
                'rules': scoring_config.rules
            }

        # Initialize Gemini service
        gemini_service = EnhancedGeminiService(api_key=settings.GEMINI_API_KEY)

        # Generate visualization recommendations
        recommendations = gemini_service.generate_visualization_recommendations(
            {'responses': responses_data},
            questionnaire_info
        )

        if 'error' in recommendations:
            return JsonResponse({'error': recommendations['error']}, status=500)

        return JsonResponse({
            'success': True,
            'recommendations': recommendations
        })

    except Exception as e:
        logger.error(f"Error generating visualization recommendations: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def generate_report(request, response_id):
    """
    Generate a comprehensive clinical report for a response
    """
    response_obj = get_object_or_404(Response, id=response_id)
    questionnaire = response_obj.survey

    # Check if user has permission
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to generate a report for this response.")
        return redirect('dashboard:index')

    # Get AI analysis for this response
    ai_analysis = AIAnalysis.objects.filter(response=response_obj).first()

    if not ai_analysis:
        messages.error(request, "AI analysis must be generated before creating a report.")
        return redirect('analytics:enhanced_ai_analysis', response_id=response_id)

    # Get all answers for this response
    answers = Answer.objects.filter(response=response_obj)

    context = {
        'response': response_obj,
        'questionnaire': questionnaire,
        'ai_analysis': ai_analysis,
        'answers': answers
    }

    return render(request, 'analytics/ai/generate_report.html', context)

@login_required
@require_POST
def create_report(request, response_id):
    """
    Create a comprehensive clinical report using Gemini API
    """
    response_obj = get_object_or_404(Response, id=response_id)
    questionnaire = response_obj.survey

    # Check if user has permission
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        return JsonResponse({'error': "You don't have permission to generate a report for this response."}, status=403)

    try:
        # Get AI analysis for this response
        ai_analysis = AIAnalysis.objects.filter(response=response_obj).first()

        if not ai_analysis:
            return JsonResponse({'error': "AI analysis must be generated before creating a report."}, status=400)

        # Get all answers for this response
        answers = Answer.objects.filter(response=response_obj)

        # Prepare response data
        response_data = {
            'id': str(response_obj.id),
            'patient_name': response_obj.patient_name,
            'patient_email': response_obj.patient_email,
            'patient_age': response_obj.patient_age,
            'patient_gender': response_obj.patient_gender,
            'score': response_obj.score,
            'risk_level': response_obj.risk_level,
            'status': response_obj.status,
            'completion_time': response_obj.completion_time,
            'created_at': response_obj.created_at.isoformat(),
            'answers': []
        }

        # Add answers to response data
        for answer in answers:
            answer_data = {
                'question_id': str(answer.question.id),
                'question_text': answer.question.text,
                'question_type': answer.question.question_type,
                'text_answer': answer.text_answer,
                'value': answer.value
            }

            if answer.selected_choice:
                answer_data['selected_choice'] = {
                    'id': str(answer.selected_choice.id),
                    'text': answer.selected_choice.text,
                    'score': answer.selected_choice.score
                }

            response_data['answers'].append(answer_data)

        # Prepare analysis data
        analysis_data = {
            'summary': ai_analysis.summary,
            'detailed_analysis': ai_analysis.detailed_analysis,
            'recommendations': ai_analysis.recommendations,
            'insights': ai_analysis.insights,
            'confidence_score': ai_analysis.confidence_score,
            'model_used': ai_analysis.model_used
        }

        # Prepare questionnaire info
        questionnaire_info = {
            'id': str(questionnaire.id),
            'title': questionnaire.title,
            'description': questionnaire.description,
            'category': questionnaire.category,
            'estimated_time': questionnaire.estimated_time,
            'version': questionnaire.version,
            'language': questionnaire.language,
            'tags': questionnaire.tags
        }

        # Get scoring config
        from surveys.models import ScoringConfig
        scoring_config = ScoringConfig.objects.filter(survey=questionnaire, is_active=True).first()

        if scoring_config:
            questionnaire_info['scoring'] = {
                'name': scoring_config.name,
                'description': scoring_config.description,
                'scoring_method': scoring_config.scoring_method,
                'max_score': scoring_config.max_score,
                'passing_score': scoring_config.passing_score,
                'rules': scoring_config.rules
            }

        # Initialize Gemini service
        gemini_service = EnhancedGeminiService(api_key=settings.GEMINI_API_KEY)

        # Generate report
        report = gemini_service.generate_report(response_data, analysis_data, questionnaire_info)

        if 'error' in report:
            return JsonResponse({'error': report['error']}, status=500)

        # Save report to database
        from analytics.models import Report

        report_obj = Report.objects.create(
            response=response_obj,
            questionnaire=questionnaire,
            title=f"Clinical Report - {questionnaire.title}",
            content=json.dumps(report),
            format='json',
            generated_by=request.user,
            is_archived=False
        )

        # Generate PDF version of the report
        try:
            from analytics.utils.pdf_generator import generate_clinical_report_pdf

            # Generate PDF
            pdf_data = generate_clinical_report_pdf(
                report_data=report,
                response_data=response_obj,
                questionnaire_data=questionnaire,
                user_data=request.user
            )

            # Save PDF to report object
            report_obj.pdf_file.save(
                f"clinical_report_{response_obj.id}.pdf",
                ContentFile(pdf_data),
                save=True
            )
        except Exception as pdf_error:
            logger.error(f"Error generating PDF: {str(pdf_error)}")
            # Continue without PDF if there's an error

        return JsonResponse({
            'success': True,
            'report': {
                'id': report_obj.id,
                'title': report_obj.title,
                'content': report,
                'created_at': report_obj.created_at.isoformat(),
                'has_pdf': bool(report_obj.pdf_file)
            }
        })

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def send_analysis_email(request, response_id):
    """
    Send AI analysis via email
    """
    response_obj = get_object_or_404(Response, id=response_id)
    questionnaire = response_obj.survey

    # Check if user has permission
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        return JsonResponse({'error': "You don't have permission to send emails for this response."}, status=403)

    try:
        # Get AI analysis for this response
        ai_analysis = AIAnalysis.objects.filter(response=response_obj).first()

        if not ai_analysis:
            return JsonResponse({'error': "AI analysis must be generated before sending an email."}, status=400)

        # Get form data
        recipient_email = request.POST.get('recipient_email')
        subject = request.POST.get('subject', f"AI Analysis Report - {questionnaire.title}")
        message = request.POST.get('message', '')
        include_charts = request.POST.get('include_charts') == 'true'
        include_pdf = request.POST.get('include_pdf') == 'true'

        if not recipient_email:
            return JsonResponse({'error': "Recipient email is required."}, status=400)

        # Get all answers for this response
        answers = Answer.objects.filter(response=response_obj)

        # Generate visualization charts if requested
        charts = {}
        if include_charts:
            from analytics.utils.response_visualizations import (
                generate_response_answer_distribution,
                generate_response_sentiment_analysis,
                generate_response_completion_time_comparison,
                generate_ai_keywords_chart,
                generate_response_radar_chart
            )

            charts = {
                'answer_distribution': generate_response_answer_distribution(response_id),
                'sentiment_analysis': generate_response_sentiment_analysis(response_id),
                'completion_time': generate_response_completion_time_comparison(response_id),
                'keywords': generate_ai_keywords_chart(response_id),
                'radar': generate_response_radar_chart(response_id)
            }

        # Prepare context for email template
        context = {
            'response': response_obj,
            'questionnaire': questionnaire,
            'answers': answers,
            'analysis': ai_analysis,
            'charts': charts,
            'message': message,
            'sender_name': request.user.get_full_name() or request.user.username,
            'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        # Render email templates
        html_content = render_to_string('analytics/email/analysis_email.html', context)
        text_content = strip_tags(html_content)

        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )

        # Attach HTML content
        email.attach_alternative(html_content, "text/html")

        # Attach PDF if requested
        if include_pdf:
            # Check if a report with PDF exists
            from analytics.models import Report
            report = Report.objects.filter(response=response_obj).order_by('-created_at').first()

            if report and report.pdf_file:
                email.attach(
                    f"analysis_report_{response_obj.id}.pdf",
                    report.pdf_file.read(),
                    'application/pdf'
                )
            else:
                # Generate a PDF on the fly
                try:
                    from analytics.utils.pdf_generator import generate_clinical_report_pdf

                    # Prepare report data
                    report_data = {
                        'executive_summary': ai_analysis.summary,
                        'clinical_interpretation': ai_analysis.detailed_analysis,
                        'recommendations': ai_analysis.recommendations,
                        'key_findings': ai_analysis.insights.get('key_points', []) if ai_analysis.insights else [],
                        'suggested_interventions': ai_analysis.insights.get('recommendations', []) if ai_analysis.insights else [],
                        'follow_up_plan': ai_analysis.insights.get('follow_up', '') if ai_analysis.insights else '',
                        'answers': [
                            {
                                'question_text': answer.question.text,
                                'text_answer': answer.text_answer,
                                'value': answer.value,
                                'selected_choice': {
                                    'text': answer.selected_choice.text,
                                    'score': answer.selected_choice.score
                                } if answer.selected_choice else None
                            } for answer in answers
                        ],
                        'model_used': ai_analysis.model_used,
                        'confidence_score': ai_analysis.confidence_score
                    }

                    # Generate PDF
                    pdf_data = generate_clinical_report_pdf(
                        report_data=report_data,
                        response_data=response_obj,
                        questionnaire_data=questionnaire,
                        user_data=request.user
                    )

                    # Attach PDF to email
                    email.attach(
                        f"analysis_report_{response_obj.id}.pdf",
                        pdf_data,
                        'application/pdf'
                    )
                except Exception as pdf_error:
                    logger.error(f"Error generating PDF for email: {str(pdf_error)}")
                    # Continue without PDF if there's an error

        # Send email
        email.send()

        return JsonResponse({'success': True})

    except Exception as e:
        logger.error(f"Error sending analysis email: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
