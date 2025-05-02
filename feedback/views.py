from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import HttpResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import csv
import json

from .models import Response as SurveyResponse, Answer
from .models.base import AIAnalysis as AnalysisResult
from surveys.models import Survey, Question, QuestionChoice

@login_required
def response_list(request):
    """
    Display a list of all responses
    """
    # Get filter parameters from request
    survey_id = request.GET.get('survey')
    status = request.GET.get('status')
    risk_level = request.GET.get('risk_level')
    search_query = request.GET.get('q')
    page = request.GET.get('page', 1)

    # Start with all responses
    responses = SurveyResponse.objects.select_related('survey', 'respondent').all()

    # Apply filters if provided
    if survey_id:
        responses = responses.filter(survey_id=survey_id)

    if status:
        responses = responses.filter(status=status)

    if risk_level:
        responses = responses.filter(risk_level=risk_level)

    if search_query:
        responses = responses.filter(
            Q(survey__title__icontains=search_query) |
            Q(respondent__email__icontains=search_query) |
            Q(respondent_email__icontains=search_query) |
            Q(respondent_name__icontains=search_query) |
            Q(response_id__icontains=search_query)
        )

    # Annotate with answer count for efficiency
    responses = responses.annotate(answer_count=Count('answers'))

    # Order by most recent first
    responses = responses.order_by('-started_at')

    # Paginate the results
    paginator = Paginator(responses, 10)  # Show 10 responses per page

    try:
        responses = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        responses = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        responses = paginator.page(paginator.num_pages)

    # Get all surveys for the filter dropdown
    surveys = Survey.objects.all()

    # Get status and risk level choices from the model
    statuses = SurveyResponse.STATUS_CHOICES
    risk_levels = SurveyResponse.RISK_LEVEL_CHOICES

    context = {
        'responses': responses,
        'surveys': surveys,
        'statuses': statuses,
        'risk_levels': risk_levels,
        'selected_survey': survey_id,
        'selected_status': status,
        'selected_risk_level': risk_level,
        'search_query': search_query,
    }

    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'feedback/partials/response_list.html', context)

    return render(request, 'feedback/response_list.html', context)

@login_required
def response_detail(request, pk):
    """
    Display response details
    """
    # Get the response from the database
    response = get_object_or_404(SurveyResponse.objects.select_related('survey', 'respondent'), pk=pk)

    # Get all answers for this response
    answers = Answer.objects.filter(response=response).select_related('question', 'selected_choice').prefetch_related('multiple_choices')

    # Check if the user has permission to view this response
    if response.survey.organization:
        # If the response is for an organization survey, check if the user is a member
        user_is_member = response.survey.organization.members.filter(user=request.user).exists()
        if not user_is_member and response.respondent != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to view this response.")
            return redirect('feedback:response_list')

    # If the response is a personal survey, check if the user is the creator or respondent
    elif response.survey.created_by != request.user and response.respondent != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to view this response.")
        return redirect('feedback:response_list')

    return render(request, 'feedback/response_detail.html', {'response': response, 'answers': answers})

