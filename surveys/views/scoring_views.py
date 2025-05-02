from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from surveys.models import Questionnaire, Question, QuestionChoice
from surveys.models import ScoringSystem, ScoreRule, ScoreRange, OptionScore, ResponseScore
from feedback.models import Response

@login_required
def scoring_list(request, questionnaire_id):
    """
    Display a list of scoring systems for a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    
    # Check if user has permission to view this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is a member of the organization
            if not questionnaire.organization.members.filter(user=request.user, is_active=True).exists():
                messages.error(request, "You don't have permission to view this questionnaire's scoring systems.")
                return redirect('surveys:survey_list')
    
    scoring_systems = ScoringSystem.objects.filter(questionnaire=questionnaire)
    
    context = {
        'questionnaire': questionnaire,
        'scoring_systems': scoring_systems,
    }
    
    return render(request, 'surveys/scoring/scoring_list.html', context)

@login_required
def scoring_create(request, questionnaire_id):
    """
    Create a new scoring system for a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    
    # Check if user has permission to edit this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is an admin or manager of the organization
            member = questionnaire.organization.members.filter(user=request.user, is_active=True).first()
            if not member or member.role not in ['admin', 'manager']:
                messages.error(request, "You don't have permission to create scoring systems for this questionnaire.")
                return redirect('surveys:scoring_list', questionnaire_id=questionnaire_id)
        else:
            messages.error(request, "You don't have permission to create scoring systems for this questionnaire.")
            return redirect('surveys:scoring_list', questionnaire_id=questionnaire_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        scoring_type = request.POST.get('scoring_type')
        formula = request.POST.get('formula', '')
        
        if not name or not scoring_type:
            messages.error(request, "Name and scoring type are required.")
            return redirect('surveys:scoring_create', questionnaire_id=questionnaire_id)
        
        # Create the scoring system
        scoring_system = ScoringSystem.objects.create(
            questionnaire=questionnaire,
            name=name,
            description=description,
            scoring_type=scoring_type,
            formula=formula,
            created_by=request.user
        )
        
        messages.success(request, "Scoring system created successfully.")
        return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_system.id)
    
    context = {
        'questionnaire': questionnaire,
        'scoring_types': ScoringSystem.SCORING_TYPE_CHOICES,
    }
    
    return render(request, 'surveys/scoring/scoring_form.html', context)

