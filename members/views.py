import time
import random
import uuid
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseRedirect, HttpResponse, FileResponse
from django.urls import reverse
from django.db.models import Q, Avg, Count, Sum
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.conf import settings

from surveys.models import Questionnaire, Question, QRCode
from feedback.models import Response, Answer, AIAnalysis
from .models import Member, MemberAccess
from core.pdf_utils import pdf_generator

def member_access_form(request):
    """
    Display a form for members to enter their access code and member number
    """
    if request.method == 'POST':
        access_code = request.POST.get('access_code')
        member_number = request.POST.get('member_number')

        # Validate input
        if not access_code or not member_number:
            messages.error(request, "Please enter both access code and member number.")
            return render(request, 'members/access_form.html')

        # Check if the member exists
        try:
            member = Member.objects.get(member_number=member_number, is_active=True)
        except Member.DoesNotExist:
            messages.error(request, "Invalid member number. Please check and try again.")
            return render(request, 'members/access_form.html')

        # Check if the access code is valid
        try:
            # Get the most recent access with this code
            member_access = MemberAccess.objects.filter(
                member=member,
                access_code=access_code,
                is_used=False
            ).order_by('-created_at').first()

            if not member_access:
                raise MemberAccess.DoesNotExist

            # Check if the access code has expired
            if member_access.expires_at and member_access.expires_at < timezone.now():
                messages.error(request, "This access code has expired. Please contact your administrator.")
                return render(request, 'members/access_form.html')

            # Store member and questionnaire info in session
            request.session['member_id'] = str(member.id)
            request.session['questionnaire_id'] = str(member_access.questionnaire.id)
            request.session['access_id'] = str(member_access.id)

            # Redirect to the questionnaire response page
            return redirect('members:questionnaire_response')

        except MemberAccess.DoesNotExist:
            messages.error(request, "Invalid access code. Please check and try again.")
            return render(request, 'members/access_form.html')

    return render(request, 'members/access_form.html')

def qr_member_access(request, qr_code_id):
    """
    Display a form for members to enter their access code and member number after scanning a QR code
    The QR code ID is passed in the URL
    """
    # Get the QR code
    try:
        qr_code = QRCode.objects.get(pk=qr_code_id, is_active=True)
    except QRCode.DoesNotExist:
        messages.error(request, "Invalid QR code. Please try again or contact your administrator.")
        return redirect('core:home')

    # Check if the QR code has expired
    if qr_code.expires_at and qr_code.expires_at < timezone.now():
        messages.error(request, "This QR code has expired. Please contact your administrator.")
        return redirect('core:home')

    # Get the questionnaire
    questionnaire = qr_code.survey

    # Check if the questionnaire is active
    if not questionnaire or not questionnaire.is_active:
        messages.error(request, "The questionnaire associated with this QR code is not available.")
        return redirect('core:home')

    # Increment the access count for the QR code
    qr_code.increment_access_count()

    # Store QR code info in session
    request.session['qr_code_id'] = str(qr_code.id)
    request.session['qr_questionnaire_id'] = str(questionnaire.id)

    if request.method == 'POST':
        member_number = request.POST.get('member_number')

        # Validate input
        if not member_number:
            messages.error(request, "Please enter your member number.")
            return render(request, 'members/qr_access_form.html', {'qr_code': qr_code, 'questionnaire': questionnaire})

        # Check if the member exists
        try:
            member = Member.objects.get(member_number=member_number, is_active=True)
        except Member.DoesNotExist:
            messages.error(request, "Invalid member number. Please check and try again.")
            return render(request, 'members/qr_access_form.html', {'qr_code': qr_code, 'questionnaire': questionnaire})

        # Check if the member has access to this questionnaire
        # First, check if there's an existing access code
        member_access = MemberAccess.objects.filter(
            member=member,
            questionnaire=questionnaire,
            is_used=False
        ).order_by('-created_at').first()

        # If no access exists, create one
        if not member_access:
            # Generate a random access code
            access_code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=8))

            # Create the access
            member_access = MemberAccess.objects.create(
                member=member,
                questionnaire=questionnaire,
                access_code=access_code,
                expires_at=timezone.now() + timedelta(days=1)  # Expires in 1 day
            )

        # Store member and questionnaire info in session
        request.session['member_id'] = str(member.id)
        request.session['questionnaire_id'] = str(questionnaire.id)
        request.session['access_id'] = str(member_access.id)

        # Redirect to the questionnaire response page
        return redirect('members:questionnaire_response')

    return render(request, 'members/qr_access_form.html', {'qr_code': qr_code, 'questionnaire': questionnaire})