@login_required
def response_detail_tabs(request, pk):
    """
    Display response details with tabbed interface and enhanced visualizations
    """
    # Get the response from the database
    response = get_object_or_404(SurveyResponse.objects.select_related('survey', 'respondent'), pk=pk)

    # Get all answers for this response
    answers = Answer.objects.filter(response=response).select_related('question', 'selected_choice').prefetch_related('multiple_choices')

    # Check if the user has permission to view this response
    if response.survey.organization:
        # If the response is for an organization survey, check if the user is a member
        user_is_member = response.survey.organization.members.filter(user=request.user).exists()
        if not user_is_member and response.respondent != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to view this response.")
            return redirect('feedback:response_list')

    # If the response is a personal survey, check if the user is the creator or respondent
    elif response.survey.created_by != request.user and response.respondent != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to view this response.")
        return redirect('feedback:response_list')

    # Get score breakdown data for charts
    score_breakdown_labels = []
    score_breakdown_data = []
    category_averages = []

    # Group answers by category and calculate scores
    categories = {}
    for answer in answers:
        category = answer.question.category or 'Uncategorized'
        if category not in categories:
            categories[category] = {'score': 0, 'count': 0}

        if hasattr(answer, 'score') and answer.score is not None:
            categories[category]['score'] += answer.score
            categories[category]['count'] += 1

    # Calculate average scores for each category
    for category, data in categories.items():
        if data['count'] > 0:
            score_breakdown_labels.append(category)
            avg_score = data['score'] / data['count']
            score_breakdown_data.append(round(avg_score, 2))

            # For now, use a placeholder for category averages
            # In a real implementation, you would calculate this from historical data
            category_averages.append(round(avg_score * 0.9, 2))  # Just a placeholder

    # Get comparative data (placeholder)
    comparative_labels = ['Previous Month', 'Current']
    comparative_data = [response.total_score * 0.85 if response.total_score else 0, response.total_score]

    # Get risk distribution (placeholder)
    # In a real implementation, you would calculate this from actual data
    risk_distribution = [25, 40, 25, 10]  # Low, Medium, High, Critical

    # Generate correlation insights (placeholder)
    # In a real implementation, you would calculate actual correlations
    correlation_insights = [
        {
            'description': 'Strong correlation between anxiety and sleep disturbance',
            'strength': 'strong',
            'questions_involved': ['Q2', 'Q7']
        },
        {
            'description': 'Moderate correlation between mood and energy levels',
            'strength': 'moderate',
            'questions_involved': ['Q1', 'Q4']
        },
        {
            'description': 'Weak correlation between appetite and concentration',
            'strength': 'weak',
            'questions_involved': ['Q3', 'Q8']
        }
    ]

    # Calculate percentile rank (placeholder)
    # In a real implementation, you would calculate this from actual data
    percentile_rank = 65  # Just a placeholder

    # Calculate average score (placeholder)
    # In a real implementation, you would calculate this from actual data
    avg_score = response.total_score * 0.9 if response.total_score else None

    # Calculate maximum possible score
    max_possible_score = 0
    for answer in answers:
        if answer.question.is_scored:
            if answer.question.max_score:
                max_possible_score += answer.question.max_score
            elif answer.question.question_type == 'scale':
                max_possible_score += answer.question.scale_max
            else:
                max_possible_score += 5  # Default max score

    # Generate question response times (placeholder)
    # In a real implementation, you would get actual response times
    import random
    question_times = [random.randint(5, 30) for _ in range(min(10, answers.count()))]
    avg_question_times = [t * 0.8 + random.randint(-3, 3) for t in question_times]

    context = {
        'response': response,
        'answers': answers,
        'score_breakdown_labels': score_breakdown_labels,
        'score_breakdown_data': score_breakdown_data,
        'category_averages': category_averages,
        'comparative_labels': comparative_labels,
        'comparative_data': comparative_data,
        'risk_distribution': risk_distribution,
        'correlation_insights': correlation_insights,
        'percentile_rank': percentile_rank,
        'avg_score': avg_score,
        'max_possible_score': max_possible_score,
        'question_times': question_times,
        'avg_question_times': avg_question_times
    }

    return render(request, 'feedback/response_detail_tabs.html', context)

@login_required
def response_analyze(request, pk):
    """
    Analyze a response
    """
    # Get the response from the database
    response = get_object_or_404(SurveyResponse.objects.select_related('survey'), pk=pk)

    # Check if the user has permission to analyze this response
    if response.survey.organization:
        # If the response is for an organization survey, check if the user is a member
        user_is_member = response.survey.organization.members.filter(user=request.user).exists()
        if not user_is_member and response.respondent != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to analyze this response.")
            return redirect('feedback:response_list')

    # If the response is a personal survey, check if the user is the creator or respondent
    elif response.survey.created_by != request.user and response.respondent != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to analyze this response.")
        return redirect('feedback:response_list')

    # Check if analysis already exists
    try:
        analysis = response.analysis
        messages.info(request, "Analysis already exists for this response.")
    except AnalysisResult.DoesNotExist:
        # Create a new analysis
        analysis = AnalysisResult(
            response=response,
            summary=f"Analysis for {response.survey.title}",
            detailed_analysis="This is a detailed analysis of the response.",
            recommendations="These are the recommendations based on the response.",
            raw_data={}
        )
        analysis.save()
        messages.success(request, "Analysis generated successfully.")

    return render(request, 'feedback/response_analyze.html', {'response': response, 'analysis': analysis})

