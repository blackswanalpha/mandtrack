from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import HttpResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import csv
import json

from .models import Response, Answer
from .models.base import AIAnalysis
from surveys.models import Questionnaire, Question, QuestionChoice

@login_required
def response_list(request):
    """
    Display a list of all responses
    """
    # Get filter parameters from request
    questionnaire_id = request.GET.get('questionnaire')
    status = request.GET.get('status')
    risk_level = request.GET.get('risk_level')
    search_query = request.GET.get('q')
    page = request.GET.get('page', 1)

    # Start with all responses
    responses = Response.objects.select_related('survey', 'user').all()

    # Apply filters if provided
    if questionnaire_id:
        responses = responses.filter(survey_id=questionnaire_id)

    if status:
        responses = responses.filter(status=status)

    if risk_level:
        responses = responses.filter(risk_level=risk_level)

    if search_query:
        responses = responses.filter(
            Q(survey__title__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(patient_email__icontains=search_query) |
            Q(patient_name__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    # Annotate with answer count for efficiency
    responses = responses.annotate(answer_count=Count('answers'))

    # Order by most recent first
    responses = responses.order_by('-created_at')

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

    # Get all questionnaires for the filter dropdown
    questionnaires = Questionnaire.objects.all()

    # Get status and risk level choices from the model
    statuses = Response.STATUS_CHOICES
    risk_levels = Response.RISK_LEVEL_CHOICES

    context = {
        'responses': responses,
        'questionnaires': questionnaires,
        'statuses': statuses,
        'risk_levels': risk_levels,
        'selected_questionnaire': questionnaire_id,
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
    response = get_object_or_404(Response.objects.select_related('survey', 'user'), pk=pk)

    # Get all answers for this response
    answers = Answer.objects.filter(response=response).select_related('question', 'selected_choice').prefetch_related('multiple_choices')

    # Check if the user has permission to view this response
    if response.survey.organization:
        # If the response is for an organization questionnaire, check if the user is a member
        user_is_member = response.survey.organization.members.filter(user=request.user).exists()
        if not user_is_member and response.user != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to view this response.")
            return redirect('feedback:response_list')

    # If the response is a personal questionnaire, check if the user is the creator or respondent
    elif response.survey.created_by != request.user and response.user != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to view this response.")
        return redirect('feedback:response_list')

    return render(request, 'feedback/response_detail.html', {'response': response, 'answers': answers})

@login_required
def response_detail_tabs(request, pk):
    """
    Display response details with tabbed interface and enhanced visualizations
    """
    # Get the response from the database
    response = get_object_or_404(Response.objects.select_related('survey', 'user'), pk=pk)

    # Get all answers for this response
    answers = Answer.objects.filter(response=response).select_related('question', 'selected_choice').prefetch_related('multiple_choices')

    # Check if the user has permission to view this response
    if response.survey.organization:
        # If the response is for an organization questionnaire, check if the user is a member
        user_is_member = response.survey.organization.members.filter(user=request.user).exists()
        if not user_is_member and response.user != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to view this response.")
            return redirect('feedback:response_list')

    # If the response is a personal questionnaire, check if the user is the creator or respondent
    elif response.survey.created_by != request.user and response.user != request.user and not request.user.is_staff:
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
    comparative_data = [response.score * 0.85 if response.score else 0, response.score]

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
    avg_score = response.score * 0.9 if response.score else None

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
    response = get_object_or_404(Response.objects.select_related('survey'), pk=pk)

    # Check if the user has permission to analyze this response
    if response.survey.organization:
        # If the response is for an organization questionnaire, check if the user is a member
        user_is_member = response.survey.organization.members.filter(user=request.user).exists()
        if not user_is_member and response.user != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to analyze this response.")
            return redirect('feedback:response_list')

    # If the response is a personal questionnaire, check if the user is the creator or respondent
    elif response.survey.created_by != request.user and response.user != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to analyze this response.")
        return redirect('feedback:response_list')

    # Check if analysis already exists
    try:
        analysis = response.analysis
        messages.info(request, "Analysis already exists for this response.")
    except AIAnalysis.DoesNotExist:
        # Create a new analysis
        analysis = AIAnalysis(
            response=response,
            summary=f"Analysis for {response.survey.title}",
            detailed_analysis="This is a detailed analysis of the response.",
            recommendations="These are the recommendations based on the response.",
            raw_data={},
            created_by=request.user
        )
        analysis.save()
        messages.success(request, "Analysis generated successfully.")

    return render(request, 'feedback/response_analyze.html', {'response': response, 'analysis': analysis})

@login_required
def questionnaire_response_list(request, questionnaire_pk):
    """
    Display a list of responses for a specific questionnaire
    """
    # Get the questionnaire from the database
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_pk)

    # Check if the user has permission to view responses for this questionnaire
    if questionnaire.organization:
        # If the questionnaire is for an organization, check if the user is a member
        user_is_member = questionnaire.organization.members.filter(user=request.user).exists()
        if not user_is_member and questionnaire.created_by != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to view responses for this questionnaire.")
            return redirect('surveys:survey_list')

    # If the questionnaire is personal, check if the user is the creator
    elif questionnaire.created_by != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to view responses for this questionnaire.")
        return redirect('surveys:survey_list')

    # Get filter parameters from request
    status = request.GET.get('status')
    risk_level = request.GET.get('risk_level')
    search_query = request.GET.get('q')

    # Get all responses for this questionnaire
    responses = Response.objects.filter(survey=questionnaire).select_related('user')

    # Apply filters if provided
    if status:
        responses = responses.filter(status=status)

    if risk_level:
        responses = responses.filter(risk_level=risk_level)

    if search_query:
        responses = responses.filter(
            Q(user__email__icontains=search_query) |
            Q(patient_email__icontains=search_query) |
            Q(patient_name__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    # Annotate with answer count for efficiency
    responses = responses.annotate(answer_count=Count('answers'))

    # Get status and risk level choices from the model
    statuses = Response.STATUS_CHOICES
    risk_levels = Response.RISK_LEVEL_CHOICES

    context = {
        'questionnaire': questionnaire,
        'responses': responses,
        'statuses': statuses,
        'risk_levels': risk_levels,
        'selected_status': status,
        'selected_risk_level': risk_level,
        'search_query': search_query,
    }

    return render(request, 'feedback/questionnaire_response_list.html', context)

def respond_to_questionnaire(request, questionnaire_pk):
    """
    Allow a user to respond to a questionnaire
    """
    # Get the questionnaire from the database
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_pk)

    # Check if this is a preview request (from admin/creator)
    is_preview = request.GET.get('preview') == 'true' or request.GET.get('mode') == 'preview'
    is_creator = request.user.is_authenticated and request.user == questionnaire.created_by
    is_admin = request.user.is_authenticated and request.user.is_staff

    # Check if the questionnaire is active (skip check for preview mode or if user is creator/admin)
    if questionnaire.status != 'active' and not (is_preview or is_creator or is_admin):
        messages.error(request, "This questionnaire is not currently active.")
        return redirect('surveys:survey_list')

    # Check if authentication is required (skip for preview mode or if user is creator/admin)
    if questionnaire.requires_auth and not request.user.is_authenticated and not (is_preview or is_creator or is_admin):
        messages.error(request, "You need to be logged in to respond to this questionnaire.")
        return redirect('account_login')

    # Check if anonymous responses are allowed
    if not questionnaire.allow_anonymous and not request.user.is_authenticated:
        messages.error(request, "Anonymous responses are not allowed for this questionnaire.")
        return redirect('account_login')

    # Get all questions for this questionnaire
    questions = Question.objects.filter(survey=questionnaire).order_by('order').prefetch_related('choices')

    # Create a new response if this is a GET request
    if request.method == 'GET':
        # Create a new response
        response = Response(
            survey=questionnaire,
            user=request.user if request.user.is_authenticated else None,
            status='in_progress',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        response.save()

        # Store the response ID in the session
        request.session['current_response_id'] = str(response.id)

        return render(request, 'feedback/respond_to_questionnaire.html', {
            'questionnaire': questionnaire,
            'questions': questions,
            'response': response
        })

    # Process the form submission if this is a POST request
    elif request.method == 'POST':
        # Get the response ID from the session
        response_id = request.session.get('current_response_id')
        if not response_id:
            messages.error(request, "Your session has expired. Please start again.")
            return redirect('feedback:respond_to_questionnaire', questionnaire_pk=questionnaire_pk)

        # Get the response
        response = get_object_or_404(Response, pk=response_id)

        # Update demographic information
        response.patient_name = request.POST.get('patient_name', '')
        response.patient_email = request.POST.get('patient_email', '')

        # Handle patient age - convert to integer if provided, otherwise set to None
        patient_age = request.POST.get('patient_age', '')
        if patient_age and patient_age.strip():
            try:
                response.patient_age = int(patient_age)
            except ValueError:
                # If conversion fails, set to None
                response.patient_age = None
        else:
            response.patient_age = None

        response.patient_gender = request.POST.get('patient_gender', '')
        response.save()

        # Process each question
        for question in questions:
            answer_key = f'question_{question.pk}'

            # Skip if the question wasn't answered
            if answer_key not in request.POST and not question.required:
                continue

            # Check if an answer already exists for this question and response
            existing_answer = Answer.objects.filter(response=response, question=question).first()

            if existing_answer:
                # Update the existing answer
                answer = existing_answer
            else:
                # Create a new answer
                answer = Answer(response=response, question=question)

            # Process the answer based on question type
            if question.question_type == 'text' or question.question_type == 'textarea':
                answer.text_answer = request.POST.get(answer_key, '')
                answer.save()  # Save before adding many-to-many relationships

            elif question.question_type == 'single_choice':
                choice_id = request.POST.get(answer_key)
                if choice_id:
                    answer.selected_choice = get_object_or_404(QuestionChoice, pk=choice_id)
                answer.save()  # Save before adding many-to-many relationships

            elif question.question_type == 'multiple_choice':
                # Save first to get an ID for the many-to-many relationship
                answer.save()

                # Clear existing choices if updating
                if existing_answer:
                    answer.multiple_choices.clear()

                # Add new choices
                choice_ids = request.POST.getlist(answer_key)
                for choice_id in choice_ids:
                    choice = get_object_or_404(QuestionChoice, pk=choice_id)
                    answer.multiple_choices.add(choice)

            elif question.question_type == 'number' or question.question_type == 'scale':
                answer.numeric_value = float(request.POST.get(answer_key, 0))
                answer.save()  # Save before adding many-to-many relationships

            # Calculate the score for this answer
            try:
                # Try to use the calculate_score method if it exists
                if hasattr(answer, 'calculate_score') and callable(answer.calculate_score):
                    answer.calculate_score()
                else:
                    # Fallback to manual score calculation
                    if hasattr(answer.question, 'is_scored') and answer.question.is_scored:
                        if answer.selected_choice:
                            answer.score = answer.selected_choice.score
                        elif answer.multiple_choices.exists():
                            # Average the scores of all selected choices
                            scores = [choice.score for choice in answer.multiple_choices.all()]
                            answer.score = sum(scores) / len(scores) if scores else 0
                        elif answer.numeric_value is not None:
                            # Scale numeric values based on question's max_score
                            if hasattr(answer.question, 'max_score'):
                                answer.score = min(answer.numeric_value, answer.question.max_score)
                            else:
                                answer.score = answer.numeric_value
                        else:
                            answer.score = 0
                        answer.save(update_fields=['score'])
            except Exception as e:
                # Log the error but continue processing
                print(f"Error calculating score for answer {answer.id}: {str(e)}")

        # Mark the response as completed
        try:
            if hasattr(response, 'mark_as_completed') and callable(response.mark_as_completed):
                response.mark_as_completed()
            else:
                # Fallback implementation
                from django.utils import timezone
                response.status = 'completed'
                response.completed_at = timezone.now()
                response.save(update_fields=['status', 'completed_at'])
        except Exception as e:
            print(f"Error marking response as completed: {str(e)}")
            # Fallback implementation
            from django.utils import timezone
            response.status = 'completed'
            response.completed_at = timezone.now()
            response.save(update_fields=['status', 'completed_at'])

        # Calculate the score
        try:
            if hasattr(response, 'calculate_score') and callable(response.calculate_score):
                response.calculate_score()
            else:
                # Fallback implementation
                calculated_score = 0
                for answer in response.answers.all():
                    if hasattr(answer, 'score') and answer.score is not None:
                        calculated_score += answer.score
                response.score = calculated_score
                response.save(update_fields=['score'])
        except Exception as e:
            print(f"Error calculating response score: {str(e)}")

        # Determine the risk level
        try:
            if hasattr(response, 'determine_risk_level') and callable(response.determine_risk_level):
                response.determine_risk_level()
            else:
                # Fallback implementation
                if response.score is None:
                    # Calculate score if not already done
                    calculated_score = 0
                    for answer in response.answers.all():
                        if hasattr(answer, 'score') and answer.score is not None:
                            calculated_score += answer.score
                    response.score = calculated_score
                    response.save(update_fields=['score'])

                # Simple risk level determination
                if response.score < 5:
                    risk = 'low'
                elif response.score < 10:
                    risk = 'medium'
                elif response.score < 15:
                    risk = 'high'
                else:
                    risk = 'critical'

                response.risk_level = risk
                response.save(update_fields=['risk_level'])
        except Exception as e:
            print(f"Error determining risk level: {str(e)}")

        # Clear the session
        if 'current_response_id' in request.session:
            del request.session['current_response_id']

        # Show success message
        messages.success(request, 'Thank you for your response!')
        return redirect('feedback:response_complete')

    return render(request, 'feedback/respond_to_questionnaire.html', {'questionnaire': questionnaire, 'questions': questions})

def response_complete(request):
    """
    Thank you page after completing a questionnaire
    """
    # Get the most recent completed response for this user/session
    response = None

    # Try to find by user if authenticated
    if request.user.is_authenticated:
        response = Response.objects.filter(
            user=request.user,
            status='completed'
        ).order_by('-completed_at').first()

    # If no response found and we have an IP address, try to find by IP
    if not response and request.META.get('REMOTE_ADDR'):
        response = Response.objects.filter(
            ip_address=request.META.get('REMOTE_ADDR'),
            status='completed'
        ).order_by('-completed_at').first()

    return render(request, 'feedback/response_complete.html', {'response': response})


def direct_questionnaire_access(request, pk=None, slug=None):
    """
    Direct access to a questionnaire via QR code or URL
    Can be accessed by UUID or slug
    """
    # Get the questionnaire by UUID or slug
    if pk:
        questionnaire = get_object_or_404(Questionnaire, pk=pk)
    elif slug:
        questionnaire = get_object_or_404(Questionnaire, slug=slug)
    else:
        messages.error(request, "Invalid questionnaire link.")
        return redirect('core:home')

    # Check if this is a preview request (from admin/creator)
    is_preview = request.GET.get('preview') == 'true' or request.GET.get('mode') == 'preview'
    is_creator = request.user.is_authenticated and request.user == questionnaire.created_by
    is_admin = request.user.is_authenticated and request.user.is_staff

    # Check if questionnaire is active (skip check for preview mode or if user is creator/admin)
    if questionnaire.status != 'active' and not (is_preview or is_creator or is_admin):
        messages.error(request, "This questionnaire is not currently active.")
        return redirect('core:home')

    # Check if authentication is required (skip for preview mode or if user is creator/admin)
    if questionnaire.requires_auth and not request.user.is_authenticated and not (is_preview or is_creator or is_admin):
        messages.error(request, "You need to be logged in to respond to this questionnaire.")
        return redirect('account_login')

    # Track QR code access if accessed via QR code
    qr_code_id = request.GET.get('qr')
    if qr_code_id:
        try:
            qr_code = questionnaire.qr_codes.get(pk=qr_code_id, is_active=True)
            qr_code.increment_access_count()
        except:
            # If QR code doesn't exist or isn't active, just continue
            pass

    # Redirect to the questionnaire response page
    return redirect('feedback:respond_to_questionnaire', questionnaire_pk=questionnaire.pk)

@login_required
def update_notes(request, pk):
    """
    Update notes for a response
    """
    # Get the response from the database
    response = get_object_or_404(Response, pk=pk)

    # Check if the user has permission to update notes for this response
    if response.survey.organization:
        # If the response is for an organization questionnaire, check if the user is a member
        user_is_member = response.survey.organization.members.filter(user=request.user).exists()
        if not user_is_member and response.user != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to update notes for this response.")
            return redirect('feedback:response_list')

    # If the response is a personal questionnaire, check if the user is the creator or respondent
    elif response.survey.created_by != request.user and response.user != request.user and not request.user.is_staff:
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
    Generate analysis for a response
    """
    # Get the response from the database
    response = get_object_or_404(Response.objects.select_related('survey'), pk=pk)

    # Check if the user has permission to generate analysis for this response
    if response.survey.organization:
        # If the response is for an organization questionnaire, check if the user is a member
        user_is_member = response.survey.organization.members.filter(user=request.user).exists()
        if not user_is_member and response.user != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to generate analysis for this response.")
            return redirect('feedback:response_list')

    # If the response is a personal questionnaire, check if the user is the creator or respondent
    elif response.survey.created_by != request.user and response.user != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to generate analysis for this response.")
        return redirect('feedback:response_list')

    # Check if analysis already exists
    try:
        analysis = response.analysis
        messages.info(request, "Analysis already exists for this response.")
    except AIAnalysis.DoesNotExist:
        # Get all answers for this response
        answers = Answer.objects.filter(response=response).select_related('question', 'selected_choice').prefetch_related('multiple_choices')

        # Generate analysis based on the questionnaire category and answers
        if response.survey.category == 'anxiety':
            summary = "Anxiety Assessment Analysis"
            if response.score < 5:
                detailed_analysis = "The patient shows minimal anxiety symptoms."
                recommendations = "No intervention needed at this time."
            elif response.score < 10:
                detailed_analysis = "The patient shows mild anxiety symptoms."
                recommendations = "Consider follow-up assessment in 4-6 weeks."
            elif response.score < 15:
                detailed_analysis = "The patient shows moderate anxiety symptoms."
                recommendations = "Consider referral to mental health professional."
            else:
                detailed_analysis = "The patient shows severe anxiety symptoms."
                recommendations = "Immediate referral to mental health professional recommended."

        elif response.survey.category == 'depression':
            summary = "Depression Screening Analysis"
            if response.score < 5:
                detailed_analysis = "The patient shows minimal depression symptoms."
                recommendations = "No intervention needed at this time."
            elif response.score < 10:
                detailed_analysis = "The patient shows mild depression symptoms."
                recommendations = "Consider follow-up assessment in 4-6 weeks."
            elif response.score < 15:
                detailed_analysis = "The patient shows moderate depression symptoms."
                recommendations = "Consider referral to mental health professional."
            else:
                detailed_analysis = "The patient shows severe depression symptoms."
                recommendations = "Immediate referral to mental health professional recommended."

        else:
            summary = f"Analysis for {response.survey.title}"
            detailed_analysis = "This is a detailed analysis of the response."
            recommendations = "These are the recommendations based on the response."

        # Create a new analysis
        analysis = AIAnalysis(
            response=response,
            summary=summary,
            detailed_analysis=detailed_analysis,
            recommendations=recommendations,
            raw_data={},
            created_by=request.user
        )
        analysis.save()
        messages.success(request, "Analysis generated successfully.")

    return redirect('feedback:response_detail', pk=pk)

@login_required
def export_response(request, pk):
    """
    Export a response to a CSV file
    """
    # Get the response from the database
    response = get_object_or_404(Response.objects.select_related('survey', 'user'), pk=pk)

    # Check if the user has permission to export this response
    if response.survey.organization:
        # If the response is for an organization questionnaire, check if the user is a member
        user_is_member = response.survey.organization.members.filter(user=request.user).exists()
        if not user_is_member and response.user != request.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to export this response.")
            return redirect('feedback:response_list')

    # If the response is a personal questionnaire, check if the user is the creator or respondent
    elif response.survey.created_by != request.user and response.user != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to export this response.")
        return redirect('feedback:response_list')

    # Get all answers for this response
    answers = Answer.objects.filter(response=response).select_related('question', 'selected_choice').prefetch_related('multiple_choices')

    # Create a CSV response
    http_response = HttpResponse(content_type='text/csv')
    http_response['Content-Disposition'] = f'attachment; filename="response_{response.id}.csv"'

    # Create a CSV writer
    writer = csv.writer(http_response)

    # Write the header row
    writer.writerow(['Questionnaire', 'Response ID', 'Respondent', 'Status', 'Created At', 'Completed At', 'Score', 'Risk Level'])

    # Write the response data
    writer.writerow([
        response.survey.title,
        response.id,
        response.user.email if response.user else (response.patient_email or 'Anonymous'),
        response.get_status_display(),
        response.created_at,
        response.completed_at,
        response.score,
        response.get_risk_level_display()
    ])

    # Write a blank row
    writer.writerow([])

    # Write the answers header
    writer.writerow(['Question', 'Answer', 'Score'])

    # Write the answers
    for answer in answers:
        writer.writerow([
            answer.question.text,
            answer.get_answer_display() or '',
            answer.score or ''
        ])

    return http_response
