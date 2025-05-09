from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import csv
import json

from .models import Response, Answer
from .models.base import AIAnalysis
# Import models from surveys app
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

    # Flag to indicate if this is a patient questionnaire (requires bio data)
    # For now, we'll treat all questionnaires as patient questionnaires to ensure bio data is collected
    is_patient_questionnaire = True  # Force bio data collection for all questionnaires

    # Check if the questionnaire is active (skip check for preview mode or if user is creator/admin)
    if questionnaire.status != 'active' and not (is_preview or is_creator or is_admin):
        messages.error(request, "This questionnaire is not currently active.")
        return redirect('surveys:survey_list')

    # For patient flow, we want to allow anonymous access regardless of settings
    # Check if this is a direct access from QR code or URL
    is_direct_access = request.GET.get('direct') == 'true' or 'direct' in request.session

    # Log the direct access status for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Respond to questionnaire: direct={is_direct_access}, session_direct={'direct' in request.session}, GET_direct={request.GET.get('direct')}")
    logger.info(f"Session keys: {list(request.session.keys())}")
    logger.info(f"GET params: {dict(request.GET.items())}")

    # If this is direct access or we have the bypass flag, skip all authentication checks
    if is_direct_access or request.session.get('bypass_auth_redirect', False):
        # This is a direct access, so we allow anonymous access
        # Make sure the session flags are set (in case direct=true was passed in URL but not via session)
        request.session['direct'] = True
        request.session['bypass_auth_redirect'] = True
        request.session['is_patient_questionnaire'] = True
        logger.info("Set session flags for direct access in respond_to_questionnaire view")
    else:
        # Apply normal authentication rules for non-direct access
        # Check if authentication is required (skip for preview mode or if user is creator/admin)
        if questionnaire.requires_auth and not request.user.is_authenticated and not (is_preview or is_creator or is_admin):
            messages.error(request, "You need to be logged in to respond to this questionnaire.")
            return redirect('account_login')

        # Check if anonymous responses are allowed
        if not questionnaire.allow_anonymous and not request.user.is_authenticated:
            messages.error(request, "Anonymous responses are not allowed for this questionnaire.")
            return redirect('account_login')

        # Check if this is an organization-specific questionnaire
        if questionnaire.organization and not (is_preview or is_creator or is_admin):
            # If user is authenticated, check if they are a member of the organization
            if request.user.is_authenticated:
                user_is_member = questionnaire.organization.members.filter(user=request.user, is_active=True).exists()
                if not user_is_member:
                    messages.error(request, "You don't have permission to access this questionnaire.")
                    return render(request, 'errors/organization_access_denied.html')

    # Get all questions for this questionnaire
    questions = Question.objects.filter(survey=questionnaire).order_by('order').prefetch_related('choices')

    # Check if bio data has been collected from the QR code flow
    bio_data_collected = request.session.get('bio_data_collected', False)

    # For direct access, we might want to simplify the bio data collection
    # or skip it entirely for a more streamlined patient experience
    is_simplified_flow = is_direct_access or request.session.get('bypass_auth_redirect', False)

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

        # If bio data was collected in the QR code flow, add it to the response
        if bio_data_collected:
            response.patient_email = request.session.get('patient_email', '')
            response.patient_age = request.session.get('patient_age')
            response.patient_gender = request.session.get('patient_gender', '')

        # For direct access, we might pre-set some values to simplify the flow
        if is_simplified_flow and not bio_data_collected:
            # Set a flag to indicate we're using simplified bio data collection
            request.session['simplified_bio_data'] = True

        response.save()

        # Store the response ID in the session
        request.session['current_response_id'] = str(response.id)

        # Only record the start time if bio data has been collected
        # This ensures we don't start timing until the patient actually starts answering questions
        if bio_data_collected:
            from django.utils import timezone
            request.session['response_start_time'] = timezone.now().timestamp()

        return render(request, 'feedback/respond_to_questionnaire.html', {
            'questionnaire': questionnaire,
            'questions': questions,
            'response': response,
            'is_patient_questionnaire': is_patient_questionnaire,
            'bio_data_collected': bio_data_collected,
            'is_simplified_flow': is_simplified_flow
        })

    # Process the form submission if this is a POST request
    elif request.method == 'POST':
        # Check if this is a bio data submission
        if 'submit_bio_data' in request.POST and is_patient_questionnaire:
            # Get the response ID from the session
            response_id = request.session.get('current_response_id')
            if not response_id:
                messages.error(request, "Your session has expired. Please start again.")
                return redirect('feedback:respond_to_questionnaire', questionnaire_pk=questionnaire_pk)

            # Get the response
            response = get_object_or_404(Response, pk=response_id)

            # Validate required bio data fields
            patient_email = request.POST.get('patient_email', '').strip()
            patient_age = request.POST.get('patient_age', '').strip()
            patient_gender = request.POST.get('patient_gender', '').strip()

            # Check if all required fields are provided
            bio_data_error = False
            bio_data_values = {
                'email': patient_email,
                'age': patient_age,
                'gender': patient_gender
            }

            if not patient_email:
                bio_data_error = True
                messages.error(request, "Email is required.")

            if not patient_age:
                bio_data_error = True
                messages.error(request, "Age is required.")

            if not patient_gender:
                bio_data_error = True
                messages.error(request, "Gender is required.")

            # If validation fails, return to the form with errors
            if bio_data_error:
                return render(request, 'feedback/respond_to_questionnaire.html', {
                    'questionnaire': questionnaire,
                    'questions': questions,
                    'response': response,
                    'is_patient_questionnaire': is_patient_questionnaire,
                    'bio_data_collected': False,
                    'bio_data_error': True,
                    'bio_data_values': bio_data_values,
                    'is_simplified_flow': is_simplified_flow
                })

            # Update bio data
            response.patient_email = patient_email

            # Handle patient age
            try:
                response.patient_age = int(patient_age)
                if response.patient_age < 1 or response.patient_age > 120:
                    messages.error(request, "Age must be between 1 and 120.")
                    return render(request, 'feedback/respond_to_questionnaire.html', {
                        'questionnaire': questionnaire,
                        'questions': questions,
                        'response': response,
                        'is_patient_questionnaire': is_patient_questionnaire,
                        'bio_data_collected': False,
                        'bio_data_error': True,
                        'bio_data_values': bio_data_values,
                        'is_simplified_flow': is_simplified_flow
                    })
            except ValueError:
                messages.error(request, "Age must be a valid number.")
                return render(request, 'feedback/respond_to_questionnaire.html', {
                    'questionnaire': questionnaire,
                    'questions': questions,
                    'response': response,
                    'is_patient_questionnaire': is_patient_questionnaire,
                    'bio_data_collected': False,
                    'bio_data_error': True,
                    'bio_data_values': bio_data_values,
                    'is_simplified_flow': is_simplified_flow
                })

            response.patient_gender = patient_gender
            response.save()

            # Set flag to indicate bio data has been collected
            request.session['bio_data_collected'] = True

            # Store bio data in session
            request.session['patient_email'] = response.patient_email
            request.session['patient_age'] = response.patient_age
            request.session['patient_gender'] = response.patient_gender

            # Start the timer now that bio data has been collected
            from django.utils import timezone
            request.session['response_start_time'] = timezone.now().timestamp()

            # Redirect back to the same page to show questions
            messages.success(request, "Patient information saved. Please complete the questionnaire.")
            return redirect('feedback:respond_to_questionnaire', questionnaire_pk=questionnaire_pk)

        # Get the response ID from the session
        response_id = request.session.get('current_response_id')
        if not response_id:
            messages.error(request, "Your session has expired. Please start again.")
            return redirect('feedback:respond_to_questionnaire', questionnaire_pk=questionnaire_pk)

        # Get the response
        response = get_object_or_404(Response, pk=response_id)

        # Update demographic information if not already set
        if not response.patient_email:
            response.patient_email = request.POST.get('patient_email', '')

        if response.patient_age is None:
            # Handle patient age - convert to integer if provided, otherwise set to None
            patient_age = request.POST.get('patient_age', '')
            if patient_age and patient_age.strip():
                try:
                    response.patient_age = int(patient_age)
                except ValueError:
                    # If conversion fails, set to None
                    response.patient_age = None

        if not response.patient_gender:
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
            try:
                if question.question_type == 'text' or question.question_type == 'textarea':
                    answer.text_answer = request.POST.get(answer_key, '')
                    answer.save()  # Save before adding many-to-many relationships

                elif question.question_type == 'single_choice':
                    choice_id = request.POST.get(answer_key)
                    if choice_id:
                        try:
                            answer.selected_choice = get_object_or_404(QuestionChoice, pk=choice_id)
                        except:
                            messages.error(request, f"Invalid choice selected for question: {question.text}", extra_tags=f"question_{question.id}")
                    elif question.required:
                        messages.error(request, f"Please select an option for question: {question.text}", extra_tags=f"question_{question.id}")
                    answer.save()  # Save before adding many-to-many relationships

                elif question.question_type == 'multiple_choice':
                    # Save first to get an ID for the many-to-many relationship
                    answer.save()

                    # Clear existing choices if updating
                    if existing_answer:
                        answer.multiple_choices.clear()

                    # Add new choices
                    choice_ids = request.POST.getlist(answer_key)

                    # Check if required and no choices selected
                    if not choice_ids and question.required:
                        messages.error(request, f"Please select at least one option for question: {question.text}", extra_tags=f"question_{question.id}")

                    for choice_id in choice_ids:
                        try:
                            choice = get_object_or_404(QuestionChoice, pk=choice_id)
                            answer.multiple_choices.add(choice)
                        except:
                            messages.error(request, f"Invalid choice selected for question: {question.text}", extra_tags=f"question_{question.id}")

                elif question.question_type == 'number' or question.question_type == 'scale':
                    try:
                        answer.numeric_value = float(request.POST.get(answer_key, 0))
                    except ValueError:
                        # Handle invalid number input
                        messages.error(request, f"Invalid number format for question: {question.text}", extra_tags=f"question_{question.id}")
                        # Set a default value
                        answer.numeric_value = 0
                    answer.save()  # Save before adding many-to-many relationships

                elif question.question_type == 'date':
                    try:
                        date_str = request.POST.get(answer_key, '')
                        if date_str:
                            from datetime import datetime
                            answer.date_value = datetime.strptime(date_str, '%Y-%m-%d').date()
                        answer.save()
                    except ValueError:
                        messages.error(request, f"Invalid date format for question: {question.text}", extra_tags=f"question_{question.id}")
                        answer.save()

                elif question.question_type == 'time':
                    try:
                        time_str = request.POST.get(answer_key, '')
                        if time_str:
                            from datetime import datetime
                            answer.time_value = datetime.strptime(time_str, '%H:%M').time()
                        answer.save()
                    except ValueError:
                        messages.error(request, f"Invalid time format for question: {question.text}", extra_tags=f"question_{question.id}")
                        answer.save()

                elif question.question_type == 'country':
                    answer.text_answer = request.POST.get(answer_key, '')
                    answer.save()

                else:
                    # Default fallback for any other question type
                    answer.text_answer = request.POST.get(answer_key, '')
                    answer.save()

            except Exception as e:
                # Log the error but continue processing
                print(f"Error processing answer for question {question.id}: {str(e)}")
                messages.error(request, f"Error processing answer for question: {question.text}", extra_tags=f"question_{question.id}")
                # Create a basic answer to avoid data loss
                answer.text_answer = request.POST.get(answer_key, '')
                answer.save()

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

        # Calculate completion time if we have a start time in session
        if request.session.get('response_start_time'):
            from django.utils import timezone
            start_time = request.session.get('response_start_time')
            end_time = timezone.now().timestamp()
            completion_time_seconds = int(end_time - start_time)

            # Update the response with the completion time
            response.completion_time = completion_time_seconds
            response.save(update_fields=['completion_time'])

        # Keep the response ID in session for the completion page
        # It will be cleared after showing the completion page

        # Show success message
        messages.success(request, 'Thank you for your response!')
        # Use the full URL pattern to avoid namespace issues
        return redirect('/responses/complete/')

    return render(request, 'feedback/respond_to_questionnaire.html', {'questionnaire': questionnaire, 'questions': questions})

