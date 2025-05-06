from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q, Sum
from django.utils import timezone
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import json
import hashlib

from surveys.models import Questionnaire, ScoringSystem, ScoringConfig, ScoreRule, ScoreRange, ResponseScore, OptionScore
from feedback.models import Response, Answer
from groups.models import Organization

def generate_cache_key(params):
    """
    Generate a cache key based on request parameters

    Args:
        params: Request GET parameters

    Returns:
        String cache key
    """
    # Create a sorted string representation of the parameters
    param_str = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))

    # Generate an MD5 hash of the parameters
    hash_obj = hashlib.md5(param_str.encode())

    # Return the cache key with a prefix
    return f"dashboard_data_{hash_obj.hexdigest()}"

@login_required
def dashboard_data(request):
    """
    API endpoint for dashboard data with caching
    """
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    organization_id = request.GET.get('organization')
    questionnaire_type = request.GET.get('questionnaire_type')

    # Default date range (last 30 days)
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')

    # Convert string dates to datetime objects
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
    end_datetime = end_datetime.replace(hour=23, minute=59, second=59)

    # Generate cache key based on parameters
    cache_key = generate_cache_key(request.GET)

    # Try to get data from cache
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)

    # Base queryset for questionnaires
    questionnaires = Questionnaire.objects.all()

    # Apply organization filter if provided
    if organization_id:
        questionnaires = questionnaires.filter(organization_id=organization_id)

    # Apply questionnaire type filter if provided
    if questionnaire_type:
        questionnaires = questionnaires.filter(type=questionnaire_type)

    # Base queryset for responses
    responses = Response.objects.filter(
        created_at__gte=start_datetime,
        created_at__lte=end_datetime,
        survey__in=questionnaires
    )

    # Calculate stats
    total_questionnaires = questionnaires.count()
    total_responses = responses.count()

    # Calculate completion rate
    completed_responses_count = responses.filter(status='completed').count()
    completion_rate = int((completed_responses_count / total_responses) * 100) if total_responses > 0 else 0

    # Calculate average score
    avg_score = responses.filter(score__isnull=False).aggregate(avg=Avg('score'))['avg'] or 0
    avg_score = round(avg_score, 1)

    # Count questionnaires by status
    active_questionnaires = questionnaires.filter(status='active').count()
    draft_questionnaires = questionnaires.filter(status='draft').count()
    archived_questionnaires = questionnaires.filter(status='archived').count()

    # Calculate completion time statistics
    completion_times = [r.completion_time for r in responses if r.completion_time is not None]
    completion_time_data = {
        'average': sum(completion_times) / len(completion_times) if completion_times else 0,
        'min': min(completion_times) if completion_times else 0,
        'max': max(completion_times) if completion_times else 0,
    }

    # Format completion time for display
    def format_time(seconds):
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        if minutes > 0:
            return f"{minutes}m {remaining_seconds}s"
        else:
            return f"{remaining_seconds}s"

    completion_time_data['average_display'] = format_time(completion_time_data['average'])
    completion_time_data['min_display'] = format_time(completion_time_data['min'])
    completion_time_data['max_display'] = format_time(completion_time_data['max'])

    # Get response trend data
    days_diff = (end_datetime - start_datetime).days + 1
    trend_data = {
        'labels': [],
        'data': [],
        'colors': []
    }

    for i in range(days_diff):
        date = start_datetime + timedelta(days=i)
        count = responses.filter(created_at__date=date.date()).count()
        trend_data['labels'].append(date.strftime('%b %d'))
        trend_data['data'].append(count)
        trend_data['colors'].append('rgba(54, 162, 235, 0.7)')

    # Gender distribution data
    gender_counts = responses.values('patient_gender').annotate(count=Count('id'))
    gender_data = {
        'labels': [],
        'data': [],
        'colors': []
    }

    gender_colors = {
        'male': 'rgba(54, 162, 235, 0.7)',
        'female': 'rgba(255, 99, 132, 0.7)',
        'non-binary': 'rgba(255, 206, 86, 0.7)',
        'prefer_not_to_say': 'rgba(75, 192, 192, 0.7)',
        'other': 'rgba(153, 102, 255, 0.7)'
    }

    for item in gender_counts:
        gender = item['patient_gender'] or 'unknown'
        gender_data['labels'].append(gender.replace('_', ' ').title())
        gender_data['data'].append(item['count'])
        gender_data['colors'].append(gender_colors.get(gender, 'rgba(201, 203, 207, 0.7)'))

    # Age distribution data
    age_ranges = [
        {'min': 0, 'max': 17, 'label': 'Under 18'},
        {'min': 18, 'max': 24, 'label': '18-24'},
        {'min': 25, 'max': 34, 'label': '25-34'},
        {'min': 35, 'max': 44, 'label': '35-44'},
        {'min': 45, 'max': 54, 'label': '45-54'},
        {'min': 55, 'max': 64, 'label': '55-64'},
        {'min': 65, 'max': 200, 'label': '65+'}
    ]

    age_data = {
        'labels': [],
        'data': [],
        'colors': []
    }

    for age_range in age_ranges:
        count = responses.filter(
            Q(patient_age__gte=age_range['min']) &
            Q(patient_age__lte=age_range['max'])
        ).count()

        age_data['labels'].append(age_range['label'])
        age_data['data'].append(count)
        age_data['colors'].append('rgba(54, 162, 235, 0.7)')

    # Device distribution data
    device_data = {
        'labels': ['Desktop', 'Mobile', 'Tablet'],
        'data': [0, 0, 0],
        'colors': ['rgba(54, 162, 235, 0.7)', 'rgba(255, 99, 132, 0.7)', 'rgba(255, 206, 86, 0.7)']
    }

    # Count devices from metadata
    for response in responses:
        if hasattr(response, 'metadata') and response.metadata:
            device = response.metadata.get('device', '').lower()
            if device == 'desktop':
                device_data['data'][0] += 1
            elif device == 'mobile':
                device_data['data'][1] += 1
            elif device == 'tablet':
                device_data['data'][2] += 1

    # Risk level distribution
    risk_data = {
        'labels': ['Low', 'Medium', 'High', 'Critical'],
        'data': [0, 0, 0, 0],
        'colors': ['rgba(75, 192, 192, 0.7)', 'rgba(255, 206, 86, 0.7)',
                  'rgba(255, 159, 64, 0.7)', 'rgba(255, 99, 132, 0.7)']
    }

    for response in responses:
        risk_level = getattr(response, 'risk_level', '').lower()
        if risk_level == 'low':
            risk_data['data'][0] += 1
        elif risk_level == 'medium':
            risk_data['data'][1] += 1
        elif risk_level == 'high':
            risk_data['data'][2] += 1
        elif risk_level == 'critical':
            risk_data['data'][3] += 1

    # Top questionnaires data
    top_questionnaires = Questionnaire.objects.filter(
        responses__created_at__gte=start_datetime,
        responses__created_at__lte=end_datetime
    ).annotate(
        response_count=Count('responses')
    ).order_by('-response_count')[:5]

    top_questionnaires_data = {
        'labels': [],
        'data': [],
        'colors': []
    }

    # Generate colors for questionnaires
    questionnaire_colors = [
        'rgba(54, 162, 235, 0.7)',
        'rgba(255, 99, 132, 0.7)',
        'rgba(255, 206, 86, 0.7)',
        'rgba(75, 192, 192, 0.7)',
        'rgba(153, 102, 255, 0.7)'
    ]

    for i, q in enumerate(top_questionnaires):
        top_questionnaires_data['labels'].append(q.title[:20] + '...' if len(q.title) > 20 else q.title)
        top_questionnaires_data['data'].append(q.response_count)
        top_questionnaires_data['colors'].append(questionnaire_colors[i % len(questionnaire_colors)])

    # Prepare response data
    data = {
        'total_questionnaires': total_questionnaires,
        'total_responses': total_responses,
        'completion_rate': completion_rate,
        'avg_score': avg_score,
        'active_questionnaires': active_questionnaires,
        'draft_questionnaires': draft_questionnaires,
        'archived_questionnaires': archived_questionnaires,
        'completion_time_data': completion_time_data,
        'trend_data': trend_data,
        'gender_distribution': gender_data,
        'age_distribution': age_data,
        'device_data': device_data,
        'risk_data': risk_data,
        'top_questionnaires_data': top_questionnaires_data,
        'cache_timestamp': timezone.now().isoformat(),
    }

    # Cache the data for 15 minutes (900 seconds)
    cache.set(cache_key, data, 900)

    return JsonResponse(data)