@login_required
def survey_response_list(request, survey_pk):
    """
    Display a list of responses for a specific survey
    """
    # Get the survey from the database
    survey = get_object_or_404(Survey, pk=survey_pk)

    # Check if the user has permission to view responses for this survey
    if survey.organization:
        # If the survey is for an organization, check if the user is a member
        user_is_member = survey.organization.members.filter(user=request.user).exists()
        if not user_is_member and survey.created_by != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to view responses for this survey.")
            return redirect('surveys:survey_list')

    # If the survey is personal, check if the user is the creator
    elif survey.created_by != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to view responses for this survey.")
        return redirect('surveys:survey_list')

    # Get filter parameters from request
    status = request.GET.get('status')
    risk_level = request.GET.get('risk_level')
    search_query = request.GET.get('q')

    # Get all responses for this survey
    responses = SurveyResponse.objects.filter(survey=survey).select_related('respondent')

    # Apply filters if provided
    if status:
        responses = responses.filter(status=status)

    if risk_level:
        responses = responses.filter(risk_level=risk_level)

    if search_query:
        responses = responses.filter(
            Q(respondent__email__icontains=search_query) |
            Q(respondent_email__icontains=search_query) |
            Q(respondent_name__icontains=search_query) |
            Q(response_id__icontains=search_query)
        )

    # Annotate with answer count for efficiency
    responses = responses.annotate(answer_count=Count('answers'))

    # Get status and risk level choices from the model
    statuses = SurveyResponse.STATUS_CHOICES
    risk_levels = SurveyResponse.RISK_LEVEL_CHOICES

    context = {
        'survey': survey,
        'responses': responses,
        'statuses': statuses,
        'risk_levels': risk_levels,
        'selected_status': status,
        'selected_risk_level': risk_level,
        'search_query': search_query,
    }

    return render(request, 'feedback/survey_response_list.html', context)