def response_complete(request):
    """
    Thank you page after completing a questionnaire
    """
    # Get the most recent completed response for this user/session
    response = None

    # Get the response ID from the session if available
    response_id = request.session.get('current_response_id')
    if response_id:
        try:
            response = Response.objects.get(pk=response_id)
        except Response.DoesNotExist:
            response = None

    # If no response found from session, try to find by user if authenticated
    if not response and request.user.is_authenticated:
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

    # Calculate completion time if we have a response and start time in session
    if response and request.session.get('response_start_time'):
        from django.utils import timezone
        start_time = request.session.get('response_start_time')
        end_time = timezone.now().timestamp()
        completion_time_seconds = int(end_time - start_time)

        # Update the response with the completion time if not already set
        if not response.completion_time:
            response.completion_time = completion_time_seconds
            response.save(update_fields=['completion_time'])

    # Clear session data related to the response
    for key in ['current_response_id', 'response_start_time', 'bio_data_collected',
                'patient_email', 'patient_age', 'patient_gender']:
        if key in request.session:
            del request.session[key]

    return render(request, 'feedback/response_complete.html', {'response': response})


def direct_questionnaire_access(request, pk=None, slug=None):
    """
    Direct access to a questionnaire via QR code or URL
    Can be accessed by UUID or slug
    For patient flow, we bypass all authentication checks
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Direct questionnaire access requested with pk={pk}, slug={slug}")

    # Get the questionnaire by UUID or slug
    questionnaire = None

    if pk:
        # First try: exact match by primary key
        try:
            questionnaire = Questionnaire.objects.get(pk=pk)
            logger.info(f"Found questionnaire by exact ID match: {questionnaire.id}")
        except Questionnaire.DoesNotExist:
            logger.info(f"No questionnaire found with exact ID: {pk}")

            # Second try: partial match by ID containing the UUID
            try:
                questionnaires = Questionnaire.objects.filter(id__icontains=pk)
                if questionnaires.exists():
                    questionnaire = questionnaires.first()
                    logger.info(f"Found questionnaire by partial ID match: {questionnaire.id}")
                else:
                    logger.warning(f"No questionnaire found with ID containing: {pk}")
            except Exception as e:
                logger.error(f"Error finding questionnaire by partial ID: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error finding questionnaire by ID: {str(e)}")

    # If we still don't have a questionnaire and a slug was provided, try that
    if not questionnaire and slug:
        try:
            questionnaire = Questionnaire.objects.get(slug=slug)
            logger.info(f"Found questionnaire by slug: {questionnaire.slug}")
        except Questionnaire.DoesNotExist:
            logger.warning(f"No questionnaire found with slug: {slug}")
        except Exception as e:
            logger.error(f"Error finding questionnaire by slug: {str(e)}")

    # If we still don't have a questionnaire, show a custom error page
    if not questionnaire:
        logger.warning(f"No questionnaire found for ID: {pk}")

        try:
            # Get a few active questionnaires to show as alternatives
            active_questionnaires = Questionnaire.objects.filter(status='active').order_by('-created_at')[:5]

            # Render the custom error page
            return render(request, 'errors/questionnaire_not_found.html', {
                'uuid': pk,
                'active_questionnaires': active_questionnaires
            })
        except Exception as e:
            logger.error(f"Error rendering questionnaire not found page: {str(e)}")
            messages.error(request, "The requested questionnaire could not be found.")
            return redirect('core:home')

    # Check if the questionnaire is active
    if questionnaire.status != 'active':
        logger.warning(f"Questionnaire {questionnaire.id} is not active (status: {questionnaire.status})")
        messages.error(request, "This questionnaire is not currently active.")
        return redirect('core:home')

    # Track QR code access if accessed via QR code
    qr_code_id = request.GET.get('qr')
    if qr_code_id:
        try:
            qr_code = questionnaire.qr_codes.get(pk=qr_code_id, is_active=True)
            qr_code.increment_access_count()
            logger.info(f"Tracked QR code access: {qr_code_id}")
        except Exception as e:
            logger.warning(f"Failed to track QR code access: {str(e)}")

    # Set session flags for direct access
    request.session['direct'] = True
    request.session['bypass_auth_redirect'] = True
    request.session['is_patient_questionnaire'] = True
    logger.info("Set session flags for direct access")

    # Construct the redirect URL - try multiple approaches for robustness
    try:
        # First try: Use Django's reverse URL resolution
        from django.urls import reverse
        redirect_url = reverse('feedback:respond_to_questionnaire', kwargs={'questionnaire_pk': questionnaire.pk})
        logger.info(f"Using reverse URL: {redirect_url}")
    except Exception as e:
        logger.warning(f"Reverse URL resolution failed: {str(e)}")

        # Second try: Construct URL manually with direct flag
        redirect_url = f'/responses/questionnaire/{questionnaire.pk}/respond/?direct=true'
        logger.info(f"Using manual URL: {redirect_url}")

    # Add direct flag to URL if not already present
    if 'direct=true' not in redirect_url:
        redirect_url = f"{redirect_url}{'&' if '?' in redirect_url else '?'}direct=true"

    logger.info(f"Redirecting to: {redirect_url}")
    return redirect(redirect_url)

def debug_questionnaire(request, pk=None):
    """
    Debug view to help diagnose questionnaire access issues
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Debug questionnaire access requested with pk={pk}")

    data = {
        'request_info': {
            'uuid_provided': pk,
            'method': request.method,
            'path': request.path,
            'GET_params': dict(request.GET.items()),
            'session_keys': list(request.session.keys()),
        },
        'system_info': {
            'django_version': __import__('django').get_version(),
            'python_version': __import__('sys').version,
        }
    }

    # Try exact match by primary key
    try:
        questionnaire = Questionnaire.objects.get(pk=pk)
        data['exact_match'] = {
            'success': True,
            'questionnaire': {
                'id': str(questionnaire.id),
                'title': questionnaire.title,
                'status': questionnaire.status,
                'created_at': str(questionnaire.created_at) if hasattr(questionnaire, 'created_at') else None,
                'organization': str(questionnaire.organization.name) if questionnaire.organization else None,
                'is_active': questionnaire.is_active if hasattr(questionnaire, 'is_active') else None,
                'question_count': questionnaire.questions.count(),
                'response_count': getattr(questionnaire, 'response_count', 'N/A'),
            }
        }

        # Get URL for this questionnaire
        try:
            from django.urls import reverse
            data['exact_match']['questionnaire']['respond_url'] = reverse(
                'feedback:respond_to_questionnaire',
                kwargs={'questionnaire_pk': questionnaire.pk}
            )
        except Exception as e:
            data['exact_match']['questionnaire']['respond_url_error'] = str(e)

        # Add direct URL
        data['exact_match']['questionnaire']['direct_url'] = f"/q/{questionnaire.pk}/"

    except Questionnaire.DoesNotExist:
        data['exact_match'] = {
            'success': False,
            'message': 'No questionnaire found with exact ID match'
        }
    except Exception as e:
        data['exact_match'] = {
            'success': False,
            'message': f'Error: {str(e)}'
        }

    # Try partial match
    try:
        questionnaires = Questionnaire.objects.filter(id__icontains=pk)
        if questionnaires.exists():
            data['partial_matches'] = {
                'success': True,
                'count': questionnaires.count(),
                'questionnaires': []
            }

            for q in questionnaires:
                data['partial_matches']['questionnaires'].append({
                    'id': str(q.id),
                    'title': q.title,
                    'status': q.status,
                    'direct_url': f"/q/{q.pk}/",
                })
        else:
            data['partial_matches'] = {
                'success': False,
                'message': 'No questionnaires found with partial ID match'
            }
    except Exception as e:
        data['partial_matches'] = {
            'success': False,
            'message': f'Error: {str(e)}'
        }

    # Get all active questionnaires
    try:
        active_questionnaires = Questionnaire.objects.filter(status='active').order_by('-created_at')[:5]
        data['active_questionnaires'] = {
            'success': True,
            'count': active_questionnaires.count(),
            'questionnaires': []
        }

        for q in active_questionnaires:
            data['active_questionnaires']['questionnaires'].append({
                'id': str(q.id),
                'title': q.title,
                'direct_url': f"/q/{q.pk}/",
            })
    except Exception as e:
        data['active_questionnaires'] = {
            'success': False,
            'message': f'Error: {str(e)}'
        }

    # Get URL patterns
    try:
        from django.urls import get_resolver
        resolver = get_resolver()
        patterns = []

        for pattern_list in resolver.url_patterns:
            if hasattr(pattern_list, 'url_patterns'):
                for pattern in pattern_list.url_patterns:
                    if 'questionnaire' in str(pattern) or 'survey' in str(pattern):
                        patterns.append(str(pattern.pattern))

        data['url_patterns'] = patterns
    except Exception as e:
        data['url_patterns_error'] = str(e)

    return JsonResponse(data)

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