def questionnaire_response(request):
    """
    Display the questionnaire for the member to respond to
    """
    # Check if the member is authenticated
    member_id = request.session.get('member_id')
    questionnaire_id = request.session.get('questionnaire_id')
    access_id = request.session.get('access_id')

    if not member_id or not questionnaire_id or not access_id:
        messages.error(request, "Please enter your access code and member number first.")
        return redirect('members:member_access_form')

    # Get the member, questionnaire, and access
    member = get_object_or_404(Member, id=member_id)
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    member_access = get_object_or_404(MemberAccess, id=access_id)

    # Get all questions for this questionnaire
    questions = Question.objects.filter(survey=questionnaire).order_by('order').prefetch_related('choices')

    # Debug information
    print(f"Questionnaire: {questionnaire.title} (ID: {questionnaire.id})")
    print(f"Questions count: {questions.count()}")
    for q in questions:
        print(f"Question: {q.text} (ID: {q.id}, Type: {q.question_type})")
        print(f"Choices count: {q.choices.count()}")

    # Handle form submission
    if request.method == 'POST':
        # Record start time if not already in session
        start_time = request.session.get('response_start_time')
        if not start_time:
            messages.error(request, "Session expired. Please start again.")
            return redirect('members:member_access_form')

        # Calculate completion time
        completion_time = int(time.time() - start_time)

        # Create a new response
        response = Response(
            survey=questionnaire,
            patient_identifier=member.member_number,
            patient_email=member.email,
            patient_name=member.name,
            status='completed',
            completion_time=completion_time,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            organization=member.organization
        )
        response.save()

        # Process each question
        total_score = 0
        for question in questions:
            answer_key = f'question_{question.id}'

            # Skip if the question wasn't answered and is not required
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
                    answer.selected_choice = get_object_or_404(question.choices, pk=choice_id)
                    if answer.selected_choice.score is not None:
                        answer.score = answer.selected_choice.score
                        total_score += answer.score

            elif question.question_type == 'checkbox':
                choice_ids = request.POST.getlist(answer_key)
                if choice_ids:
                    choices = question.choices.filter(pk__in=choice_ids)
                    answer.save()  # Save first to establish M2M relationship
                    answer.multiple_choices.set(choices)

                    # Calculate score for multiple choices
                    choice_score = sum(choice.score or 0 for choice in choices)
                    answer.score = choice_score
                    total_score += choice_score

            elif question.question_type == 'number':
                try:
                    numeric_value = float(request.POST.get(answer_key, 0))
                    answer.numeric_value = numeric_value

                    # Score based on numeric value if scoring is configured
                    if hasattr(question, 'scoring_config') and question.scoring_config:
                        config = question.scoring_config
                        if config.scoring_type == 'range':
                            for range_item in config.ranges:
                                if range_item['min'] <= numeric_value <= range_item['max']:
                                    answer.score = range_item['score']
                                    total_score += answer.score
                                    break
                except ValueError:
                    pass

            # Save the answer
            answer.save()

        # Update the response with the total score
        response.score = total_score

        # Determine risk level based on score
        if hasattr(questionnaire, 'scoring_config') and questionnaire.scoring_config:
            config = questionnaire.scoring_config
            for level in config.risk_levels:
                if level['min'] <= total_score <= level['max']:
                    response.risk_level = level['level']
                    break

        response.save()

        # Mark the access as used
        member_access.is_used = True
        member_access.used_at = timezone.now()
        member_access.save()

        # Store the response ID in the session for the completion page
        request.session['response_id'] = str(response.id)

        # Clear other session data
        if 'response_start_time' in request.session:
            del request.session['response_start_time']

        # Redirect to the completion page
        return redirect('members:response_complete')

    # For GET requests, create a new session with start time
    request.session['response_start_time'] = time.time()

    return render(request, 'members/questionnaire_response.html', {
        'questionnaire': questionnaire,
        'questions': questions,
        'member': member
    })