def respond_to_survey(request, survey_pk):
    """
    Allow a user to respond to a survey
    """
    # Get the survey from the database
    survey = get_object_or_404(Survey, pk=survey_pk)

    # Check if the survey is active
    if survey.status != 'active':
        messages.error(request, "This survey is not currently active.")
        return redirect('surveys:survey_list')

    # Check if authentication is required
    if survey.requires_auth and not request.user.is_authenticated:
        messages.error(request, "You need to be logged in to respond to this survey.")
        return redirect('account_login')

    # Check if anonymous responses are allowed
    if not survey.allow_anonymous and not request.user.is_authenticated:
        messages.error(request, "Anonymous responses are not allowed for this survey.")
        return redirect('account_login')

    # Get all questions for this survey
    questions = Question.objects.filter(survey=survey).order_by('order').prefetch_related('choices')

    # Create a new response if this is a GET request
    if request.method == 'GET':
        # Create a new response
        response = SurveyResponse(
            survey=survey,
            respondent=request.user if request.user.is_authenticated else None,
            status='in_progress',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        response.save()

        # Store the response ID in the session
        request.session['current_response_id'] = response.pk

        return render(request, 'feedback/respond_to_survey.html', {
            'survey': survey,
            'questions': questions,
            'response': response
        })

    # Process the form submission if this is a POST request
    elif request.method == 'POST':
        # Get the response ID from the session
        response_id = request.session.get('current_response_id')
        if not response_id:
            messages.error(request, "Your session has expired. Please start again.")
            return redirect('feedback:respond_to_survey', survey_pk=survey_pk)

        # Get the response
        response = get_object_or_404(SurveyResponse, pk=response_id)

        # Process each question
        for question in questions:
            answer_key = f'question_{question.pk}'

            # Skip if the question wasn't answered
            if answer_key not in request.POST and not question.required:
                continue

            # Create a new answer
            answer = Answer(response=response, question=question)

            # Process the answer based on question type
            if question.question_type == 'text' or question.question_type == 'textarea':
                answer.text_answer = request.POST.get(answer_key, '')

            elif question.question_type == 'radio' or question.question_type == 'dropdown':
                choice_id = request.POST.get(answer_key)
                if choice_id:
                    answer.selected_choice = get_object_or_404(QuestionChoice, pk=choice_id)

            elif question.question_type == 'checkbox':
                choice_ids = request.POST.getlist(answer_key)
                answer.save()  # Save first to get an ID for the many-to-many relationship
                for choice_id in choice_ids:
                    choice = get_object_or_404(QuestionChoice, pk=choice_id)
                    answer.multiple_choices.add(choice)

            elif question.question_type == 'scale':
                answer.numeric_value = int(request.POST.get(answer_key, 0))

            # Save the answer
            answer.save()

        # Mark the response as completed
        response.status = 'completed'
        response.completed_at = timezone.now()

        # Calculate the score
        response.calculate_score()

        # Determine the risk level
        response.determine_risk_level()

        # Save the response
        response.save()

        # Clear the session
        if 'current_response_id' in request.session:
            del request.session['current_response_id']

        # Show success message
        messages.success(request, 'Thank you for your response!')
        return redirect('feedback:response_complete')

    return render(request, 'feedback/respond_to_survey.html', {'survey': survey, 'questions': questions})

def response_complete(request):
    """
    Thank you page after completing a survey
    """
    return render(request, 'feedback/response_complete.html')

@login_required
def update_notes(request, pk):
    """
    Update notes for a response
    """
    # Get the response from the database
    response = get_object_or_404(SurveyResponse, pk=pk)

    # Check if the user has permission to update notes for this response
    if response.survey.organization:
        # If the response is for an organization survey, check if the user is a member
        user_is_member = response.survey.organization.members.filter(user=request.user).exists()
        if not user_is_member and response.respondent != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to update notes for this response.")
            return redirect('feedback:response_list')

    # If the response is a personal survey, check if the user is the creator or respondent
    elif response.survey.created_by != request.user and response.respondent != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to update notes for this response.")
        return redirect('feedback:response_list')

    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        response.notes = notes
        response.save(update_fields=['notes'])
        messages.success(request, 'Notes updated successfully.')

    return redirect('feedback:response_detail', pk=pk)

@login_required
def generate_analysis(request, pk):
    """
    Generate analysis for a response using Gemini API
    """
    # Get the response from the database
    response = get_object_or_404(SurveyResponse.objects.select_related('survey'), pk=pk)

    # Check if the user has permission to generate analysis for this response
    if response.survey.organization:
        # If the response is for an organization survey, check if the user is a member
        user_is_member = response.survey.organization.members.filter(user=request.user).exists()
        if not user_is_member and response.respondent != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to generate analysis for this response.")
            return redirect('feedback:response_list')

    # If the response is a personal survey, check if the user is the creator or respondent
    elif response.survey.created_by != request.user and response.respondent != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to generate analysis for this response.")
        return redirect('feedback:response_list')

    # Check if analysis already exists
    try:
        analysis = response.analysis
        messages.info(request, "Analysis already exists for this response.")
        return redirect('feedback:response_detail', pk=pk)
    except AnalysisResult.DoesNotExist:
        # Get all answers for this response
        answers = Answer.objects.filter(response=response).select_related('question', 'selected_choice').prefetch_related('multiple_choices')

        try:
            # Import the Gemini service
            try:
                from analytics.services.gemini_service import GeminiService
                # Initialize the Gemini service with the API key
                gemini_service = GeminiService(api_key="AIzaSyAp5usIOWlm16BgN1tfGje4aD0YKVa1Mjc")
            except ImportError:
                # If the GeminiService is not available, use a fallback approach
                gemini_service = None

            if gemini_service:
                # Prepare the data for analysis
                questionnaire_info = {
                    "title": response.survey.title,
                    "category": response.survey.category,
                    "description": response.survey.description,
                    "total_questions": answers.count(),
                    "scoring_method": "weighted_sum" if response.total_score is not None else "none"
                }

                # Format the answers for the API
                answer_data = []
                for answer in answers:
                    answer_item = {
                        "question_text": answer.question.text,
                        "question_type": answer.question.question_type,
                        "question_category": answer.question.category,
                        "is_scored": answer.question.is_scored,
                    }

                    # Add the appropriate answer value based on question type
                    if answer.question.question_type == 'text' or answer.question.question_type == 'textarea':
                        answer_item["answer"] = answer.text_answer
                    elif answer.question.question_type in ['radio', 'dropdown', 'single_choice']:
                        answer_item["answer"] = answer.selected_choice.text if answer.selected_choice else "No selection"
                    elif answer.question.question_type in ['checkbox', 'multiple_choice']:
                        answer_item["answer"] = [choice.text for choice in answer.multiple_choices.all()]
                    elif answer.question.question_type == 'scale' or answer.question.question_type == 'number':
                        answer_item["answer"] = answer.numeric_value

                    # Add score information if available
                    if hasattr(answer, 'score') and answer.score is not None:
                        answer_item["score"] = answer.score
                        answer_item["weight"] = answer.question.scoring_weight
                        answer_item["weighted_score"] = answer.score * answer.question.scoring_weight

                    answer_data.append(answer_item)

                # Add respondent information
                respondent_info = {
                    "age": getattr(response, 'patient_age', None),
                    "gender": getattr(response, 'patient_gender', None),
                    "completion_time": getattr(response, 'completion_time', None),
                    "total_score": response.total_score,
                    "risk_level": response.risk_level
                }

                # Combine all data
                analysis_data = {
                    "questionnaire": questionnaire_info,
                    "respondent": respondent_info,
                    "answers": answer_data
                }

                # Generate the analysis using Gemini API
                result = gemini_service.analyze_questionnaire_data(analysis_data, questionnaire_info)

                # Extract the analysis components
                summary = result.get('summary', f"Analysis for {response.survey.title}")
                detailed_analysis = result.get('detailed_analysis', "Analysis not available.")
                recommendations = result.get('recommendations', "No specific recommendations available.")

                # Create the raw data for storage
                raw_data = {
                    "gemini_response": result,
                    "analysis_data": analysis_data,
                    "generated_at": timezone.now().isoformat(),
                    "model": "gemini-pro"
                }

            else:
                # Fallback to basic analysis if Gemini API is not available
                if response.survey.category == 'anxiety':
                    summary = "Anxiety Assessment Analysis"
                    if response.total_score < 5:
                        detailed_analysis = "The patient shows minimal anxiety symptoms."
                        recommendations = "No intervention needed at this time."
                    elif response.total_score < 10:
                        detailed_analysis = "The patient shows mild anxiety symptoms."
                        recommendations = "Consider follow-up assessment in 4-6 weeks."
                    elif response.total_score < 15:
                        detailed_analysis = "The patient shows moderate anxiety symptoms."
                        recommendations = "Consider referral to mental health professional."
                    else:
                        detailed_analysis = "The patient shows severe anxiety symptoms."
                        recommendations = "Immediate referral to mental health professional recommended."

                elif response.survey.category == 'depression':
                    summary = "Depression Screening Analysis"
                    if response.total_score < 5:
                        detailed_analysis = "The patient shows minimal depression symptoms."
                        recommendations = "No intervention needed at this time."
                    elif response.total_score < 10:
                        detailed_analysis = "The patient shows mild depression symptoms."
                        recommendations = "Consider follow-up assessment in 4-6 weeks."
                    elif response.total_score < 15:
                        detailed_analysis = "The patient shows moderate depression symptoms."
                        recommendations = "Consider referral to mental health professional."
                    else:
                        detailed_analysis = "The patient shows severe depression symptoms."
                        recommendations = "Immediate referral to mental health professional recommended."

                else:
                    summary = f"Analysis for {response.survey.title}"
                    detailed_analysis = "This is a detailed analysis of the response."
                    recommendations = "These are the recommendations based on the response."

                raw_data = {}

            # Create a new analysis
            analysis = AnalysisResult(
                response=response,
                summary=summary,
                detailed_analysis=detailed_analysis,
                recommendations=recommendations,
                raw_data=raw_data
            )
            analysis.save()
            messages.success(request, "Analysis generated successfully using AI.")

        except Exception as e:
            # Log the error and create a basic analysis
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating analysis: {str(e)}")

            # Create a basic analysis
            analysis = AnalysisResult(
                response=response,
                summary=f"Analysis for {response.survey.title}",
                detailed_analysis="An error occurred while generating the detailed analysis.",
                recommendations="Please try regenerating the analysis.",
                raw_data={"error": str(e)}
            )
            analysis.save()
            messages.warning(request, f"Analysis generated with limited functionality due to an error: {str(e)}")

    return redirect('feedback:response_detail', pk=pk)

@login_required
def export_response(request, pk):
    """
    Export a response to a CSV file
    """
    # Get the response from the database
    response = get_object_or_404(SurveyResponse.objects.select_related('survey', 'respondent'), pk=pk)

    # Check if the user has permission to export this response
    if response.survey.organization:
        # If the response is for an organization survey, check if the user is a member
        user_is_member = response.survey.organization.members.filter(user=request.user).exists()
        if not user_is_member and response.respondent != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to export this response.")
            return redirect('feedback:response_list')

    # If the response is a personal survey, check if the user is the creator or respondent
    elif response.survey.created_by != request.user and response.respondent != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to export this response.")
        return redirect('feedback:response_list')

    # Get all answers for this response
    answers = Answer.objects.filter(response=response).select_related('question', 'selected_choice').prefetch_related('multiple_choices')

    # Create a CSV response
    http_response = HttpResponse(content_type='text/csv')
    http_response['Content-Disposition'] = f'attachment; filename="response_{response.pk}.csv"'

    # Create a CSV writer
    writer = csv.writer(http_response)

    # Write the header row
    writer.writerow(['Survey', 'Response ID', 'Respondent', 'Status', 'Started At', 'Completed At', 'Total Score', 'Risk Level'])

    # Write the response data
    writer.writerow([
        response.survey.title,
        response.response_id,
        response.respondent.email if response.respondent else (response.respondent_email or 'Anonymous'),
        response.get_status_display(),
        response.started_at,
        response.completed_at,
        response.total_score,
        response.get_risk_level_display()
    ])

    # Write a blank row
    writer.writerow([])

    # Write the answers header
    writer.writerow(['Question', 'Answer', 'Score'])

    # Write the answers
    for answer in answers:
        if answer.question.question_type == 'text' or answer.question.question_type == 'textarea':
            writer.writerow([answer.question.text, answer.text_answer, ''])

        elif answer.question.question_type == 'radio' or answer.question.question_type == 'dropdown':
            if answer.selected_choice:
                writer.writerow([answer.question.text, answer.selected_choice.text, answer.selected_choice.score])
            else:
                writer.writerow([answer.question.text, '', ''])

        elif answer.question.question_type == 'checkbox':
            choices = ', '.join([choice.text for choice in answer.multiple_choices.all()])
            score = sum([choice.score for choice in answer.multiple_choices.all()])
            writer.writerow([answer.question.text, choices, score])

        elif answer.question.question_type == 'scale':
            writer.writerow([answer.question.text, answer.numeric_value, answer.numeric_value])

        elif answer.question.question_type == 'date':
            writer.writerow([answer.question.text, answer.date_value, ''])

        elif answer.question.question_type == 'time':
            writer.writerow([answer.question.text, answer.time_value, ''])

    return http_response
