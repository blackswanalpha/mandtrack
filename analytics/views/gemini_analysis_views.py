from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, Q

from surveys.models import Questionnaire, Question
from feedback.models import Response, Answer
from analytics.models import AIModel, AIAnalysisResult, AIInsight
from analytics.services.gemini_service import GeminiService

import json
import pandas as pd
from collections import defaultdict

@login_required
def gemini_analysis_dashboard(request):
    """
    Display the Gemini AI analysis dashboard
    """
    # Get questionnaires the user has access to
    if request.user.is_staff:
        questionnaires = Questionnaire.objects.all()
    else:
        # Get questionnaires created by the user
        user_questionnaires = Questionnaire.objects.filter(created_by=request.user)

        # Get questionnaires from organizations the user is a member of
        org_memberships = request.user.organization_memberships.filter(is_active=True)
        org_ids = [membership.organization_id for membership in org_memberships]
        org_questionnaires = Questionnaire.objects.filter(organization__in=org_ids)

        # Combine the querysets
        questionnaires = user_questionnaires | org_questionnaires

    # Get recent AI analysis results
    recent_results = AIAnalysisResult.objects.filter(
        analyzed_by=request.user
    ).order_by('-analyzed_at')[:5]

    # Get recent insights
    recent_insights = AIInsight.objects.filter(
        Q(questionnaire__created_by=request.user) |
        Q(questionnaire__organization__members__user=request.user, questionnaire__organization__members__is_active=True)
    ).distinct().order_by('-created_at')[:5]

    context = {
        'questionnaires': questionnaires,
        'recent_results': recent_results,
        'recent_insights': recent_insights,
    }

    return render(request, 'analytics/gemini/dashboard.html', context)