def response_complete(request):
    """
    Display the completion page with time taken, scores, and questions answered
    """
    # Check if the response ID is in the session
    response_id = request.session.get('response_id')
    if not response_id:
        messages.error(request, "No response found. Please start again.")
        return redirect('members:member_access_form')

    # Get the response
    response = get_object_or_404(Response, id=response_id)

    # Get the answers
    answers = Answer.objects.filter(response=response).select_related('question', 'selected_choice')

    # Clear session data
    for key in ['member_id', 'questionnaire_id', 'access_id', 'response_id']:
        if key in request.session:
            del request.session[key]

    return render(request, 'members/response_complete.html', {
        'response': response,
        'answers': answers
    })

# Analytics Views

def analytics_dashboard(request):
    """
    Display the analytics dashboard for members
    """
    # Get the member from the session or request
    member_id = request.session.get('member_id')
    member = None

    if member_id:
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            pass

    # Get all responses for this member
    responses = Response.objects.filter(patient_identifier=member.member_number if member else request.GET.get('member_number'))

    # Calculate statistics
    total_responses = responses.count()
    completed_responses = responses.filter(status='completed').count()
    average_score = responses.aggregate(Avg('score'))['score__avg'] or 0
    average_time = responses.aggregate(Avg('completion_time'))['completion_time__avg'] or 0

    # Get recent responses
    recent_responses = responses.order_by('-created_at')[:5]

    # Determine risk level based on average score
    risk_level = 'low'
    risk_description = "Based on your responses, you appear to be at low risk. Continue with your current practices and monitor regularly."

    if average_score < 50:
        risk_level = 'high'
        risk_description = "Your responses indicate a higher level of risk. We recommend reviewing the detailed assessment and considering the suggested actions."
    elif average_score < 70:
        risk_level = 'medium'
        risk_description = "Your responses indicate a moderate level of risk. Consider implementing some of the recommendations to improve your situation."

    return render(request, 'members/analytics_dashboard.html', {
        'total_responses': total_responses,
        'completed_responses': completed_responses,
        'average_score': average_score,
        'average_time': average_time,
        'recent_responses': recent_responses,
        'risk_level': risk_level,
        'risk_description': risk_description,
    })

def reports(request):
    """
    Display the reports page for members
    """
    # Get the member from the session or request
    member_id = request.session.get('member_id')
    member = None

    if member_id:
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            pass

    # Get filter parameters
    questionnaire_id = request.GET.get('questionnaire')
    date_range = request.GET.get('date_range', 'all')

    # Get all responses for this member
    responses = Response.objects.filter(patient_identifier=member.member_number if member else request.GET.get('member_number'))

    # Apply filters
    if questionnaire_id:
        responses = responses.filter(survey_id=questionnaire_id)

    if date_range != 'all':
        now = timezone.now()
        if date_range == 'week':
            start_date = now - timedelta(days=7)
        elif date_range == 'month':
            start_date = now - timedelta(days=30)
        elif date_range == 'quarter':
            start_date = now - timedelta(days=90)
        elif date_range == 'year':
            start_date = now - timedelta(days=365)

        responses = responses.filter(created_at__gte=start_date)

    # Get all questionnaires for the dropdown
    questionnaires = Questionnaire.objects.filter(
        id__in=responses.values_list('survey_id', flat=True)
    ).distinct()

    return render(request, 'members/reports.html', {
        'responses': responses,
        'questionnaires': questionnaires,
        'selected_questionnaire': questionnaire_id,
        'date_range': date_range,
    })

