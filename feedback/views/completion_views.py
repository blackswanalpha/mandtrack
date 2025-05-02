from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from surveys.models import Questionnaire, Question
# Import models directly to avoid circular imports
from feedback.models.completion import CompletionTracker, CompletionEvent
# Use direct import from the module where they are defined
from feedback.models import Response, Answer

def track_response_start(request, response_id):
    """
    Track the start of a response
    """
    response = get_object_or_404(Response, pk=response_id)

    # Create or get the completion tracker
    tracker, created = CompletionTracker.objects.get_or_create(response=response)

    # Create a start event if this is a new tracker
    if created:
        # Count required questions
        required_questions = response.survey.questions.filter(required=True).count()
        tracker.answers_required = required_questions
        tracker.save()

        # Create start event
        CompletionEvent.objects.create(
            tracker=tracker,
            event_type='start',
            metadata={
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': request.META.get('REMOTE_ADDR', ''),
            }
        )

    return JsonResponse({
        'success': True,
        'tracker_id': tracker.id,
        'started_at': tracker.started_at.isoformat(),
        'is_completed': tracker.is_completed,
        'completion_percentage': tracker.completion_percentage,
    })

def track_answer_submission(request, response_id, question_id):
    """
    Track the submission of an answer
    """
    response = get_object_or_404(Response, pk=response_id)
    question = get_object_or_404(Question, pk=question_id)

    # Get the completion tracker
    tracker, created = CompletionTracker.objects.get_or_create(response=response)

    # Get the answer if it exists
    answer = Answer.objects.filter(response=response, question=question).first()

    # Create answer event
    CompletionEvent.objects.create(
        tracker=tracker,
        event_type='answer',
        question=question,
        answer=answer,
        metadata={
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': request.META.get('REMOTE_ADDR', ''),
        }
    )

    # Update completion
    tracker.update_completion()

    return JsonResponse({
        'success': True,
        'tracker_id': tracker.id,
        'is_completed': tracker.is_completed,
        'completion_percentage': tracker.completion_percentage,
        'answers_provided': tracker.answers_provided,
        'answers_required': tracker.answers_required,
    })

def track_navigation(request, response_id):
    """
    Track navigation between questions
    """
    response = get_object_or_404(Response, pk=response_id)

    # Get the completion tracker
    tracker, created = CompletionTracker.objects.get_or_create(response=response)

    # Get the current and next question IDs from the request
    current_question_id = request.GET.get('current')
    next_question_id = request.GET.get('next')

    # Get the questions if they exist
    current_question = None
    next_question = None

    if current_question_id:
        current_question = Question.objects.filter(pk=current_question_id).first()

    if next_question_id:
        next_question = Question.objects.filter(pk=next_question_id).first()

    # Create navigation event
    CompletionEvent.objects.create(
        tracker=tracker,
        event_type='navigation',
        question=current_question,
        metadata={
            'current_question_id': current_question_id,
            'next_question_id': next_question_id,
            'direction': request.GET.get('direction', 'forward'),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': request.META.get('REMOTE_ADDR', ''),
        }
    )

    return JsonResponse({
        'success': True,
        'tracker_id': tracker.id,
        'is_completed': tracker.is_completed,
        'completion_percentage': tracker.completion_percentage,
    })

def track_completion(request, response_id):
    """
    Track the completion of a response
    """
    response = get_object_or_404(Response, pk=response_id)

    # Get the completion tracker
    tracker, created = CompletionTracker.objects.get_or_create(response=response)

    # Mark as completed
    tracker.mark_completed()

    # Create completion event
    CompletionEvent.objects.create(
        tracker=tracker,
        event_type='completion',
        metadata={
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': request.META.get('REMOTE_ADDR', ''),
            'time_spent': str(tracker.time_spent) if tracker.time_spent else None,
        }
    )

    return JsonResponse({
        'success': True,
        'tracker_id': tracker.id,
        'is_completed': tracker.is_completed,
        'completion_percentage': tracker.completion_percentage,
        'completed_at': tracker.completed_at.isoformat() if tracker.completed_at else None,
        'time_spent': str(tracker.time_spent) if tracker.time_spent else None,
    })

