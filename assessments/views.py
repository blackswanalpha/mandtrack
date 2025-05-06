from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from .models import Assessment, Consultation
from feedback.models import Response
from .forms import AssessmentForm, ConsultationForm
from .pdf_utils import generate_assessment_pdf

@login_required
def assessment_list(request):
    """
    Display a list of all assessments
    """
    # Get filter parameters from request
    status = request.GET.get('status')
    risk_level = request.GET.get('risk_level')
    consultation = request.GET.get('consultation')
    search_query = request.GET.get('q')

    # Start with all assessments
    assessments = Assessment.objects.select_related('response', 'assessor').all()

    # Apply filters if provided
    if status:
        assessments = assessments.filter(status=status)

    if risk_level:
        assessments = assessments.filter(response__risk_level=risk_level)

    if consultation:
        assessments = assessments.filter(consultation_recommended=consultation)

    if search_query:
        assessments = assessments.filter(
            Q(response__patient_identifier__icontains=search_query) |
            Q(response__patient_email__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # Paginate results
    paginator = Paginator(assessments, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_choices': Assessment.STATUS_CHOICES,
        'risk_level_choices': Response.RISK_LEVEL_CHOICES,
        'consultation_choices': Assessment.CONSULTATION_CHOICES,
        'selected_status': status,
        'selected_risk_level': risk_level,
        'selected_consultation': consultation,
        'search_query': search_query,
    }

    return render(request, 'assessments/assessment_list.html', context)

@login_required
def assessment_detail(request, pk):
    """
    Display assessment details
    """
    assessment = get_object_or_404(Assessment, pk=pk)
    consultations = assessment.consultations.all().order_by('-scheduled_date')

    context = {
        'assessment': assessment,
        'consultations': consultations,
    }

    return render(request, 'assessments/assessment_detail.html', context)

@login_required
def assessment_create(request, response_id=None):
    """
    Create a new assessment
    """
    # If response_id is provided, pre-fill the form with that response
    response = None
    if response_id:
        response = get_object_or_404(Response, pk=response_id)

    if request.method == 'POST':
        form = AssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.assessor = request.user
            assessment.save()

            messages.success(request, 'Assessment created successfully!')
            return redirect('assessments:assessment_detail', pk=assessment.pk)
    else:
        initial_data = {}
        if response:
            initial_data['response'] = response
        form = AssessmentForm(initial=initial_data)

    context = {
        'form': form,
        'response': response,
    }

    return render(request, 'assessments/assessment_form.html', context)

@login_required
def assessment_update(request, pk):
    """
    Update an existing assessment
    """
    assessment = get_object_or_404(Assessment, pk=pk)

    if request.method == 'POST':
        form = AssessmentForm(request.POST, instance=assessment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assessment updated successfully!')
            return redirect('assessments:assessment_detail', pk=assessment.pk)
    else:
        form = AssessmentForm(instance=assessment)

    context = {
        'form': form,
        'assessment': assessment,
        'is_update': True,
    }

    return render(request, 'assessments/assessment_form.html', context)

@login_required
def assessment_dashboard(request):
    """
    Display assessment dashboard with statistics and charts
    """
    # Get counts for different statuses
    pending_count = Assessment.objects.filter(status='pending').count()
    in_progress_count = Assessment.objects.filter(status='in_progress').count()
    completed_count = Assessment.objects.filter(status='completed').count()

    # Get counts for different risk levels
    low_risk_count = Assessment.objects.filter(response__risk_level='low').count()
    medium_risk_count = Assessment.objects.filter(response__risk_level='medium').count()
    high_risk_count = Assessment.objects.filter(response__risk_level='high').count()
    critical_risk_count = Assessment.objects.filter(response__risk_level='critical').count()

    # Get counts for consultation recommendations
    not_required_count = Assessment.objects.filter(consultation_recommended='not_required').count()
    recommended_count = Assessment.objects.filter(consultation_recommended='recommended').count()
    required_count = Assessment.objects.filter(consultation_recommended='required').count()
    scheduled_count = Assessment.objects.filter(consultation_recommended='scheduled').count()
    completed_consult_count = Assessment.objects.filter(consultation_recommended='completed').count()

    # Get recent assessments
    recent_assessments = Assessment.objects.select_related('response', 'assessor').order_by('-assessment_date')[:5]

    # Get high-risk assessments
    high_risk_assessments = Assessment.objects.select_related('response').filter(
        Q(response__risk_level='high') | Q(response__risk_level='critical')
    ).order_by('-assessment_date')[:5]

    context = {
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'low_risk_count': low_risk_count,
        'medium_risk_count': medium_risk_count,
        'high_risk_count': high_risk_count,
        'critical_risk_count': critical_risk_count,
        'not_required_count': not_required_count,
        'recommended_count': recommended_count,
        'required_count': required_count,
        'scheduled_count': scheduled_count,
        'completed_consult_count': completed_consult_count,
        'recent_assessments': recent_assessments,
        'high_risk_assessments': high_risk_assessments,
    }

    return render(request, 'assessments/assessment_dashboard.html', context)

@login_required
def consultation_create(request, assessment_id):
    """
    Create a new consultation for an assessment
    """
    assessment = get_object_or_404(Assessment, pk=assessment_id)

    if request.method == 'POST':
        form = ConsultationForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.assessment = assessment
            consultation.save()

            # Update the assessment's consultation status
            assessment.consultation_recommended = 'scheduled'
            assessment.save()

            messages.success(request, 'Consultation scheduled successfully!')
            return redirect('assessments:assessment_detail', pk=assessment.pk)
    else:
        form = ConsultationForm(initial={'assessment': assessment})

    context = {
        'form': form,
        'assessment': assessment,
    }

    return render(request, 'assessments/consultation_form.html', context)

@login_required
def consultation_update(request, pk):
    """
    Update an existing consultation
    """
    consultation = get_object_or_404(Consultation, pk=pk)

    if request.method == 'POST':
        form = ConsultationForm(request.POST, instance=consultation)
        if form.is_valid():
            form.save()

            # If consultation is completed, update the assessment
            if consultation.status == 'completed':
                consultation.assessment.consultation_recommended = 'completed'
                consultation.assessment.save()

            messages.success(request, 'Consultation updated successfully!')
            return redirect('assessments:assessment_detail', pk=consultation.assessment.pk)
    else:
        form = ConsultationForm(instance=consultation)

    context = {
        'form': form,
        'consultation': consultation,
        'is_update': True,
    }

    return render(request, 'assessments/consultation_form.html', context)

@login_required
def flag_for_consultation(request, assessment_id):
    """
    AJAX endpoint to flag an assessment for consultation
    """
    if request.method == 'POST':
        assessment = get_object_or_404(Assessment, pk=assessment_id)
        consultation_type = request.POST.get('consultation_type', 'recommended')

        if consultation_type in dict(Assessment.CONSULTATION_CHOICES):
            assessment.consultation_recommended = consultation_type
            assessment.save()

            return JsonResponse({
                'success': True,
                'message': f'Assessment flagged for {dict(Assessment.CONSULTATION_CHOICES)[consultation_type]} consultation'
            })

        return JsonResponse({
            'success': False,
            'message': 'Invalid consultation type'
        })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@login_required
@require_GET
def export_assessment_pdf(request, pk):
    """
    Export an assessment as PDF
    """
    assessment = get_object_or_404(Assessment, pk=pk)

    # Generate PDF
    return generate_assessment_pdf(assessment)

@login_required
def consultation_calendar(request):
    """
    Display a calendar view of consultations
    """
    # Get assessments for the new consultation form
    assessments = Assessment.objects.select_related('response').filter(
        Q(consultation_recommended='recommended') |
        Q(consultation_recommended='required')
    ).order_by('-assessment_date')

    # Get consultants (users who can conduct consultations)
    consultants = request.user.__class__.objects.filter(is_active=True).order_by('first_name', 'last_name')

    context = {
        'assessments': assessments,
        'consultants': consultants,
    }

    return render(request, 'assessments/consultation_calendar.html', context)

@login_required
def consultation_events(request):
    """
    Return consultations as JSON for FullCalendar
    """
    # Get start and end dates from request
    start = request.GET.get('start')
    end = request.GET.get('end')

    # Query consultations
    consultations = Consultation.objects.select_related('assessment', 'assessment__response', 'consultant')

    # Filter by date range if provided
    if start and end:
        consultations = consultations.filter(scheduled_date__gte=start, scheduled_date__lte=end)

    # Convert to calendar events
    events = []
    for consultation in consultations:
        patient_id = consultation.assessment.response.patient_identifier or 'Anonymous'
        consultant_name = consultation.consultant.get_full_name() if consultation.consultant else 'Unassigned'

        events.append({
            'id': str(consultation.id),
            'title': f"{patient_id} - {consultant_name}",
            'start': consultation.scheduled_date.isoformat(),
            'end': (consultation.scheduled_date + timezone.timedelta(hours=1)).isoformat(),
            'status': consultation.status,
            'extendedProps': {
                'status': consultation.status,
                'patient_id': patient_id,
                'consultant': consultant_name,
                'assessment_id': str(consultation.assessment.id),
            }
        })

    return JsonResponse(events, safe=False)

@login_required
def consultation_details(request, pk):
    """
    Return consultation details as JSON
    """
    try:
        consultation = Consultation.objects.select_related('assessment', 'assessment__response', 'consultant').get(pk=pk)

        data = {
            'success': True,
            'consultation': {
                'id': str(consultation.id),
                'patient_id': consultation.assessment.response.patient_identifier or 'Anonymous',
                'consultant_name': consultation.consultant.get_full_name() if consultation.consultant else 'Unassigned',
                'scheduled_date': consultation.scheduled_date.strftime('%Y-%m-%d %H:%M'),
                'status': consultation.status,
                'status_display': consultation.get_status_display(),
                'notes': consultation.notes,
                'outcome': consultation.outcome,
                'follow_up_required': consultation.follow_up_required,
                'assessment_id': str(consultation.assessment.id),
            }
        }

        return JsonResponse(data)

    except Consultation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Consultation not found'
        })

@login_required
def consultation_create_ajax(request):
    """
    Create a new consultation via AJAX
    """
    if request.method == 'POST':
        try:
            # Get form data
            assessment_id = request.POST.get('assessment')
            consultant_id = request.POST.get('consultant')
            scheduled_date = request.POST.get('scheduled_date')
            notes = request.POST.get('notes', '')
            follow_up_required = request.POST.get('follow_up_required') == 'on'

            # Validate required fields
            if not assessment_id or not consultant_id or not scheduled_date:
                return JsonResponse({
                    'success': False,
                    'message': 'Assessment, consultant, and scheduled date are required.'
                })

            # Get assessment and consultant
            assessment = Assessment.objects.get(pk=assessment_id)
            consultant = request.user.__class__.objects.get(pk=consultant_id)

            # Create consultation
            consultation = Consultation.objects.create(
                assessment=assessment,
                consultant=consultant,
                scheduled_date=scheduled_date,
                notes=notes,
                follow_up_required=follow_up_required
            )

            # Update assessment consultation status
            assessment.consultation_recommended = 'scheduled'
            assessment.save()

            return JsonResponse({
                'success': True,
                'message': 'Consultation scheduled successfully.',
                'consultation_id': str(consultation.id)
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error scheduling consultation: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def patient_portal(request):
    """
    Patient portal for viewing assessment results
    """
    error_message = None
    patient_identifier = None
    assessments = []
    consultations = []
    upcoming_consultations = []
    latest_assessment = None
    risk_trend = None

    # Check if the patient is already authenticated
    if 'patient_identifier' in request.session:
        patient_identifier = request.session['patient_identifier']

    # Process login form
    if request.method == 'POST':
        access_code = request.POST.get('access_code')
        patient_identifier = request.POST.get('patient_identifier')

        if not access_code or not patient_identifier:
            error_message = "Access code and patient ID are required."
        else:
            # Check if the patient exists with the given access code
            # For simplicity, we're just checking if there are any responses with this patient identifier
            # In a real system, you would have a more secure authentication mechanism
            responses = Response.objects.filter(patient_identifier=patient_identifier)

            if responses.exists():
                # Store patient identifier in session
                request.session['patient_identifier'] = patient_identifier
            else:
                error_message = "Invalid access code or patient ID."
                patient_identifier = None

    # If patient is authenticated, get their data
    if patient_identifier:
        # Get assessments for this patient
        assessments = Assessment.objects.filter(
            response__patient_identifier=patient_identifier
        ).select_related('response', 'response__survey').order_by('-assessment_date')

        # Get consultations for this patient
        if assessments:
            assessment_ids = [assessment.id for assessment in assessments]
            consultations = Consultation.objects.filter(
                assessment_id__in=assessment_ids
            ).select_related('consultant').order_by('-scheduled_date')

            # Get upcoming consultations
            upcoming_consultations = consultations.filter(
                status='scheduled',
                scheduled_date__gte=timezone.now()
            )

            # Get latest assessment
            latest_assessment = assessments.first()

            # Calculate risk trend if there are multiple assessments
            if len(assessments) > 1:
                # Convert risk levels to numeric values
                risk_values = []
                for assessment in assessments:
                    risk_level = assessment.get_risk_level()
                    if risk_level == 'low':
                        risk_values.append(1)
                    elif risk_level == 'medium':
                        risk_values.append(2)
                    elif risk_level == 'high':
                        risk_values.append(3)
                    elif risk_level == 'critical':
                        risk_values.append(4)
                    else:
                        risk_values.append(0)

                # Calculate trend (simple comparison of first and last values)
                if risk_values[0] < risk_values[-1]:
                    risk_trend = 'worsening'
                elif risk_values[0] > risk_values[-1]:
                    risk_trend = 'improving'
                else:
                    risk_trend = 'stable'

    context = {
        'patient_identifier': patient_identifier,
        'error_message': error_message,
        'assessments': assessments,
        'consultations': consultations,
        'upcoming_consultations': upcoming_consultations,
        'latest_assessment': latest_assessment,
        'risk_trend': risk_trend,
    }

    return render(request, 'assessments/patient_portal.html', context)

@login_required
def patient_progress(request):
    """
    Advanced analytics for patient progress
    """
    # Get filter parameters
    selected_patient = request.GET.get('patient_identifier', '')
    selected_date_range = request.GET.get('date_range', '90')

    # Initialize variables
    assessments = []
    first_assessment = None
    latest_assessment = None
    risk_trend = None
    score_change = 0
    consultations_count = 0
    low_risk_count = 0
    medium_risk_count = 0
    high_risk_count = 0
    critical_risk_count = 0

    # If patient ID is provided, get their assessments
    if selected_patient:
        # Get date filter
        if selected_date_range != 'all':
            date_threshold = timezone.now() - timezone.timedelta(days=int(selected_date_range))
            assessments = Assessment.objects.filter(
                response__patient_identifier=selected_patient,
                assessment_date__gte=date_threshold
            ).select_related('response', 'response__survey').order_by('assessment_date')
        else:
            assessments = Assessment.objects.filter(
                response__patient_identifier=selected_patient
            ).select_related('response', 'response__survey').order_by('assessment_date')

        # If assessments found, calculate analytics
        if assessments:
            # Get first and latest assessments
            first_assessment = assessments.first()
            latest_assessment = assessments.last()

            # Count risk levels
            for assessment in assessments:
                risk_level = assessment.get_risk_level()
                if risk_level == 'low':
                    low_risk_count += 1
                elif risk_level == 'medium':
                    medium_risk_count += 1
                elif risk_level == 'high':
                    high_risk_count += 1
                elif risk_level == 'critical':
                    critical_risk_count += 1

            # Calculate risk trend
            first_risk = first_assessment.get_risk_level()
            latest_risk = latest_assessment.get_risk_level()

            risk_values = {
                'low': 1,
                'medium': 2,
                'high': 3,
                'critical': 4
            }

            if risk_values.get(first_risk, 0) > risk_values.get(latest_risk, 0):
                risk_trend = 'improving'
            elif risk_values.get(first_risk, 0) < risk_values.get(latest_risk, 0):
                risk_trend = 'worsening'
            else:
                risk_trend = 'stable'

            # Calculate score change
            first_score = first_assessment.response.score or 0
            latest_score = latest_assessment.response.score or 0
            score_change = latest_score - first_score

            # Get consultation count
            assessment_ids = [assessment.id for assessment in assessments]
            consultations_count = Consultation.objects.filter(
                assessment_id__in=assessment_ids
            ).count()

    context = {
        'selected_patient': selected_patient,
        'selected_date_range': selected_date_range,
        'assessments': assessments,
        'first_assessment': first_assessment,
        'latest_assessment': latest_assessment,
        'risk_trend': risk_trend,
        'score_change': score_change,
        'consultations_count': consultations_count,
        'low_risk_count': low_risk_count,
        'medium_risk_count': medium_risk_count,
        'high_risk_count': high_risk_count,
        'critical_risk_count': critical_risk_count,
    }

    return render(request, 'assessments/patient_progress.html', context)