def risk_assessment(request):
    """
    Display the risk assessment page for members
    """
    # Get the member from the session or request
    member_id = request.session.get('member_id')
    member = None

    if member_id:
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            pass

    # Get all responses for this member
    responses = Response.objects.filter(patient_identifier=member.member_number if member else request.GET.get('member_number'))

    # Calculate average score
    average_score = responses.aggregate(Avg('score'))['score__avg'] or 0

    # Determine risk level based on average score
    risk_level = 'low'
    risk_description = "Based on your responses, you appear to be at low risk. Continue with your current practices and monitor regularly."

    if average_score < 50:
        risk_level = 'high'
        risk_description = "Your responses indicate a higher level of risk. We recommend reviewing the detailed assessment and considering the suggested actions."
    elif average_score < 70:
        risk_level = 'medium'
        risk_description = "Your responses indicate a moderate level of risk. Consider implementing some of the recommendations to improve your situation."

    # Sample risk factor scores - in a real app, these would be calculated from responses
    factor1_score = random.randint(60, 90)  # Emotional Well-being
    factor2_score = random.randint(40, 80)  # Stress Management
    factor3_score = random.randint(50, 85)  # Social Support

    # Sample factor descriptions
    factor1_description = "Your emotional well-being score indicates generally positive emotional health with some areas for improvement."
    factor2_description = "Your stress management score suggests moderate ability to cope with stress, but there may be room for developing additional coping strategies."
    factor3_description = "Your social support score indicates a moderate to strong support network, which is beneficial for overall well-being."

    # Sample recommendations
    recommendation1_title = "Practice Mindfulness"
    recommendation1_description = "Regular mindfulness meditation can help reduce stress and improve emotional regulation. Try starting with just 5 minutes daily."

    recommendation2_title = "Enhance Social Connections"
    recommendation2_description = "Schedule regular check-ins with friends and family to strengthen your support network."

    recommendation3_title = "Develop Healthy Routines"
    recommendation3_description = "Establish consistent sleep, exercise, and meal schedules to improve overall well-being and resilience."

    return render(request, 'members/risk_assessment.html', {
        'risk_level': risk_level,
        'risk_description': risk_description,
        'factor1_score': factor1_score,
        'factor1_description': factor1_description,
        'factor2_score': factor2_score,
        'factor2_description': factor2_description,
        'factor3_score': factor3_score,
        'factor3_description': factor3_description,
        'recommendation1_title': recommendation1_title,
        'recommendation1_description': recommendation1_description,
        'recommendation2_title': recommendation2_title,
        'recommendation2_description': recommendation2_description,
        'recommendation3_title': recommendation3_title,
        'recommendation3_description': recommendation3_description,
    })