@login_required
def scoring_systems_data(request):
    """
    API endpoint for scoring systems data
    """
    # Get filter parameters
    questionnaire_id = request.GET.get('questionnaire_id')

    # Base queryset for scoring systems
    scoring_systems = ScoringSystem.objects.all()

    # Apply questionnaire filter if provided
    if questionnaire_id:
        scoring_systems = scoring_systems.filter(questionnaire_id=questionnaire_id)

    # Prepare response data
    data = []
    for system in scoring_systems:
        # Get score rules count
        rules_count = ScoreRule.objects.filter(scoring_system=system).count()

        # Get score ranges
        ranges = ScoreRange.objects.filter(scoring_system=system)
        ranges_data = []
        for range_obj in ranges:
            ranges_data.append({
                'id': range_obj.id,
                'name': range_obj.name,
                'min_score': range_obj.min_score,
                'max_score': range_obj.max_score,
                'color': range_obj.color,
                'description': range_obj.description
            })

        # Get response scores count
        responses_count = ResponseScore.objects.filter(scoring_system=system).count()

        data.append({
            'id': system.id,
            'name': system.name,
            'questionnaire_id': system.questionnaire.id,
            'questionnaire_title': system.questionnaire.title,
            'scoring_type': system.scoring_type,
            'rules_count': rules_count,
            'ranges': ranges_data,
            'responses_count': responses_count,
            'created_at': system.created_at.isoformat()
        })

    return JsonResponse({'scoring_systems': data})


