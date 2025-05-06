"""
Views for enhanced scoring functionality.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction

from surveys.models import (
    ScoringSystem, ResponseScore, EnhancedScoringFeedback
)
from feedback.models import Response
from surveys.services.enhanced_scoring_service import EnhancedScoringService

def enhanced_scoring_detail(request, response_id, scoring_system_id=None):
    """
    View for displaying enhanced scoring details
    """
    # Get the response
    response = get_object_or_404(Response, id=response_id)
    
    # Get the scoring system
    if scoring_system_id:
        scoring_system = get_object_or_404(ScoringSystem, id=scoring_system_id)
    else:
        # Use the default scoring system for this questionnaire
        scoring_system = ScoringSystem.objects.filter(
            questionnaire=response.survey,
            is_default=True
        ).first()
        
        if not scoring_system:
            # If no default, use the first available
            scoring_system = ScoringSystem.objects.filter(
                questionnaire=response.survey
            ).first()
            
            if not scoring_system:
                messages.error(request, "No scoring system found for this questionnaire.")
                return redirect('feedback:response_detail', response_id=response_id)
    
    # Get or calculate the response score
    try:
        # Try to get existing score
        response_score = ResponseScore.objects.get(
            response=response,
            scoring_system=scoring_system
        )
        
        # Check if it has enhanced data
        if response_score.z_score is None and response_score.percentile is None and response_score.additional_data is None:
            # Calculate enhanced score
            scoring_service = EnhancedScoringService(scoring_system)
            response_score = scoring_service.calculate_score(response)
            messages.success(request, "Enhanced score calculated successfully.")
        
    except ResponseScore.DoesNotExist:
        # Calculate new score
        scoring_service = EnhancedScoringService(scoring_system)
        response_score = scoring_service.calculate_score(response)
        messages.success(request, "Enhanced score calculated successfully.")
    
    # Get other scoring systems for this questionnaire
    other_scoring_systems = ScoringSystem.objects.filter(
        questionnaire=response.survey
    ).exclude(id=scoring_system.id)
    
    # Prepare context
    context = {
        'response': response,
        'scoring_system': scoring_system,
        'response_score': response_score,
        'other_scoring_systems': other_scoring_systems,
    }
    
    return render(request, 'surveys/enhanced_scoring_detail.html', context)

def enhanced_scoring_feedback(request, response_id=None, scoring_system_id=None):
    """
    View for collecting feedback on enhanced scoring
    """
    if request.method == 'POST':
        # Process form submission
        response_id = request.POST.get('response_id')
        scoring_system_id = request.POST.get('scoring_system_id')
        
        # Get the response and scoring system
        response = get_object_or_404(Response, id=response_id)
        scoring_system = get_object_or_404(ScoringSystem, id=scoring_system_id)
        
        # Get form data
        accuracy_rating = request.POST.get('accuracy_rating')
        usefulness_rating = request.POST.get('usefulness_rating')
        preferred_features = request.POST.getlist('preferred_features')
        feedback_text = request.POST.get('feedback_text', '')
        
        # Create or update feedback
        with transaction.atomic():
            feedback, created = EnhancedScoringFeedback.objects.update_or_create(
                response=response,
                scoring_system=scoring_system,
                defaults={
                    'accuracy_rating': accuracy_rating,
                    'usefulness_rating': usefulness_rating,
                    'preferred_features': preferred_features,
                    'feedback_text': feedback_text,
                    'user': request.user if request.user.is_authenticated else None,
                }
            )
        
        messages.success(request, "Thank you for your feedback!")
        return redirect('feedback:response_detail', response_id=response_id)
    
    else:
        # Display feedback form
        if not response_id or not scoring_system_id:
            messages.error(request, "Response and scoring system are required.")
            return redirect('surveys:dashboard')
        
        # Get the response and scoring system
        response = get_object_or_404(Response, id=response_id)
        scoring_system = get_object_or_404(ScoringSystem, id=scoring_system_id)
        
        # Check if feedback already exists
        existing_feedback = EnhancedScoringFeedback.objects.filter(
            response=response,
            scoring_system=scoring_system
        ).first()
        
        # Prepare context
        context = {
            'response': response,
            'response_id': response_id,
            'scoring_system': scoring_system,
            'scoring_system_id': scoring_system_id,
            'existing_feedback': existing_feedback,
        }
        
        return render(request, 'surveys/enhanced_scoring_feedback.html', context)

@require_POST
def calculate_enhanced_score(request, response_id, scoring_system_id):
    """
    API view for calculating enhanced score
    """
    # Get the response and scoring system
    response = get_object_or_404(Response, id=response_id)
    scoring_system = get_object_or_404(ScoringSystem, id=scoring_system_id)
    
    # Calculate enhanced score
    try:
        scoring_service = EnhancedScoringService(scoring_system)
        response_score = scoring_service.calculate_score(response)
        
        # Return success response
        return JsonResponse({
            'success': True,
            'raw_score': response_score.raw_score,
            'z_score': response_score.z_score,
            'percentile': response_score.percentile,
            'score_range': {
                'name': response_score.score_range.name if response_score.score_range else None,
                'min_score': response_score.score_range.min_score if response_score.score_range else None,
                'max_score': response_score.score_range.max_score if response_score.score_range else None,
                'interpretation': response_score.score_range.interpretation if response_score.score_range else None,
            } if response_score.score_range else None,
            'additional_data': response_score.additional_data,
        })
    
    except Exception as e:
        # Return error response
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)