def analysis(request):
    """
    Display the AI analysis page for members
    """
    # Get the member from the session or request
    member_id = request.session.get('member_id')
    member = None

    if member_id:
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            pass

    # Get all responses for this member
    responses = Response.objects.filter(patient_identifier=member.member_number if member else request.GET.get('member_number'))

    # Get the selected response
    response_id = request.GET.get('response')
    selected_response = None

    if response_id:
        try:
            selected_response = responses.get(id=response_id)

            # Check if AI analysis exists
            try:
                selected_response.ai_analysis = AIAnalysis.objects.get(response=selected_response)

                # Sample insights and recommendations for display
                selected_response.ai_analysis.insights = [
                    {
                        'title': 'Stress Management',
                        'description': 'Your responses indicate moderate stress levels. Consider incorporating stress reduction techniques into your daily routine.'
                    },
                    {
                        'title': 'Sleep Quality',
                        'description': 'Your sleep patterns show some disruption. Establishing a consistent sleep schedule may improve overall well-being.'
                    },
                    {
                        'title': 'Social Connections',
                        'description': 'You appear to have a good support network, which is beneficial for mental health and resilience.'
                    }
                ]

                selected_response.ai_analysis.recommendations = [
                    {
                        'title': 'Mindfulness Practice',
                        'description': 'Consider incorporating 5-10 minutes of mindfulness meditation daily to reduce stress and improve focus.'
                    },
                    {
                        'title': 'Sleep Hygiene',
                        'description': 'Establish a consistent sleep schedule and avoid screens for at least 30 minutes before bedtime.'
                    },
                    {
                        'title': 'Regular Exercise',
                        'description': 'Aim for at least 150 minutes of moderate exercise per week to improve mood and overall health.'
                    }
                ]

            except AIAnalysis.DoesNotExist:
                selected_response.ai_analysis = None

        except Response.DoesNotExist:
            selected_response = None

    return render(request, 'members/analysis.html', {
        'responses': responses,
        'selected_response': selected_response,
    })

def response_detail(request, pk):
    """
    Display the details of a specific response
    """
    # Get the response
    response = get_object_or_404(Response, pk=pk)

    # Get the answers
    answers = Answer.objects.filter(response=response).select_related('question', 'selected_choice')

    return render(request, 'members/response_detail.html', {
        'response': response,
        'answers': answers,
    })

def progress_report(request):
    """
    Display the progress report for members
    """
    # This is a placeholder for the progress report view
    return render(request, 'members/progress_report.html')

def trend_analysis(request):
    """
    Display the trend analysis for members
    """
    # This is a placeholder for the trend analysis view
    return render(request, 'members/trend_analysis.html')

def ai_insights(request):
    """
    Display the AI insights for members
    """
    # This is a placeholder for the AI insights view
    return render(request, 'members/ai_insights.html')

def download_report(request, pk):
    """
    Download a report for a specific response
    """
    # Get the response
    response_obj = get_object_or_404(Response, pk=pk)

    # Get the answers
    answers = Answer.objects.filter(response=response_obj).select_related('question', 'selected_choice')

    # Get enhanced scoring data if available
    from surveys.models import ResponseScore
    enhanced_score = ResponseScore.objects.filter(
        response=response_obj
    ).order_by('-calculated_at').first()

    # Prepare context for the PDF template
    context = {
        'response': response_obj,
        'answers': answers,
        'enhanced_score': enhanced_score,
        'now': timezone.now(),
    }

    # Generate the PDF
    filename = f"report_{response_obj.survey.title.replace(' ', '_')}_{pk}.pdf"
    return pdf_generator.generate_pdf_from_template('pdf/response_report.html', context, filename)

def download_analysis(request, pk):
    """
    Download an AI analysis for a specific response
    """
    # Get the response
    response_obj = get_object_or_404(Response, pk=pk)

    # Get the answers
    answers = Answer.objects.filter(response=response_obj).select_related('question', 'selected_choice')

    # Check if AI analysis exists
    try:
        ai_analysis = AIAnalysis.objects.get(response=response_obj)

        # Add sample insights and recommendations for display
        ai_analysis.insights = [
            {
                'title': 'Stress Management',
                'description': 'Your responses indicate moderate stress levels. Consider incorporating stress reduction techniques into your daily routine.'
            },
            {
                'title': 'Sleep Quality',
                'description': 'Your sleep patterns show some disruption. Establishing a consistent sleep schedule may improve overall well-being.'
            },
            {
                'title': 'Social Connections',
                'description': 'You appear to have a good support network, which is beneficial for mental health and resilience.'
            }
        ]

        ai_analysis.recommendations = [
            {
                'title': 'Mindfulness Practice',
                'description': 'Consider incorporating 5-10 minutes of mindfulness meditation daily to reduce stress and improve focus.'
            },
            {
                'title': 'Sleep Hygiene',
                'description': 'Establish a consistent sleep schedule and avoid screens for at least 30 minutes before bedtime.'
            },
            {
                'title': 'Regular Exercise',
                'description': 'Aim for at least 150 minutes of moderate exercise per week to improve mood and overall health.'
            }
        ]

        response_obj.ai_analysis = ai_analysis
    except AIAnalysis.DoesNotExist:
        # If no AI analysis exists, redirect to the response detail page
        messages.error(request, "No AI analysis available for this response.")
        return redirect('members:response_detail', pk=pk)

    # Prepare context for the PDF template
    context = {
        'response': response_obj,
        'answers': answers,
        'now': timezone.now(),
    }

    # Generate the PDF
    filename = f"analysis_{response_obj.survey.title.replace(' ', '_')}_{pk}.pdf"
    return pdf_generator.generate_pdf_from_template('pdf/ai_analysis.html', context, filename)