@login_required
def analyze_questionnaire(request, questionnaire_id):
    """
    Analyze a questionnaire using Gemini AI
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)

    # Check if user has permission to view this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is a member of the organization
            if not questionnaire.organization.members.filter(user=request.user, is_active=True).exists():
                messages.error(request, "You don't have permission to analyze this questionnaire.")
                return redirect('analytics:gemini_analysis_dashboard')
        else:
            messages.error(request, "You don't have permission to analyze this questionnaire.")
            return redirect('analytics:gemini_analysis_dashboard')

    if request.method == 'POST':
        analysis_type = request.POST.get('analysis_type')

        if not analysis_type:
            messages.error(request, "Analysis type is required.")
            return redirect('analytics:analyze_questionnaire', questionnaire_id=questionnaire_id)

        # Get responses for this questionnaire
        responses = Response.objects.filter(survey=questionnaire)

        if not responses.exists():
            messages.error(request, "No responses found for this questionnaire.")
            return redirect('analytics:analyze_questionnaire', questionnaire_id=questionnaire_id)

        # Initialize the Gemini service
        gemini_service = GeminiService()

        # Prepare data for analysis
        data = prepare_data_for_analysis(questionnaire, responses)

        # Perform the analysis
        if analysis_type == 'sentiment':
            result = perform_sentiment_analysis(gemini_service, data)
        elif analysis_type == 'themes':
            result = perform_themes_analysis(gemini_service, data)
        elif analysis_type == 'patterns':
            result = perform_patterns_analysis(gemini_service, data)
        elif analysis_type == 'insights':
            result = perform_insights_analysis(gemini_service, data, questionnaire)
        else:
            result = {'error': 'Invalid analysis type'}

        if 'error' in result:
            messages.error(request, f"Error performing analysis: {result['error']}")
            return redirect('analytics:analyze_questionnaire', questionnaire_id=questionnaire_id)

        # Create an AI model if it doesn't exist
        ai_model, created = AIModel.objects.get_or_create(
            name='Gemini Pro',
            defaults={
                'description': 'Google Gemini Pro AI model for text analysis',
                'model_type': 'nlp',
                'version': '1.0',
                'is_active': True,
                'created_by': request.user
            }
        )

        # Create an analysis result
        analysis_result = AIAnalysisResult.objects.create(
            response=responses.first(),  # Just link to the first response for now
            ai_model=ai_model,
            result_data=result,
            summary=result.get('summary', ''),
            confidence_score=result.get('confidence', 0.75),
            analyzed_by=request.user
        )

        # Create insights if available
        if 'key_insights' in result:
            for insight_data in result['key_insights']:
                AIInsight.objects.create(
                    title=insight_data.get('title', 'Untitled Insight'),
                    description=insight_data.get('description', ''),
                    insight_type='pattern',
                    severity='medium',
                    questionnaire=questionnaire,
                    ai_model=ai_model,
                    supporting_data=insight_data.get('supporting_data', {}),
                )

        messages.success(request, "Analysis completed successfully.")
        return redirect('analytics:analysis_result_detail', result_id=analysis_result.id)

    context = {
        'questionnaire': questionnaire,
        'analysis_types': [
            ('sentiment', 'Sentiment Analysis'),
            ('themes', 'Theme Identification'),
            ('patterns', 'Pattern Recognition'),
            ('insights', 'Generate Insights'),
        ],
    }

    return render(request, 'analytics/gemini/analyze_questionnaire.html', context)

@login_required
def analyze_response(request, response_id):
    """
    Analyze a single response using Gemini AI
    """
    response = get_object_or_404(Response, pk=response_id)
    questionnaire = response.survey

    # Check if user has permission to view this response
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is a member of the organization
            if not questionnaire.organization.members.filter(user=request.user, is_active=True).exists():
                messages.error(request, "You don't have permission to analyze this response.")
                return redirect('analytics:gemini_analysis_dashboard')
        else:
            messages.error(request, "You don't have permission to analyze this response.")
            return redirect('analytics:gemini_analysis_dashboard')

    if request.method == 'POST':
        analysis_type = request.POST.get('analysis_type')

        if not analysis_type:
            messages.error(request, "Analysis type is required.")
            return redirect('analytics:analyze_response', response_id=response_id)

        # Initialize the Gemini service
        gemini_service = GeminiService()

        # Prepare data for analysis
        data = prepare_response_for_analysis(response)

        # Perform the analysis
        if analysis_type == 'sentiment':
            result = perform_sentiment_analysis(gemini_service, data)
        elif analysis_type == 'themes':
            result = perform_themes_analysis(gemini_service, data)
        else:
            result = {'error': 'Invalid analysis type'}

        if 'error' in result:
            messages.error(request, f"Error performing analysis: {result['error']}")
            return redirect('analytics:analyze_response', response_id=response_id)

        # Create an AI model if it doesn't exist
        ai_model, created = AIModel.objects.get_or_create(
            name='Gemini Pro',
            defaults={
                'description': 'Google Gemini Pro AI model for text analysis',
                'model_type': 'nlp',
                'version': '1.0',
                'is_active': True,
                'created_by': request.user
            }
        )

        # Create an analysis result
        analysis_result = AIAnalysisResult.objects.create(
            response=response,
            ai_model=ai_model,
            result_data=result,
            summary=result.get('summary', ''),
            confidence_score=result.get('confidence', 0.75),
            analyzed_by=request.user
        )

        messages.success(request, "Analysis completed successfully.")
        return redirect('analytics:analysis_result_detail', result_id=analysis_result.id)

    context = {
        'response': response,
        'questionnaire': questionnaire,
        'analysis_types': [
            ('sentiment', 'Sentiment Analysis'),
            ('themes', 'Theme Identification'),
        ],
    }

    return render(request, 'analytics/gemini/analyze_response.html', context)

@login_required
def analyze_text(request):
    """
    Analyze custom text using Gemini AI
    """
    if request.method == 'POST':
        text = request.POST.get('text')
        analysis_type = request.POST.get('analysis_type')

        if not text or not analysis_type:
            messages.error(request, "Text and analysis type are required.")
            return redirect('analytics:analyze_text')

        # Initialize the Gemini service
        gemini_service = GeminiService()

        # Perform the analysis
        result = gemini_service.analyze_text(text, analysis_type)

        if 'error' in result:
            messages.error(request, f"Error performing analysis: {result['error']}")
            return redirect('analytics:analyze_text')

        # Create an AI model if it doesn't exist
        ai_model, created = AIModel.objects.get_or_create(
            name='Gemini Pro',
            defaults={
                'description': 'Google Gemini Pro AI model for text analysis',
                'model_type': 'nlp',
                'version': '1.0',
                'is_active': True,
                'created_by': request.user
            }
        )

        # Create a dummy response for storing the result
        # In a real application, you might want to create a separate model for text analysis
        dummy_response = Response.objects.create(
            questionnaire=None,
            email=request.user.email,
            user=request.user,
            completed_at=timezone.now()
        )

        # Create an analysis result
        analysis_result = AIAnalysisResult.objects.create(
            response=dummy_response,
            ai_model=ai_model,
            result_data={'text': text, 'analysis': result},
            summary=result.get('summary', ''),
            confidence_score=result.get('confidence', 0.75),
            analyzed_by=request.user
        )

        messages.success(request, "Analysis completed successfully.")
        return redirect('analytics:analysis_result_detail', result_id=analysis_result.id)

    context = {
        'analysis_types': [
            ('general', 'General Analysis'),
            ('sentiment', 'Sentiment Analysis'),
            ('themes', 'Theme Identification'),
            ('summary', 'Text Summarization'),
        ],
    }

    return render(request, 'analytics/gemini/analyze_text.html', context)

def prepare_data_for_analysis(questionnaire, responses):
    """
    Prepare questionnaire and response data for analysis
    """
    # Get all questions for this questionnaire
    questions = Question.objects.filter(survey=questionnaire).order_by('order')

    # Prepare data structure
    data = {
        'questionnaire': {
            'id': str(questionnaire.id),
            'title': questionnaire.title,
            'description': questionnaire.description,
            'questions': []
        },
        'responses': []
    }

    # Add questions
    for question in questions:
        question_data = {
            'id': question.id,
            'text': question.text,
            'type': question.question_type,
            'required': question.required,
            'order': question.order
        }

        # Add choices for choice questions
        if question.question_type in ['single_choice', 'multiple_choice']:
            question_data['choices'] = [
                {'id': choice.id, 'text': choice.text, 'order': choice.order}
                for choice in question.choices.all().order_by('order')
            ]

        data['questionnaire']['questions'].append(question_data)

    # Add responses
    for response in responses:
        response_data = {
            'id': str(response.id),
            'created_at': response.created_at.isoformat(),
            'completed_at': response.completed_at.isoformat() if response.completed_at else None,
            'email': response.email,
            'gender': response.gender,
            'age': response.age,
            'answers': []
        }

        # Add answers
        answers = Answer.objects.filter(response=response)
        for answer in answers:
            answer_data = {
                'question_id': answer.question.id,
                'question_text': answer.question.text,
                'question_type': answer.question.question_type,
            }

            if answer.selected_option:
                answer_data['selected_option'] = answer.selected_option.text
            elif answer.text_value:
                answer_data['text_value'] = answer.text_value
            elif answer.numeric_value is not None:
                answer_data['numeric_value'] = answer.numeric_value

            response_data['answers'].append(answer_data)

        data['responses'].append(response_data)

    return data

def prepare_response_for_analysis(response):
    """
    Prepare a single response for analysis
    """
    questionnaire = response.survey

    # Prepare data structure
    data = {
        'response': {
            'id': str(response.id),
            'created_at': response.created_at.isoformat(),
            'completed_at': response.completed_at.isoformat() if response.completed_at else None,
            'email': response.email,
            'gender': response.gender,
            'age': response.age,
        },
        'questionnaire': {
            'id': str(questionnaire.id),
            'title': questionnaire.title,
            'description': questionnaire.description,
        },
        'answers': []
    }

    # Add answers
    answers = Answer.objects.filter(response=response)
    for answer in answers:
        answer_data = {
            'question_id': answer.question.id,
            'question_text': answer.question.text,
            'question_type': answer.question.question_type,
        }

        if answer.selected_option:
            answer_data['selected_option'] = answer.selected_option.text
        elif answer.text_value:
            answer_data['text_value'] = answer.text_value
        elif answer.numeric_value is not None:
            answer_data['numeric_value'] = answer.numeric_value

        data['answers'].append(answer_data)

    return data

def perform_sentiment_analysis(gemini_service, data):
    """
    Perform sentiment analysis on response data
    """
    try:
        # For questionnaire analysis, analyze text answers
        if 'responses' in data:
            # Collect all text answers
            text_answers = []
            for response in data['responses']:
                for answer in response['answers']:
                    if 'text_value' in answer and answer['text_value']:
                        text_answers.append(answer['text_value'])

            # If no text answers, return an error
            if not text_answers:
                return {'error': 'No text answers found for sentiment analysis'}

            # Analyze each text answer
            sentiments = []
            for text in text_answers:
                result = gemini_service.analyze_text(text, 'sentiment')
                sentiments.append(result)

            # Aggregate results
            overall_sentiment = 'neutral'
            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
            total_score = 0

            for sentiment in sentiments:
                if 'sentiment' in sentiment:
                    sentiment_counts[sentiment['sentiment']] += 1
                if 'score' in sentiment:
                    total_score += sentiment['score']

            # Determine overall sentiment
            if sentiment_counts['positive'] > sentiment_counts['negative'] and sentiment_counts['positive'] > sentiment_counts['neutral']:
                overall_sentiment = 'positive'
            elif sentiment_counts['negative'] > sentiment_counts['positive'] and sentiment_counts['negative'] > sentiment_counts['neutral']:
                overall_sentiment = 'negative'

            # Calculate average score
            avg_score = total_score / len(sentiments) if sentiments else 0

            return {
                'overall_sentiment': overall_sentiment,
                'sentiment_counts': sentiment_counts,
                'average_score': avg_score,
                'individual_sentiments': sentiments,
                'summary': f"Overall sentiment: {overall_sentiment.capitalize()} with an average score of {avg_score:.2f}",
                'confidence': 0.85
            }

        # For single response analysis
        elif 'answers' in data:
            # Collect all text answers
            text_answers = []
            for answer in data['answers']:
                if 'text_value' in answer and answer['text_value']:
                    text_answers.append(answer['text_value'])

            # If no text answers, return an error
            if not text_answers:
                return {'error': 'No text answers found for sentiment analysis'}

            # Combine all text answers
            combined_text = ' '.join(text_answers)

            # Analyze the combined text
            result = gemini_service.analyze_text(combined_text, 'sentiment')

            # Add a summary
            result['summary'] = f"Sentiment: {result.get('sentiment', 'neutral').capitalize()} with a score of {result.get('score', 0):.2f}"

            return result

        return {'error': 'Invalid data format for sentiment analysis'}

    except Exception as e:
        return {'error': str(e)}

def perform_themes_analysis(gemini_service, data):
    """
    Perform theme identification on response data
    """
    try:
        # For questionnaire analysis, analyze text answers
        if 'responses' in data:
            # Collect all text answers
            text_answers = []
            for response in data['responses']:
                for answer in response['answers']:
                    if 'text_value' in answer and answer['text_value']:
                        text_answers.append(answer['text_value'])

            # If no text answers, return an error
            if not text_answers:
                return {'error': 'No text answers found for theme analysis'}

            # Combine all text answers
            combined_text = ' '.join(text_answers)

            # Analyze the combined text
            result = gemini_service.analyze_text(combined_text, 'themes')

            # Add a summary
            if 'themes' in result:
                theme_names = [theme['name'] for theme in result['themes']]
                result['summary'] = f"Main themes identified: {', '.join(theme_names)}"

            return result

        # For single response analysis
        elif 'answers' in data:
            # Collect all text answers
            text_answers = []
            for answer in data['answers']:
                if 'text_value' in answer and answer['text_value']:
                    text_answers.append(answer['text_value'])

            # If no text answers, return an error
            if not text_answers:
                return {'error': 'No text answers found for theme analysis'}

            # Combine all text answers
            combined_text = ' '.join(text_answers)

            # Analyze the combined text
            result = gemini_service.analyze_text(combined_text, 'themes')

            # Add a summary
            if 'themes' in result:
                theme_names = [theme['name'] for theme in result['themes']]
                result['summary'] = f"Main themes identified: {', '.join(theme_names)}"

            return result

        return {'error': 'Invalid data format for theme analysis'}

    except Exception as e:
        return {'error': str(e)}

def perform_patterns_analysis(gemini_service, data):
    """
    Perform pattern recognition on response data
    """
    try:
        # This only works for questionnaire analysis
        if 'responses' in data:
            # Need at least a few responses for pattern analysis
            if len(data['responses']) < 3:
                return {'error': 'Not enough responses for pattern analysis (minimum 3 required)'}

            # Prepare responses in a format suitable for pattern analysis
            responses_for_analysis = []
            for response in data['responses']:
                response_data = {
                    'id': response['id'],
                    'answers': {}
                }

                for answer in response['answers']:
                    question_text = answer['question_text']

                    if 'selected_option' in answer:
                        response_data['answers'][question_text] = answer['selected_option']
                    elif 'text_value' in answer and answer['text_value']:
                        response_data['answers'][question_text] = answer['text_value']
                    elif 'numeric_value' in answer:
                        response_data['answers'][question_text] = answer['numeric_value']

                responses_for_analysis.append(response_data)

            # Analyze the responses
            result = gemini_service.analyze_responses(responses_for_analysis, 'patterns')

            # Add a summary
            if 'patterns' in result:
                pattern_count = len(result['patterns'])
                result['summary'] = f"Identified {pattern_count} patterns in the responses"

            return result

        return {'error': 'Invalid data format for pattern analysis'}

    except Exception as e:
        return {'error': str(e)}

def perform_insights_analysis(gemini_service, data, questionnaire):
    """
    Generate insights from response data
    """
    try:
        # This only works for questionnaire analysis
        if 'responses' in data:
            # Need at least a few responses for insights
            if len(data['responses']) < 3:
                return {'error': 'Not enough responses for insights analysis (minimum 3 required)'}

            # Prepare questionnaire info
            questionnaire_info = {
                'id': str(questionnaire.id),
                'title': questionnaire.title,
                'description': questionnaire.description,
                'question_count': len(data['questionnaire']['questions']),
                'response_count': len(data['responses']),
                'questions': [
                    {
                        'id': q['id'],
                        'text': q['text'],
                        'type': q['type']
                    }
                    for q in data['questionnaire']['questions']
                ]
            }

            # Generate insights
            result = gemini_service.generate_insights(data, questionnaire_info)

            # Add a summary
            if 'key_insights' in result:
                insight_count = len(result['key_insights'])
                result['summary'] = f"Generated {insight_count} key insights from the responses"

            return result

        return {'error': 'Invalid data format for insights analysis'}

    except Exception as e:
        return {'error': str(e)}