@login_required
def scoring_detail(request, questionnaire_id, scoring_id):
    """
    Display details of a scoring system
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    scoring_system = get_object_or_404(ScoringSystem, pk=scoring_id, questionnaire=questionnaire)
    
    # Check if user has permission to view this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is a member of the organization
            if not questionnaire.organization.members.filter(user=request.user, is_active=True).exists():
                messages.error(request, "You don't have permission to view this scoring system.")
                return redirect('surveys:survey_list')
    
    # Get all score rules for this scoring system
    score_rules = ScoreRule.objects.filter(scoring_system=scoring_system).select_related('question')
    
    # Get all score ranges for this scoring system
    score_ranges = ScoreRange.objects.filter(scoring_system=scoring_system)
    
    # Get questions that don't have score rules yet
    questions_with_rules = score_rules.values_list('question_id', flat=True)
    questions_without_rules = Question.objects.filter(survey=questionnaire).exclude(id__in=questions_with_rules)
    
    context = {
        'questionnaire': questionnaire,
        'scoring_system': scoring_system,
        'score_rules': score_rules,
        'score_ranges': score_ranges,
        'questions_without_rules': questions_without_rules,
    }
    
    return render(request, 'surveys/scoring/scoring_detail.html', context)

@login_required
def scoring_edit(request, questionnaire_id, scoring_id):
    """
    Edit a scoring system
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    scoring_system = get_object_or_404(ScoringSystem, pk=scoring_id, questionnaire=questionnaire)
    
    # Check if user has permission to edit this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is an admin or manager of the organization
            member = questionnaire.organization.members.filter(user=request.user, is_active=True).first()
            if not member or member.role not in ['admin', 'manager']:
                messages.error(request, "You don't have permission to edit scoring systems for this questionnaire.")
                return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
        else:
            messages.error(request, "You don't have permission to edit scoring systems for this questionnaire.")
            return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        scoring_type = request.POST.get('scoring_type')
        formula = request.POST.get('formula', '')
        
        if not name or not scoring_type:
            messages.error(request, "Name and scoring type are required.")
            return redirect('surveys:scoring_edit', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
        
        # Update the scoring system
        scoring_system.name = name
        scoring_system.description = description
        scoring_system.scoring_type = scoring_type
        scoring_system.formula = formula
        scoring_system.save()
        
        messages.success(request, "Scoring system updated successfully.")
        return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    context = {
        'questionnaire': questionnaire,
        'scoring_system': scoring_system,
        'scoring_types': ScoringSystem.SCORING_TYPE_CHOICES,
    }
    
    return render(request, 'surveys/scoring/scoring_form.html', context)

@login_required
def scoring_delete(request, questionnaire_id, scoring_id):
    """
    Delete a scoring system
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    scoring_system = get_object_or_404(ScoringSystem, pk=scoring_id, questionnaire=questionnaire)
    
    # Check if user has permission to edit this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is an admin of the organization
            member = questionnaire.organization.members.filter(user=request.user, is_active=True).first()
            if not member or member.role != 'admin':
                messages.error(request, "You don't have permission to delete scoring systems for this questionnaire.")
                return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
        else:
            messages.error(request, "You don't have permission to delete scoring systems for this questionnaire.")
            return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    if request.method == 'POST':
        # Delete the scoring system
        scoring_system.delete()
        
        messages.success(request, "Scoring system deleted successfully.")
        return redirect('surveys:scoring_list', questionnaire_id=questionnaire_id)
    
    context = {
        'questionnaire': questionnaire,
        'scoring_system': scoring_system,
    }
    
    return render(request, 'surveys/scoring/scoring_confirm_delete.html', context)

@login_required
def score_rule_create(request, questionnaire_id, scoring_id):
    """
    Create a new score rule for a question
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    scoring_system = get_object_or_404(ScoringSystem, pk=scoring_id, questionnaire=questionnaire)
    
    # Check if user has permission to edit this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is an admin or manager of the organization
            member = questionnaire.organization.members.filter(user=request.user, is_active=True).first()
            if not member or member.role not in ['admin', 'manager']:
                messages.error(request, "You don't have permission to create score rules for this questionnaire.")
                return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
        else:
            messages.error(request, "You don't have permission to create score rules for this questionnaire.")
            return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    if request.method == 'POST':
        question_id = request.POST.get('question')
        weight = request.POST.get('weight', 1.0)
        text_score_enabled = request.POST.get('text_score_enabled') == 'on'
        text_score = request.POST.get('text_score', 0.0)
        notes = request.POST.get('notes', '')
        
        if not question_id:
            messages.error(request, "Question is required.")
            return redirect('surveys:score_rule_create', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
        
        question = get_object_or_404(Question, pk=question_id, survey=questionnaire)
        
        # Create the score rule
        score_rule = ScoreRule.objects.create(
            scoring_system=scoring_system,
            question=question,
            weight=float(weight),
            text_score_enabled=text_score_enabled,
            text_score=float(text_score),
            notes=notes
        )
        
        # If the question has choices, create option scores for each choice
        if question.question_type in ['single_choice', 'multiple_choice']:
            choices = QuestionChoice.objects.filter(question=question)
            for choice in choices:
                option_score = request.POST.get(f'option_score_{choice.id}', 0.0)
                OptionScore.objects.create(
                    score_rule=score_rule,
                    option=choice,
                    score=float(option_score)
                )
        
        messages.success(request, "Score rule created successfully.")
        return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    # Get questions that don't have score rules yet
    questions_with_rules = ScoreRule.objects.filter(scoring_system=scoring_system).values_list('question_id', flat=True)
    questions = Question.objects.filter(survey=questionnaire).exclude(id__in=questions_with_rules)
    
    context = {
        'questionnaire': questionnaire,
        'scoring_system': scoring_system,
        'questions': questions,
    }
    
    return render(request, 'surveys/scoring/score_rule_form.html', context)

@login_required
def score_rule_edit(request, questionnaire_id, scoring_id, rule_id):
    """
    Edit a score rule
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    scoring_system = get_object_or_404(ScoringSystem, pk=scoring_id, questionnaire=questionnaire)
    score_rule = get_object_or_404(ScoreRule, pk=rule_id, scoring_system=scoring_system)
    
    # Check if user has permission to edit this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is an admin or manager of the organization
            member = questionnaire.organization.members.filter(user=request.user, is_active=True).first()
            if not member or member.role not in ['admin', 'manager']:
                messages.error(request, "You don't have permission to edit score rules for this questionnaire.")
                return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
        else:
            messages.error(request, "You don't have permission to edit score rules for this questionnaire.")
            return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    if request.method == 'POST':
        weight = request.POST.get('weight', 1.0)
        text_score_enabled = request.POST.get('text_score_enabled') == 'on'
        text_score = request.POST.get('text_score', 0.0)
        notes = request.POST.get('notes', '')
        
        # Update the score rule
        score_rule.weight = float(weight)
        score_rule.text_score_enabled = text_score_enabled
        score_rule.text_score = float(text_score)
        score_rule.notes = notes
        score_rule.save()
        
        # If the question has choices, update option scores for each choice
        if score_rule.question.question_type in ['single_choice', 'multiple_choice']:
            choices = QuestionChoice.objects.filter(question=score_rule.question)
            for choice in choices:
                option_score = request.POST.get(f'option_score_{choice.id}', 0.0)
                OptionScore.objects.update_or_create(
                    score_rule=score_rule,
                    option=choice,
                    defaults={'score': float(option_score)}
                )
        
        messages.success(request, "Score rule updated successfully.")
        return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    # Get option scores for this rule
    option_scores = OptionScore.objects.filter(score_rule=score_rule)
    
    context = {
        'questionnaire': questionnaire,
        'scoring_system': scoring_system,
        'score_rule': score_rule,
        'option_scores': {score.option_id: score.score for score in option_scores},
    }
    
    return render(request, 'surveys/scoring/score_rule_form.html', context)

@login_required
def score_rule_delete(request, questionnaire_id, scoring_id, rule_id):
    """
    Delete a score rule
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    scoring_system = get_object_or_404(ScoringSystem, pk=scoring_id, questionnaire=questionnaire)
    score_rule = get_object_or_404(ScoreRule, pk=rule_id, scoring_system=scoring_system)
    
    # Check if user has permission to edit this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is an admin or manager of the organization
            member = questionnaire.organization.members.filter(user=request.user, is_active=True).first()
            if not member or member.role not in ['admin', 'manager']:
                messages.error(request, "You don't have permission to delete score rules for this questionnaire.")
                return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
        else:
            messages.error(request, "You don't have permission to delete score rules for this questionnaire.")
            return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    if request.method == 'POST':
        # Delete the score rule
        score_rule.delete()
        
        messages.success(request, "Score rule deleted successfully.")
        return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    context = {
        'questionnaire': questionnaire,
        'scoring_system': scoring_system,
        'score_rule': score_rule,
    }
    
    return render(request, 'surveys/scoring/score_rule_confirm_delete.html', context)

@login_required
def score_range_create(request, questionnaire_id, scoring_id):
    """
    Create a new score range
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    scoring_system = get_object_or_404(ScoringSystem, pk=scoring_id, questionnaire=questionnaire)
    
    # Check if user has permission to edit this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is an admin or manager of the organization
            member = questionnaire.organization.members.filter(user=request.user, is_active=True).first()
            if not member or member.role not in ['admin', 'manager']:
                messages.error(request, "You don't have permission to create score ranges for this questionnaire.")
                return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
        else:
            messages.error(request, "You don't have permission to create score ranges for this questionnaire.")
            return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        min_score = request.POST.get('min_score')
        max_score = request.POST.get('max_score')
        description = request.POST.get('description', '')
        interpretation = request.POST.get('interpretation', '')
        color = request.POST.get('color', 'gray')
        
        if not name or min_score is None or max_score is None:
            messages.error(request, "Name, minimum score, and maximum score are required.")
            return redirect('surveys:score_range_create', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
        
        # Create the score range
        ScoreRange.objects.create(
            scoring_system=scoring_system,
            name=name,
            min_score=float(min_score),
            max_score=float(max_score),
            description=description,
            interpretation=interpretation,
            color=color
        )
        
        messages.success(request, "Score range created successfully.")
        return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    context = {
        'questionnaire': questionnaire,
        'scoring_system': scoring_system,
    }
    
    return render(request, 'surveys/scoring/score_range_form.html', context)

@login_required
def score_range_edit(request, questionnaire_id, scoring_id, range_id):
    """
    Edit a score range
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    scoring_system = get_object_or_404(ScoringSystem, pk=scoring_id, questionnaire=questionnaire)
    score_range = get_object_or_404(ScoreRange, pk=range_id, scoring_system=scoring_system)
    
    # Check if user has permission to edit this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is an admin or manager of the organization
            member = questionnaire.organization.members.filter(user=request.user, is_active=True).first()
            if not member or member.role not in ['admin', 'manager']:
                messages.error(request, "You don't have permission to edit score ranges for this questionnaire.")
                return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
        else:
            messages.error(request, "You don't have permission to edit score ranges for this questionnaire.")
            return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        min_score = request.POST.get('min_score')
        max_score = request.POST.get('max_score')
        description = request.POST.get('description', '')
        interpretation = request.POST.get('interpretation', '')
        color = request.POST.get('color', 'gray')
        
        if not name or min_score is None or max_score is None:
            messages.error(request, "Name, minimum score, and maximum score are required.")
            return redirect('surveys:score_range_edit', questionnaire_id=questionnaire_id, scoring_id=scoring_id, range_id=range_id)
        
        # Update the score range
        score_range.name = name
        score_range.min_score = float(min_score)
        score_range.max_score = float(max_score)
        score_range.description = description
        score_range.interpretation = interpretation
        score_range.color = color
        score_range.save()
        
        messages.success(request, "Score range updated successfully.")
        return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    context = {
        'questionnaire': questionnaire,
        'scoring_system': scoring_system,
        'score_range': score_range,
    }
    
    return render(request, 'surveys/scoring/score_range_form.html', context)

@login_required
def score_range_delete(request, questionnaire_id, scoring_id, range_id):
    """
    Delete a score range
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    scoring_system = get_object_or_404(ScoringSystem, pk=scoring_id, questionnaire=questionnaire)
    score_range = get_object_or_404(ScoreRange, pk=range_id, scoring_system=scoring_system)
    
    # Check if user has permission to edit this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is an admin or manager of the organization
            member = questionnaire.organization.members.filter(user=request.user, is_active=True).first()
            if not member or member.role not in ['admin', 'manager']:
                messages.error(request, "You don't have permission to delete score ranges for this questionnaire.")
                return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
        else:
            messages.error(request, "You don't have permission to delete score ranges for this questionnaire.")
            return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    if request.method == 'POST':
        # Delete the score range
        score_range.delete()
        
        messages.success(request, "Score range deleted successfully.")
        return redirect('surveys:scoring_detail', questionnaire_id=questionnaire_id, scoring_id=scoring_id)
    
    context = {
        'questionnaire': questionnaire,
        'scoring_system': scoring_system,
        'score_range': score_range,
    }
    
    return render(request, 'surveys/scoring/score_range_confirm_delete.html', context)

@login_required
def calculate_response_score(request, questionnaire_id, response_id):
    """
    Calculate score for a response using a scoring system
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    response = get_object_or_404(Response, pk=response_id, questionnaire=questionnaire)
    
    # Check if user has permission to view this response
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is a member of the organization
            if not questionnaire.organization.members.filter(user=request.user, is_active=True).exists():
                messages.error(request, "You don't have permission to calculate scores for this response.")
                return redirect('surveys:survey_detail', pk=questionnaire_id)
        else:
            messages.error(request, "You don't have permission to calculate scores for this response.")
            return redirect('surveys:survey_detail', pk=questionnaire_id)
    
    if request.method == 'POST':
        scoring_id = request.POST.get('scoring_system')
        
        if not scoring_id:
            messages.error(request, "Scoring system is required.")
            return redirect('feedback:response_detail', pk=response_id)
        
        scoring_system = get_object_or_404(ScoringSystem, pk=scoring_id, questionnaire=questionnaire)
        
        try:
            # Calculate the score
            result = scoring_system.calculate_score(response)
            
            # If the result is a dictionary (for range-based scoring), extract the raw score
            raw_score = result if isinstance(result, (int, float)) else result.get('raw_score', 0)
            
            # Find the score range if applicable
            score_range = None
            if scoring_system.scoring_type == 'range_based':
                score_range = ScoreRange.objects.filter(
                    scoring_system=scoring_system,
                    min_score__lte=raw_score,
                    max_score__gte=raw_score
                ).first()
            
            # Create or update the response score
            response_score, created = ResponseScore.objects.update_or_create(
                response=response,
                scoring_system=scoring_system,
                defaults={
                    'raw_score': raw_score,
                    'score_range': score_range,
                    'notes': f"Score calculated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            )
            
            messages.success(request, f"Score calculated successfully: {raw_score}")
            return redirect('feedback:response_detail', pk=response_id)
        
        except Exception as e:
            messages.error(request, f"Error calculating score: {str(e)}")
            return redirect('feedback:response_detail', pk=response_id)
    
    # Get all scoring systems for this questionnaire
    scoring_systems = ScoringSystem.objects.filter(questionnaire=questionnaire)
    
    context = {
        'questionnaire': questionnaire,
        'response': response,
        'scoring_systems': scoring_systems,
    }
    
    return render(request, 'surveys/scoring/calculate_score.html', context)

@login_required
def response_scores(request, questionnaire_id):
    """
    Display scores for all responses to a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    
    # Check if user has permission to view this questionnaire
    if not request.user.is_staff and questionnaire.created_by != request.user:
        if questionnaire.organization:
            # Check if user is a member of the organization
            if not questionnaire.organization.members.filter(user=request.user, is_active=True).exists():
                messages.error(request, "You don't have permission to view scores for this questionnaire.")
                return redirect('surveys:survey_list')
        else:
            messages.error(request, "You don't have permission to view scores for this questionnaire.")
            return redirect('surveys:survey_list')
    
    # Get all responses for this questionnaire
    responses = Response.objects.filter(questionnaire=questionnaire)
    
    # Get all scoring systems for this questionnaire
    scoring_systems = ScoringSystem.objects.filter(questionnaire=questionnaire)
    
    # Get all response scores
    response_scores = ResponseScore.objects.filter(
        response__in=responses,
        scoring_system__in=scoring_systems
    ).select_related('response', 'scoring_system', 'score_range')
    
    # Organize scores by response and scoring system
    scores_by_response = {}
    for response in responses:
        scores_by_response[response.id] = {
            'response': response,
            'scores': {}
        }
    
    for score in response_scores:
        scores_by_response[score.response.id]['scores'][score.scoring_system.id] = score
    
    context = {
        'questionnaire': questionnaire,
        'scoring_systems': scoring_systems,
        'scores_by_response': scores_by_response,
    }
    
    return render(request, 'surveys/scoring/response_scores.html', context)