def download_risk_report(request):
    """
    Download a risk assessment report
    """
    # Get the member from the session or request
    member_id = request.session.get('member_id')
    member = None

    if member_id:
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            pass

    # Get all responses for this member
    responses = Response.objects.filter(patient_identifier=member.member_number if member else request.GET.get('member_number'))

    # Calculate average score
    average_score = responses.aggregate(Avg('score'))['score__avg'] or 0

    # Determine risk level based on average score
    risk_level = 'low'
    risk_description = "Based on your responses, you appear to be at low risk. Continue with your current practices and monitor regularly."

    if average_score < 50:
        risk_level = 'high'
        risk_description = "Your responses indicate a higher level of risk. We recommend reviewing the detailed assessment and considering the suggested actions."
    elif average_score < 70:
        risk_level = 'medium'
        risk_description = "Your responses indicate a moderate level of risk. Consider implementing some of the recommendations to improve your situation."

    # Sample risk factor scores - in a real app, these would be calculated from responses
    factor1_score = random.randint(60, 90)  # Emotional Well-being
    factor2_score = random.randint(40, 80)  # Stress Management
    factor3_score = random.randint(50, 85)  # Social Support

    # Sample factor descriptions
    factor1_description = "Your emotional well-being score indicates generally positive emotional health with some areas for improvement."
    factor2_description = "Your stress management score suggests moderate ability to cope with stress, but there may be room for developing additional coping strategies."
    factor3_description = "Your social support score indicates a moderate to strong support network, which is beneficial for overall well-being."

    # Sample recommendations
    recommendation1_title = "Practice Mindfulness"
    recommendation1_description = "Regular mindfulness meditation can help reduce stress and improve emotional regulation. Try starting with just 5 minutes daily."

    recommendation2_title = "Enhance Social Connections"
    recommendation2_description = "Schedule regular check-ins with friends and family to strengthen your support network."

    recommendation3_title = "Develop Healthy Routines"
    recommendation3_description = "Establish consistent sleep, exercise, and meal schedules to improve overall well-being and resilience."

    # Prepare context for the PDF template
    context = {
        'risk_level': risk_level,
        'risk_description': risk_description,
        'factor1_score': factor1_score,
        'factor1_description': factor1_description,
        'factor2_score': factor2_score,
        'factor2_description': factor2_description,
        'factor3_score': factor3_score,
        'factor3_description': factor3_description,
        'recommendation1_title': recommendation1_title,
        'recommendation1_description': recommendation1_description,
        'recommendation2_title': recommendation2_title,
        'recommendation2_description': recommendation2_description,
        'recommendation3_title': recommendation3_title,
        'recommendation3_description': recommendation3_description,
        'now': timezone.now(),
    }

    # Generate the PDF
    member_identifier = member.member_number if member else "anonymous"
    filename = f"risk_assessment_{member_identifier}.pdf"
    return pdf_generator.generate_pdf_from_template('pdf/risk_assessment.html', context, filename)