@login_required
def scoring_system_detail(request, system_id):
    """
    API endpoint for scoring system detail
    """
    try:
        system = get_object_or_404(ScoringSystem, id=system_id)

        # Get score rules
        rules = ScoreRule.objects.filter(scoring_system=system).select_related('question')
        rules_data = []

        for rule in rules:
            # Get option scores if applicable
            option_scores = []
            if rule.question.question_type in ['single_choice', 'multiple_choice']:
                options = rule.question.choices.all()
                for option in options:
                    try:
                        option_score = OptionScore.objects.get(score_rule=rule, option=option)
                        score = option_score.score
                    except OptionScore.DoesNotExist:
                        score = 0

                    option_scores.append({
                        'option_id': option.id,
                        'option_text': option.text,
                        'score': score
                    })

            rules_data.append({
                'id': rule.id,
                'question_id': rule.question.id,
                'question_text': rule.question.text,
                'question_type': rule.question.question_type,
                'weight': rule.weight,
                'text_score_enabled': rule.text_score_enabled,
                'text_score': rule.text_score,
                'option_scores': option_scores
            })

        # Get score ranges
        ranges = ScoreRange.objects.filter(scoring_system=system)
        ranges_data = []

        for range_obj in ranges:
            ranges_data.append({
                'id': range_obj.id,
                'name': range_obj.name,
                'min_score': range_obj.min_score,
                'max_score': range_obj.max_score,
                'color': range_obj.color,
                'description': range_obj.description,
                'interpretation': range_obj.interpretation
            })

        # Get recent response scores
        response_scores = ResponseScore.objects.filter(scoring_system=system).select_related('response', 'score_range').order_by('-calculated_at')[:10]
        scores_data = []

        for score in response_scores:
            scores_data.append({
                'id': score.id,
                'response_id': str(score.response.id),
                'raw_score': score.raw_score,
                'range_name': score.score_range.name if score.score_range else None,
                'range_color': score.score_range.color if score.score_range else None,
                'calculated_at': score.calculated_at.isoformat()
            })

        # Prepare system data
        system_data = {
            'id': system.id,
            'name': system.name,
            'description': system.description,
            'questionnaire_id': system.questionnaire.id,
            'questionnaire_title': system.questionnaire.title,
            'scoring_type': system.scoring_type,
            'formula': system.formula,
            'rules': rules_data,
            'ranges': ranges_data,
            'recent_scores': scores_data,
            'created_at': system.created_at.isoformat(),
            'updated_at': system.updated_at.isoformat()
        }

        return JsonResponse({'scoring_system': system_data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def questionnaire_scores(request, questionnaire_id):
    """
    API endpoint for questionnaire scores
    """
    try:
        questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)

        # Get responses for this questionnaire
        responses = Response.objects.filter(survey=questionnaire)

        # Get scoring systems for this questionnaire
        scoring_systems = ScoringSystem.objects.filter(questionnaire=questionnaire)

        # Prepare data
        scores_data = []

        for response in responses:
            response_scores = ResponseScore.objects.filter(
                response=response,
                scoring_system__in=scoring_systems
            ).select_related('scoring_system', 'score_range')

            scores = []
            for score in response_scores:
                scores.append({
                    'scoring_system_id': score.scoring_system.id,
                    'scoring_system_name': score.scoring_system.name,
                    'raw_score': score.raw_score,
                    'range_name': score.score_range.name if score.score_range else None,
                    'range_color': score.score_range.color if score.score_range else None,
                    'calculated_at': score.calculated_at.isoformat()
                })

            scores_data.append({
                'response_id': str(response.id),
                'patient_email': response.patient_email,
                'patient_age': response.patient_age,
                'patient_gender': response.patient_gender,
                'created_at': response.created_at.isoformat(),
                'completed_at': response.completed_at.isoformat() if response.completed_at else None,
                'status': response.status,
                'scores': scores
            })

        return JsonResponse({
            'questionnaire_id': questionnaire_id,
            'questionnaire_title': questionnaire.title,
            'scores': scores_data
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def calculate_score(request):
    """
    API endpoint to calculate score for a response
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        data = json.loads(request.body)
        response_id = data.get('response_id')
        scoring_system_id = data.get('scoring_system_id')

        if not response_id or not scoring_system_id:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)

        response = get_object_or_404(Response, id=response_id)
        scoring_system = get_object_or_404(ScoringSystem, id=scoring_system_id)

        # Calculate the score
        result = scoring_system.calculate_score(response)

        # Initialize default values
        raw_score = 0
        z_score = None
        percentile = None
        additional_data = None

        # Process the result based on scoring type
        if isinstance(result, (int, float)):
            raw_score = result
        elif isinstance(result, dict):
            raw_score = result.get('raw_score', 0)
            z_score = result.get('z_score')
            percentile = result.get('percentile')

            # Store any additional data
            additional_data = {k: v for k, v in result.items()
                              if k not in ['raw_score', 'z_score', 'percentile', 'range']}

            if additional_data and not additional_data:
                additional_data = None

        # Find the score range if applicable
        score_range = None
        if scoring_system.scoring_type == 'range_based':
            if isinstance(result, dict) and 'range' in result:
                score_range = result.get('range')
            else:
                score_range = ScoreRange.objects.filter(
                    scoring_system=scoring_system,
                    min_score__lte=raw_score,
                    max_score__gte=raw_score
                ).first()

        # Create or update the response score
        defaults = {
            'raw_score': raw_score,
            'score_range': score_range,
            'notes': f"Score calculated via API on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }

        # Add additional scoring data if available
        if z_score is not None:
            defaults['z_score'] = z_score
        if percentile is not None:
            defaults['percentile'] = percentile
        if additional_data:
            defaults['additional_data'] = additional_data

        response_score, created = ResponseScore.objects.update_or_create(
            response=response,
            scoring_system=scoring_system,
            defaults=defaults
        )

        # Prepare response data
        score_data = {
            'id': response_score.id,
            'response_id': str(response.id),
            'scoring_system_id': scoring_system.id,
            'scoring_type': scoring_system.scoring_type,
            'raw_score': response_score.raw_score,
            'range_name': score_range.name if score_range else None,
            'range_color': score_range.color if score_range else None,
            'calculated_at': response_score.calculated_at.isoformat(),
            'created': created
        }

        # Add additional scoring data if available
        if response_score.z_score is not None:
            score_data['z_score'] = response_score.z_score
        if response_score.percentile is not None:
            score_data['percentile'] = response_score.percentile
        if response_score.additional_data:
            score_data['additional_data'] = response_score.additional_data

        return JsonResponse({'success': True, 'score': score_data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def batch_calculate_scores(request):
    """
    API endpoint to calculate scores for multiple responses
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        data = json.loads(request.body)
        scoring_system_id = data.get('scoring_system_id')
        response_ids = data.get('response_ids', [])

        if not scoring_system_id:
            return JsonResponse({'error': 'Missing scoring_system_id parameter'}, status=400)

        if not response_ids:
            return JsonResponse({'error': 'No response_ids provided'}, status=400)

        # Get the scoring system
        scoring_system = get_object_or_404(ScoringSystem, id=scoring_system_id)

        # Calculate scores for each response
        results = []
        errors = []

        for response_id in response_ids:
            try:
                # Get the response
                response = Response.objects.get(id=response_id)

                # Calculate the score
                result = scoring_system.calculate_score(response)

                # Initialize default values
                raw_score = 0
                z_score = None
                percentile = None
                additional_data = None

                # Process the result based on scoring type
                if isinstance(result, (int, float)):
                    raw_score = result
                elif isinstance(result, dict):
                    raw_score = result.get('raw_score', 0)
                    z_score = result.get('z_score')
                    percentile = result.get('percentile')

                    # Store any additional data
                    additional_data = {k: v for k, v in result.items()
                                      if k not in ['raw_score', 'z_score', 'percentile', 'range']}

                    if additional_data and not additional_data:
                        additional_data = None

                # Find the score range if applicable
                score_range = None
                if scoring_system.scoring_type == 'range_based':
                    if isinstance(result, dict) and 'range' in result:
                        score_range = result.get('range')
                    else:
                        score_range = ScoreRange.objects.filter(
                            scoring_system=scoring_system,
                            min_score__lte=raw_score,
                            max_score__gte=raw_score
                        ).first()

                # Create or update the response score
                defaults = {
                    'raw_score': raw_score,
                    'score_range': score_range,
                    'notes': f"Score calculated via batch API on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }

                # Add additional scoring data if available
                if z_score is not None:
                    defaults['z_score'] = z_score
                if percentile is not None:
                    defaults['percentile'] = percentile
                if additional_data:
                    defaults['additional_data'] = additional_data

                response_score, created = ResponseScore.objects.update_or_create(
                    response=response,
                    scoring_system=scoring_system,
                    defaults=defaults
                )

                # Add to results
                results.append({
                    'response_id': str(response_id),
                    'score_id': response_score.id,
                    'raw_score': response_score.raw_score,
                    'range_name': score_range.name if score_range else None,
                    'created': created
                })

            except Response.DoesNotExist:
                errors.append({
                    'response_id': str(response_id),
                    'error': 'Response not found'
                })
            except Exception as e:
                errors.append({
                    'response_id': str(response_id),
                    'error': str(e)
                })

        return JsonResponse({
            'success': True,
            'scoring_system_id': scoring_system_id,
            'total_processed': len(response_ids),
            'successful': len(results),
            'failed': len(errors),
            'results': results,
            'errors': errors
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def calculate_all_scores(request, system_id):
    """
    API endpoint to calculate scores for all responses for a questionnaire
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        # Get the scoring system
        scoring_system = get_object_or_404(ScoringSystem, id=system_id)

        # Get all responses for this questionnaire
        responses = Response.objects.filter(
            survey=scoring_system.questionnaire,
            status='completed'
        )

        # Calculate scores for each response
        results = []
        errors = []

        for response in responses:
            try:
                # Calculate the score
                result = scoring_system.calculate_score(response)

                # Initialize default values
                raw_score = 0
                z_score = None
                percentile = None
                additional_data = None

                # Process the result based on scoring type
                if isinstance(result, (int, float)):
                    raw_score = result
                elif isinstance(result, dict):
                    raw_score = result.get('raw_score', 0)
                    z_score = result.get('z_score')
                    percentile = result.get('percentile')

                    # Store any additional data
                    additional_data = {k: v for k, v in result.items()
                                      if k not in ['raw_score', 'z_score', 'percentile', 'range']}

                    if additional_data and not additional_data:
                        additional_data = None

                # Find the score range if applicable
                score_range = None
                if scoring_system.scoring_type == 'range_based':
                    if isinstance(result, dict) and 'range' in result:
                        score_range = result.get('range')
                    else:
                        score_range = ScoreRange.objects.filter(
                            scoring_system=scoring_system,
                            min_score__lte=raw_score,
                            max_score__gte=raw_score
                        ).first()

                # Create or update the response score
                defaults = {
                    'raw_score': raw_score,
                    'score_range': score_range,
                    'notes': f"Score calculated via batch API on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }

                # Add additional scoring data if available
                if z_score is not None:
                    defaults['z_score'] = z_score
                if percentile is not None:
                    defaults['percentile'] = percentile
                if additional_data:
                    defaults['additional_data'] = additional_data

                response_score, created = ResponseScore.objects.update_or_create(
                    response=response,
                    scoring_system=scoring_system,
                    defaults=defaults
                )

                # Add to results
                results.append({
                    'response_id': str(response.id),
                    'score_id': response_score.id,
                    'raw_score': response_score.raw_score,
                    'range_name': score_range.name if score_range else None,
                    'created': created
                })

            except Exception as e:
                errors.append({
                    'response_id': str(response.id),
                    'error': str(e)
                })

        return JsonResponse({
            'success': True,
            'scoring_system_id': system_id,
            'questionnaire_id': str(scoring_system.questionnaire.id),
            'total_processed': len(responses),
            'successful': len(results),
            'failed': len(errors),
            'results': results[:10],  # Only return first 10 results to avoid large responses
            'errors': errors[:10]     # Only return first 10 errors
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def export_scores_csv(request, system_id):
    """
    API endpoint to export scores for a scoring system as CSV
    """
    try:
        import csv
        from django.http import HttpResponse

        # Get the scoring system
        scoring_system = get_object_or_404(ScoringSystem, id=system_id)

        # Get all scores for this scoring system
        scores = ResponseScore.objects.filter(
            scoring_system=scoring_system
        ).select_related('response', 'score_range').order_by('-calculated_at')

        # Create the HttpResponse object with CSV header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{scoring_system.name}_scores.csv"'

        # Create CSV writer
        writer = csv.writer(response)

        # Write header row
        header = [
            'Response ID',
            'Patient Email',
            'Patient Age',
            'Patient Gender',
            'Raw Score',
            'Z-Score',
            'Percentile',
            'Score Range',
            'Calculated At',
            'Response Created At',
            'Response Completed At'
        ]
        writer.writerow(header)

        # Write data rows
        for score in scores:
            row = [
                str(score.response.id),
                score.response.patient_email,
                score.response.patient_age,
                score.response.patient_gender,
                score.raw_score,
                score.z_score if score.z_score is not None else '',
                score.percentile if score.percentile is not None else '',
                score.score_range.name if score.score_range else '',
                score.calculated_at.strftime('%Y-%m-%d %H:%M:%S'),
                score.response.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                score.response.completed_at.strftime('%Y-%m-%d %H:%M:%S') if score.response.completed_at else ''
            ]
            writer.writerow(row)

        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def export_scores_excel(request, system_id):
    """
    API endpoint to export scores for a scoring system as Excel
    """
    try:
        import xlsxwriter
        from io import BytesIO
        from django.http import HttpResponse

        # Get the scoring system
        scoring_system = get_object_or_404(ScoringSystem, id=system_id)

        # Get all scores for this scoring system
        scores = ResponseScore.objects.filter(
            scoring_system=scoring_system
        ).select_related('response', 'score_range').order_by('-calculated_at')

        # Create a BytesIO object to store the Excel file
        output = BytesIO()

        # Create a workbook and add a worksheet
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Scores')

        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'color': 'white',
            'border': 1
        })

        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})

        # Write header row
        headers = [
            'Response ID',
            'Patient Email',
            'Patient Age',
            'Patient Gender',
            'Raw Score',
            'Z-Score',
            'Percentile',
            'Score Range',
            'Calculated At',
            'Response Created At',
            'Response Completed At'
        ]

        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        # Write data rows
        for row, score in enumerate(scores, start=1):
            worksheet.write(row, 0, str(score.response.id))
            worksheet.write(row, 1, score.response.patient_email)
            worksheet.write(row, 2, score.response.patient_age)
            worksheet.write(row, 3, score.response.patient_gender)
            worksheet.write(row, 4, score.raw_score)
            worksheet.write(row, 5, score.z_score if score.z_score is not None else '')
            worksheet.write(row, 6, score.percentile if score.percentile is not None else '')
            worksheet.write(row, 7, score.score_range.name if score.score_range else '')
            worksheet.write_datetime(row, 8, score.calculated_at, date_format)
            worksheet.write_datetime(row, 9, score.response.created_at, date_format)
            if score.response.completed_at:
                worksheet.write_datetime(row, 10, score.response.completed_at, date_format)
            else:
                worksheet.write(row, 10, '')

        # Add auto-filter to the header row
        worksheet.autofilter(0, 0, len(scores), len(headers) - 1)

        # Adjust column widths
        for col, header in enumerate(headers):
            worksheet.set_column(col, col, len(header) + 5)

        # Close the workbook
        workbook.close()

        # Create the HttpResponse object with Excel header
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{scoring_system.name}_scores.xlsx"'

        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def export_scores_pdf(request, system_id):
    """
    API endpoint to export scores for a scoring system as PDF
    """
    try:
        from django.http import HttpResponse
        from django.template.loader import render_to_string
        from weasyprint import HTML, CSS
        from django.conf import settings
        import tempfile
        import os

        # Get the scoring system
        scoring_system = get_object_or_404(ScoringSystem, id=system_id)

        # Get all scores for this scoring system
        scores = ResponseScore.objects.filter(
            scoring_system=scoring_system
        ).select_related('response', 'score_range').order_by('-calculated_at')

        # Get score ranges for this scoring system
        score_ranges = ScoreRange.objects.filter(scoring_system=scoring_system).order_by('min_score')

        # Calculate statistics
        from django.db.models import Avg, StdDev, Min, Max, Count
        stats = scores.aggregate(
            avg=Avg('raw_score'),
            stddev=StdDev('raw_score'),
            min=Min('raw_score'),
            max=Max('raw_score'),
            count=Count('id')
        )

        # Prepare context for the template
        context = {
            'scoring_system': scoring_system,
            'scores': scores,
            'score_ranges': score_ranges,
            'stats': stats,
            'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'generated_by': request.user.get_full_name() or request.user.email
        }

        # Render HTML content
        html_string = render_to_string('admin_portal/pdf/scores_report.html', context)

        # Create a temporary file to store the PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            # Generate PDF
            HTML(string=html_string).write_pdf(
                tmp.name,
                stylesheets=[
                    CSS(string='@page { size: A4; margin: 1cm; }')
                ]
            )

            # Read the PDF file
            with open(tmp.name, 'rb') as pdf_file:
                pdf_content = pdf_file.read()

            # Delete the temporary file
            os.unlink(tmp.name)

        # Create the HttpResponse object with PDF header
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{scoring_system.name}_scores_report.pdf"'

        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)