def track_abandonment(request, response_id):
    """
    Track the abandonment of a response
    """
    response = get_object_or_404(Response, pk=response_id)

    # Get the completion tracker
    tracker, created = CompletionTracker.objects.get_or_create(response=response)

    # Create abandonment event
    CompletionEvent.objects.create(
        tracker=tracker,
        event_type='abandonment',
        metadata={
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': request.META.get('REMOTE_ADDR', ''),
            'reason': request.GET.get('reason', 'unknown'),
        }
    )

    return JsonResponse({
        'success': True,
        'tracker_id': tracker.id,
        'is_completed': tracker.is_completed,
        'completion_percentage': tracker.completion_percentage,
    })

@login_required
def view_completion_stats(request, questionnaire_id):
    """
    View completion statistics for a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)

    # Check if user has permission to view this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is a member of the organization
            if not questionnaire.organization.members.filter(user=request.user, is_active=True).exists():
                messages.error(request, "You don't have permission to view completion statistics for this questionnaire.")
                return redirect('surveys:survey_list')
        else:
            messages.error(request, "You don't have permission to view completion statistics for this questionnaire.")
            return redirect('surveys:survey_list')

    # Get all responses for this questionnaire
    responses = Response.objects.filter(survey=questionnaire)

    # Get completion trackers for these responses
    trackers = CompletionTracker.objects.filter(response__in=responses)

    # Calculate statistics
    total_responses = responses.count()
    completed_responses = trackers.filter(is_completed=True).count()
    abandoned_responses = trackers.filter(is_completed=False).count()

    completion_rate = 0
    if total_responses > 0:
        completion_rate = (completed_responses / total_responses) * 100

    # Calculate average time spent
    avg_time_spent = None
    completed_trackers_with_time = trackers.filter(is_completed=True, time_spent__isnull=False)
    if completed_trackers_with_time.exists():
        total_seconds = 0
        for tracker in completed_trackers_with_time:
            total_seconds += tracker.time_spent.total_seconds()
        avg_time_spent = total_seconds / completed_trackers_with_time.count()

    # Get completion events
    events = CompletionEvent.objects.filter(tracker__in=trackers)

    # Count events by type
    event_counts = {}
    for event_type, _ in CompletionEvent.EVENT_TYPE_CHOICES:
        event_counts[event_type] = events.filter(event_type=event_type).count()

    context = {
        'questionnaire': questionnaire,
        'total_responses': total_responses,
        'completed_responses': completed_responses,
        'abandoned_responses': abandoned_responses,
        'completion_rate': completion_rate,
        'avg_time_spent': avg_time_spent,
        'event_counts': event_counts,
        'trackers': trackers,
    }

    return render(request, 'feedback/completion_stats.html', context)

@login_required
def view_completion_details(request, tracker_id):
    """
    View details of a completion tracker
    """
    tracker = get_object_or_404(CompletionTracker, pk=tracker_id)
    response = tracker.response
    questionnaire = response.survey

    # Check if user has permission to view this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is a member of the organization
            if not questionnaire.organization.members.filter(user=request.user, is_active=True).exists():
                messages.error(request, "You don't have permission to view completion details for this response.")
                return redirect('surveys:survey_list')
        else:
            messages.error(request, "You don't have permission to view completion details for this response.")
            return redirect('surveys:survey_list')

    # Get all events for this tracker
    events = CompletionEvent.objects.filter(tracker=tracker)

    context = {
        'tracker': tracker,
        'response': response,
        'questionnaire': questionnaire,
        'events': events,
    }

    return render(request, 'feedback/completion_details.html', context)
