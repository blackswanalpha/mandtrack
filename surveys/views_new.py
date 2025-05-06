from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.forms import modelformset_factory
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.files import File
from django.apps import apps

# Get the actual database models directly
SurveysQuestionnaire = apps.get_model('surveys', 'SurveysQuestionnaire')
SurveysQuestion = apps.get_model('surveys', 'SurveysQuestion')
SurveysQuestionchoice = apps.get_model('surveys', 'SurveysQuestionchoice')
SurveysQrcode = apps.get_model('surveys', 'SurveysQrcode')
SurveysScoringconfig = apps.get_model('surveys', 'SurveysScoringconfig')
SurveysEmailtemplate = apps.get_model('surveys', 'SurveysEmailtemplate')

# Create aliases for backward compatibility
Questionnaire = SurveysQuestionnaire
Question = SurveysQuestion
QuestionChoice = SurveysQuestionchoice
QRCode = SurveysQrcode
ScoringConfig = SurveysScoringconfig
EmailTemplate = SurveysEmailtemplate

from .forms import SurveyForm, QuestionForm, QuestionChoiceForm, QRCodeForm, ScoringConfigForm, EmailTemplateForm
from .utils import log_form_errors, log_model_creation_attempt, log_exception
import qrcode
from io import BytesIO
import logging
import traceback
import json

# Set up logger
logger = logging.getLogger(__name__)

@login_required
def survey_list(request):
    """
    Display a list of all questionnaires
    """
    try:
        # Get questionnaires created by the user or in their organizations
        user_questionnaires = Questionnaire.objects.filter(created_by=request.user)

        # Get questionnaires from organizations the user is a member of
        org_questionnaires = Questionnaire.objects.filter(organization__members__user=request.user)

        # Combine and remove duplicates
        questionnaires = (user_questionnaires | org_questionnaires).distinct()

        # Filter by category if provided
        category = request.GET.get('category')
        if category:
            questionnaires = questionnaires.filter(category=category)

        # Filter by status if provided
        status = request.GET.get('status')
        if status:
            questionnaires = questionnaires.filter(status=status)

        # Get template questionnaires
        template_questionnaires = Questionnaire.objects.filter(is_template=True)

        context = {
            'questionnaires': questionnaires,
            'template_questionnaires': template_questionnaires,
            'categories': Questionnaire.CATEGORY_CHOICES,
            'statuses': Questionnaire.STATUS_CHOICES,
        }

        return render(request, 'surveys/survey_list.html', context)
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in survey_list view: {str(e)}")

        # Show error message to user
        from django.contrib import messages
        messages.error(request, f"An error occurred while loading the questionnaires: {str(e)}")

        # Return empty context
        context = {
            'questionnaires': [],
            'template_questionnaires': [],
            'categories': Questionnaire.CATEGORY_CHOICES,
            'statuses': Questionnaire.STATUS_CHOICES,
        }

        return render(request, 'surveys/survey_list.html', context)

@login_required
def survey_create(request):
    """
    Create a new questionnaire
    """
    if request.method == 'POST':
        form = SurveyForm(request.POST)
        if form.is_valid():
            try:
                # Create the questionnaire but don't save to DB yet
                questionnaire = form.save(commit=False)

                # Set the created_by field to the current user
                questionnaire.created_by = request.user

                # Set default values for fields not in the form
                if not questionnaire.type:
                    questionnaire.type = 'standard'

                # Now save to the database
                questionnaire.save()

                # Save many-to-many relationships if any
                form.save_m2m()

                # If cloning from a template
                template_id = request.POST.get('template_id')
                if template_id:
                    try:
                        template = get_object_or_404(Questionnaire, pk=template_id, is_template=True)
                        # Clone questions from template
                        for template_question in template.questions.all():
                            question = Question.objects.create(
                                survey=questionnaire,
                                text=template_question.text,
                                description=template_question.description,
                                question_type=template_question.question_type,
                                required=template_question.required,
                                order=template_question.order
                            )
                            # Clone choices if applicable
                            for template_choice in template_question.choices.all():
                                # Use direct SQL to insert the choice
                                # This bypasses model validation issues
                                from django.utils import timezone
                                from django.db import connection

                                now = timezone.now()

                                # Use SQL to directly insert into the database
                                with connection.cursor() as cursor:
                                    cursor.execute("""
                                        INSERT INTO surveys_questionchoice
                                        (question_id, text, "order", score, is_correct, created_at, updated_at)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                                    """, [
                                        question.id,
                                        template_choice.text,
                                        template_choice.order,
                                        template_choice.score,
                                        False,  # is_correct default value
                                        now,
                                        now
                                    ])
                    except Exception as e:
                        # If there's an error with the template, log it but continue
                        print(f"Error cloning template: {e}")
                        # The questionnaire is still created, just without template questions

                messages.success(request, 'Questionnaire created successfully!')
                return redirect('surveys:survey_detail', pk=questionnaire.pk)

            except Exception as e:
                # If there's an error saving the questionnaire, show it to the user
                print(f"Error creating questionnaire: {e}")
                messages.error(request, f"Error creating questionnaire: {e}")
        else:
            # If the form is not valid, show the errors
            print(f"Form errors: {form.errors}")
    else:
        form = SurveyForm()

    # Get template questionnaires for cloning
    template_questionnaires = Questionnaire.objects.filter(is_template=True)

    return render(request, 'surveys/survey_form.html', {
        'form': form,
        'template_questionnaires': template_questionnaires
    })

@login_required
def survey_preview(request, pk):
    """
    Preview a questionnaire with progress bar and navigation
    """
    questionnaire = get_object_or_404(Questionnaire, pk=pk)

    # Check if this is a preview request
    is_preview = request.GET.get('preview') == 'true'
    is_creator = request.user == questionnaire.created_by
    is_admin = request.user.is_staff

    # If it's a preview or the user is the creator/admin, allow access regardless of questionnaire status
    if is_preview or is_creator or is_admin:
        # Allow access for preview mode
        pass
    # Otherwise, check if user has permission to view this questionnaire
    elif questionnaire.created_by != request.user:
        if questionnaire.organization and not questionnaire.organization.members.filter(user=request.user).exists():
            messages.error(request, "You don't have permission to preview this questionnaire.")
            return redirect('surveys:survey_list')
        elif not questionnaire.organization:
            messages.error(request, "You don't have permission to preview this questionnaire.")
            return redirect('surveys:survey_list')

    # Get all questions for this questionnaire
    questions = questionnaire.questions.all().order_by('order')

    # Get the current question index from the query parameters, default to 1
    current_question_index = int(request.GET.get('question', 1))

    # Ensure the index is valid
    if current_question_index < 1:
        current_question_index = 1
    elif current_question_index > questions.count():
        current_question_index = questions.count()

    # Get the current question
    try:
        current_question = questions[current_question_index - 1]
    except IndexError:
        current_question = None

    # Calculate progress percentage
    progress_percentage = 0
    if questions.count() > 0:
        progress_percentage = (current_question_index / questions.count()) * 100

    return render(request, 'surveys/survey_preview.html', {
        'questionnaire': questionnaire,
        'questions': questions,
        'current_question': current_question,
        'current_question_index': current_question_index,
        'total_questions': questions.count(),
        'progress_percentage': progress_percentage,
        'next_question_index': min(current_question_index + 1, questions.count()),
        'prev_question_index': max(current_question_index - 1, 1)
    })

@login_required
def survey_detail(request, pk):
    """
    Display questionnaire details
    """
    questionnaire = get_object_or_404(Questionnaire, pk=pk)

    # Check if user has permission to view this questionnaire
    if questionnaire.created_by != request.user:
        # If the questionnaire has an organization, check if the user is a member
        if questionnaire.organization and not questionnaire.organization.members.filter(user=request.user).exists():
            messages.error(request, "You don't have permission to view this questionnaire.")
            return redirect('surveys:survey_list')
        # If no organization and not the creator, deny access
        elif not questionnaire.organization:
            messages.error(request, "You don't have permission to view this questionnaire.")
            return redirect('surveys:survey_list')

    questions = questionnaire.questions.all().order_by('order')

    # Get response count - handle case where get_response_count might not exist
    try:
        response_count = questionnaire.get_response_count()
    except AttributeError:
        # Fallback: try to count responses directly
        try:
            # Try to access the responses related field
            if hasattr(questionnaire, 'responses'):
                response_count = questionnaire.responses.count()
            # If that fails, try member_accesses
            elif hasattr(questionnaire, 'member_accesses'):
                response_count = questionnaire.member_accesses.filter(is_used=True).count()
            else:
                # If all else fails, default to 0
                response_count = 0
            logger.info(f"Calculated response count fallback: {response_count}")
        except Exception as e:
            logger.error(f"Error calculating response count: {e}")
            response_count = 0

    context = {
        'questionnaire': questionnaire,
        'questions': questions,
        'response_count': response_count,
    }

    return render(request, 'surveys/survey_detail.html', context)

@login_required
def survey_edit(request, pk):
    """
    Edit an existing questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, pk=pk)

    # Check if user has permission to edit this questionnaire
    if questionnaire.created_by != request.user:
        # If the questionnaire has an organization, check if the user is a member with appropriate role
        if questionnaire.organization and not questionnaire.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
            messages.error(request, "You don't have permission to edit this questionnaire.")
            return redirect('surveys:survey_detail', pk=pk)
        # If no organization and not the creator, deny access
        elif not questionnaire.organization:
            messages.error(request, "You don't have permission to edit this questionnaire.")
            return redirect('surveys:survey_detail', pk=pk)

    if request.method == 'POST':
        form = SurveyForm(request.POST, instance=questionnaire)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Questionnaire updated successfully!')
                return redirect('surveys:survey_detail', pk=pk)
            except Exception as e:
                print(f"Error updating questionnaire: {e}")
                messages.error(request, f"Error updating questionnaire: {e}")
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = SurveyForm(instance=questionnaire)

    return render(request, 'surveys/survey_form.html', {
        'form': form,
        'questionnaire': questionnaire,
        'is_edit': True
    })

@login_required
def survey_delete(request, pk):
    """
    Delete a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, pk=pk)

    # Check if user has permission to delete this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user, role='admin').exists():
        messages.error(request, "You don't have permission to delete this questionnaire.")
        return redirect('surveys:survey_detail', pk=pk)

    if request.method == 'POST':
        questionnaire.delete()
        messages.success(request, 'Questionnaire deleted successfully!')
        return redirect('surveys:survey_list')

    return render(request, 'surveys/survey_confirm_delete.html', {'questionnaire': questionnaire})

@login_required
def survey_archive(request, pk):
    """
    Archive a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, pk=pk)

    # Check if user has permission to archive this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to archive this questionnaire.")
        return redirect('surveys:survey_detail', pk=pk)

    if request.method == 'POST':
        questionnaire.status = 'archived'
        questionnaire.save()
        messages.success(request, 'Questionnaire archived successfully!')
        return redirect('surveys:survey_list')

    return render(request, 'surveys/survey_confirm_archive.html', {'questionnaire': questionnaire})

@login_required
def survey_restore(request, pk):
    """
    Restore an archived questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, pk=pk)

    # Check if user has permission to restore this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to restore this questionnaire.")
        return redirect('surveys:survey_detail', pk=pk)

    if request.method == 'POST':
        questionnaire.status = 'draft'
        questionnaire.save()
        messages.success(request, 'Questionnaire restored successfully!')
        return redirect('surveys:survey_detail', pk=pk)

    return redirect('surveys:survey_archive_list')

@login_required
def survey_archive_list(request):
    """
    Display a list of archived questionnaires
    """
    # Get archived questionnaires created by the user or in their organizations
    user_questionnaires = Questionnaire.objects.filter(created_by=request.user, status='archived')
    org_questionnaires = Questionnaire.objects.filter(organization__members__user=request.user, status='archived')

    # Combine and remove duplicates
    archived_surveys = (user_questionnaires | org_questionnaires).distinct()

    # Filter by category if provided
    category = request.GET.get('category')
    if category:
        archived_surveys = archived_surveys.filter(category=category)

    # Sort by different criteria
    sort = request.GET.get('sort', 'recent')
    if sort == 'title':
        archived_surveys = archived_surveys.order_by('title')
    elif sort == 'oldest':
        archived_surveys = archived_surveys.order_by('updated_at')
    else:  # recent
        archived_surveys = archived_surveys.order_by('-updated_at')

    # Search functionality
    search = request.GET.get('search')
    if search:
        archived_surveys = archived_surveys.filter(
            models.Q(title__icontains=search) |
            models.Q(description__icontains=search)
        )

    # Get category choices for the filter dropdown
    category_choices = Questionnaire.CATEGORY_CHOICES

    context = {
        'archived_surveys': archived_surveys,
        'category_choices': category_choices,
    }

    return render(request, 'surveys/survey_archive.html', context)

@login_required
def question_list(request, pk):
    """
    Display a list of questions for a questionnaire
    """
    # Add extra validation for pk
    if not pk:
        messages.error(request, "Invalid questionnaire ID.")
        return redirect('surveys:survey_list')

    try:
        questionnaire = get_object_or_404(Questionnaire, pk=pk)
    except (ValueError, TypeError):
        messages.error(request, "Invalid questionnaire ID format.")
        return redirect('surveys:survey_list')

    # Log the questionnaire for debugging
    logger.info(f"Viewing questions for questionnaire: {questionnaire.id}, title: {questionnaire.title}")

    # Check if user has permission to view this questionnaire's questions
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to view this questionnaire's questions.")
        return redirect('surveys:survey_list')

    # Get all questions for this questionnaire
    questions = questionnaire.questions.all().order_by('order')

    # Log the questions for debugging
    logger.info(f"Found {questions.count()} questions for questionnaire {questionnaire.id}")
    for q in questions:
        logger.info(f"Question ID: {q.id}, Text: {q.text}, Type: {q.question_type}")

        # For choice questions, log the choices
        if q.question_type in ['single_choice', 'multiple_choice']:
            choices = q.choices.all()
            logger.info(f"  Choices: {choices.count()}")
            for c in choices:
                logger.info(f"    Choice ID: {c.id}, Text: {c.text}, Score: {c.score}")

    return render(request, 'surveys/question_list.html', {
        'questionnaire': questionnaire,
        'questions': questions
    })

@login_required
def question_create(request, survey_pk):
    """
    Create a new question for a questionnaire - simplified version for reliability
    """
    questionnaire = get_object_or_404(Questionnaire, pk=survey_pk)

    # Check if user has permission to add questions to this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to add questions to this questionnaire.")
        return redirect('surveys:survey_detail', pk=survey_pk)

    # Get the next order number
    next_order = questionnaire.questions.count() + 1

    if request.method == 'POST':
        # Log the raw POST data for debugging
        logger.info(f"Question creation POST data: {json.dumps(dict(request.POST))}")

        form = QuestionForm(request.POST)

        # Log form data before validation
        logger.info(f"Form data before validation: {json.dumps({field: form[field].value() for field in form.fields})}")

        if form.is_valid():
            try:
                # SIMPLIFIED APPROACH: Create the question directly
                logger.info("Using simplified question creation approach")

                # Get the cleaned data from the form
                question_data = form.cleaned_data
                question_type = question_data.get('question_type', 'text')

                logger.info(f"Creating question with type: {question_type}")

                # Try to get the QuestionType object
                try:
                    from .models import QuestionType
                    question_type_obj = QuestionType.objects.filter(code=question_type).first()
                    logger.info(f"Found QuestionType: {question_type_obj}")
                except Exception as e:
                    logger.error(f"Error getting QuestionType: {e}")
                    question_type_obj = None

                # Set default values for scoring fields based on question type
                is_scored = question_data.get('is_scored', False)
                scoring_weight = question_data.get('scoring_weight')
                max_score = question_data.get('max_score')

                # If scoring fields are not provided but question is scored, use defaults
                if is_scored:
                    if scoring_weight is None:
                        if question_type_obj and question_type_obj.is_scorable:
                            scoring_weight = question_type_obj.default_scoring_weight
                        else:
                            scoring_weight = 1.0
                        logger.info(f"Using default scoring_weight: {scoring_weight}")

                    if max_score is None:
                        if question_type_obj and question_type_obj.is_scorable:
                            max_score = question_type_obj.default_max_score
                        else:
                            max_score = 0
                        logger.info(f"Using default max_score: {max_score}")
                else:
                    # If question is not scored, use default values
                    scoring_weight = 1.0
                    max_score = 0

                # Create the question directly
                question = Question(
                    survey=questionnaire,
                    text=question_data.get('text', ''),
                    description=question_data.get('description', ''),
                    question_type=question_type,
                    question_type_obj=question_type_obj,
                    required=question_data.get('required', True),
                    is_scored=is_scored,
                    is_visible=question_data.get('is_visible', True),
                    scoring_weight=scoring_weight,
                    max_score=max_score,
                    category=question_data.get('category')
                )

                # Log the question data
                logger.info(f"Question data: {vars(question)}")

                # Handle order field
                order_value = question_data.get('order', 0)
                if order_value > 0:
                    # User specified an order - shift other questions if needed
                    with transaction.atomic():
                        # Set this question's order
                        question.order = order_value

                        # Shift questions with order >= the new order down by 1
                        questionnaire.questions.filter(order__gte=order_value).update(order=models.F('order') + 1)
                else:
                    # Auto-assign at the end
                    question.order = next_order

                # Save the question
                question.save()
                logger.info(f"Question saved with ID: {question.id}")

                # Verify the question was saved
                saved_question = Question.objects.filter(id=question.id).first()
                if not saved_question:
                    logger.error("Failed to verify question was saved")
                    raise Exception("Question could not be saved to the database")

                # For choice-based questions, handle the choices
                if question_type in ['single_choice', 'multiple_choice']:
                    choice_texts = request.POST.getlist('choice_text')
                    choice_scores = request.POST.getlist('choice_score')

                    logger.info(f"Processing {len(choice_texts)} choices")

                    # Filter out empty choices
                    valid_choices = [(text, score) for text, score in zip(choice_texts, choice_scores) if text.strip()]

                    # If no valid choices, create default ones
                    if not valid_choices:
                        valid_choices = [("Option 1", "0"), ("Option 2", "0")]
                        logger.info("Using default choices")

                    # Create the choices
                    for i, (text, score) in enumerate(valid_choices):
                        try:
                            score_value = float(score) if score else 0
                        except ValueError:
                            score_value = 0

                        # Use direct SQL to insert the choice
                        # This bypasses model validation issues
                        from django.utils import timezone
                        from django.db import connection

                        now = timezone.now()

                        # Use SQL to directly insert into the database
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                INSERT INTO surveys_questionchoice
                                (question_id, text, "order", score, is_correct, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, [
                                question.id,
                                text,
                                i+1,
                                score_value,
                                False,  # is_correct default value
                                now,
                                now
                            ])
                        logger.info(f"Created choice {i+1}: {text}")

                messages.success(request, 'Question added successfully!')
                return redirect('surveys:question_list', pk=survey_pk)

            except Exception as e:
                # Log any exceptions
                logger.error(f"Error creating question: {str(e)}")
                messages.error(request, f"Error creating question: {str(e)}")
        else:
            # Log form validation errors
            logger.error(f"Form validation failed: {form.errors}")
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = QuestionForm(initial={'order': next_order})

    # Add debug information to the context
    context = {
        'form': form,
        'questionnaire': questionnaire,
    }

    # Add debug info in development
    if settings.DEBUG:
        post_data = None
        if request.method == 'POST':
            post_data = dict(request.POST)
            if 'csrfmiddlewaretoken' in post_data:
                post_data['csrfmiddlewaretoken'] = '[REDACTED]'

        context['debug_info'] = {
            'form_data': {field: form[field].value() for field in form.fields},
            'form_errors': form.errors if hasattr(form, 'errors') else None,
            'post_data': post_data,
            'question_type_choices': [choice[0] for choice in Question.TYPE_CHOICES],
        }

    return render(request, 'surveys/question_form.html', context)

@login_required
def question_detail(request, survey_pk, pk):
    """
    Display question details
    """
    questionnaire = get_object_or_404(Questionnaire, pk=survey_pk)
    question = get_object_or_404(Question, pk=pk, survey=questionnaire)

    # Check if user has permission to view this question
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to view this question.")
        return redirect('surveys:survey_list')

    choices = question.choices.all().order_by('order')

    return render(request, 'surveys/question_detail.html', {
        'survey': questionnaire,  # Use 'survey' to match the template variable
        'questionnaire': questionnaire,  # Keep this for backward compatibility
        'question': question,
        'choices': choices
    })

@login_required
def question_edit(request, survey_pk, pk):
    """
    Edit an existing question
    """
    questionnaire = get_object_or_404(Questionnaire, pk=survey_pk)
    question = get_object_or_404(Question, pk=pk, survey=questionnaire)

    # Check if user has permission to edit this question
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to edit this question.")
        return redirect('surveys:question_detail', survey_pk=survey_pk, pk=pk)

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)

        if form.is_valid():
            # Get the question instance but don't save it yet
            question_instance = form.save(commit=False)

            # Ensure question_type is explicitly set from the form
            question_instance.question_type = form.cleaned_data.get('question_type', 'text')

            # Handle order changes
            old_order = question.order
            new_order = form.cleaned_data.get('order', 0)

            # If order has changed and is not 0 (auto), update question ordering
            if new_order != old_order and new_order > 0:
                with transaction.atomic():
                    # If moving to a higher order (down the list)
                    if new_order > old_order:
                        # Shift questions between old and new order up by 1
                        questionnaire.questions.filter(
                            order__gt=old_order,
                            order__lte=new_order
                        ).exclude(id=question.id).update(order=models.F('order') - 1)
                    # If moving to a lower order (up the list)
                    elif new_order < old_order:
                        # Shift questions between new and old order down by 1
                        questionnaire.questions.filter(
                            order__gte=new_order,
                            order__lt=old_order
                        ).exclude(id=question.id).update(order=models.F('order') + 1)

                    # Set the new order for this question
                    question_instance.order = new_order

            # Save the question with the updated question_type and order
            question_instance.save()

            # Log the question update for debugging
            print(f"Question updated with type: {question_instance.question_type}")

            # Handle choices for multiple choice questions
            if question.question_type in ['single_choice', 'multiple_choice']:
                # Get existing choices
                existing_choices = list(question.choices.all().order_by('order'))

                # Get new choice data
                choice_texts = request.POST.getlist('choice_text')
                choice_scores = request.POST.getlist('choice_score')

                # Filter out empty choices
                valid_choices = [(i+1, text, score) for i, (text, score) in enumerate(zip(choice_texts, choice_scores)) if text.strip()]

                # Import timezone for created_at and updated_at fields
                from django.utils import timezone
                from django.db import connection
                now = timezone.now()

                # Update existing choices or create new ones as needed
                for i, (order, text, score) in enumerate(valid_choices):
                    try:
                        score_value = float(score) if score else 0
                    except ValueError:
                        score_value = 0

                    # If we have an existing choice at this index, update it
                    if i < len(existing_choices):
                        choice = existing_choices[i]
                        # Update the choice using SQL
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                UPDATE surveys_questionchoice
                                SET text = %s, "order" = %s, score = %s, updated_at = %s
                                WHERE id = %s
                            """, [
                                text,
                                order,
                                score_value,
                                now,
                                choice.id
                            ])
                    else:
                        # Create a new choice using SQL
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                INSERT INTO surveys_questionchoice
                                (question_id, text, "order", score, is_correct, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, [
                                question.id,
                                text,
                                order,
                                score_value,
                                False,  # is_correct default value
                                now,
                                now
                            ])

                # If we have more existing choices than new ones, delete the extras
                if len(existing_choices) > len(valid_choices):
                    # Get IDs of choices to keep
                    keep_ids = [choice.id for choice in existing_choices[:len(valid_choices)]]

                    # Delete choices that aren't in the keep_ids list
                    if keep_ids:
                        id_list = ','.join(['?'] * len(keep_ids))
                        with connection.cursor() as cursor:
                            cursor.execute(f"""
                                DELETE FROM surveys_questionchoice
                                WHERE question_id = ? AND id NOT IN ({id_list})
                            """, [question.id] + keep_ids)
                    else:
                        # If no choices to keep, delete all for this question
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                DELETE FROM surveys_questionchoice
                                WHERE question_id = ?
                            """, [question.id])

            messages.success(request, 'Question updated successfully!')
            return redirect('surveys:question_detail', survey_pk=survey_pk, pk=pk)
    else:
        form = QuestionForm(instance=question)

    choices = question.choices.all().order_by('order')

    return render(request, 'surveys/question_form.html', {
        'form': form,
        'questionnaire': questionnaire,
        'question': question,
        'choices': choices,
        'is_edit': True
    })

@login_required
def country_question_create(request, survey_pk):
    """
    Create a new country question for a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, pk=survey_pk)

    # Check if user has permission to add questions to this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to add questions to this questionnaire.")
        return redirect('surveys:survey_detail', pk=survey_pk)

    # Get the next order number
    next_order = questionnaire.questions.count() + 1

    if request.method == 'POST':
        # Log the raw POST data for debugging
        logger.info(f"Country question creation POST data: {json.dumps(dict(request.POST))}")

        # Create a copy of POST data to modify
        post_data = request.POST.copy()

        # Ensure question_type is set to 'country'
        post_data['question_type'] = 'country'

        form = QuestionForm(post_data)

        # Log form data before validation
        logger.info(f"Form data before validation: {json.dumps({field: form[field].value() for field in form.fields})}")

        if form.is_valid():
            try:
                # Create the question directly
                logger.info("Creating country question")

                # Get the cleaned data from the form
                question_data = form.cleaned_data

                # Try to get the QuestionType object
                try:
                    from .models import QuestionType
                    question_type_obj = QuestionType.objects.filter(code='country').first()
                    logger.info(f"Found QuestionType: {question_type_obj}")
                except Exception as e:
                    logger.error(f"Error getting QuestionType: {e}")
                    question_type_obj = None

                # Set default values for scoring fields
                is_scored = question_data.get('is_scored', False)
                scoring_weight = question_data.get('scoring_weight', 1.0)
                max_score = question_data.get('max_score', 0)

                # Create the question directly
                question = Question(
                    survey=questionnaire,
                    text=question_data.get('text', 'Select your country'),
                    description=question_data.get('description', ''),
                    question_type='country',  # Explicitly set to 'country'
                    question_type_obj=question_type_obj,
                    required=question_data.get('required', True),
                    is_scored=is_scored,
                    is_visible=question_data.get('is_visible', True),
                    scoring_weight=scoring_weight,
                    max_score=max_score,
                    category=question_data.get('category')
                )

                # Log the question data
                logger.info(f"Question data: {vars(question)}")

                # Handle order field
                order_value = question_data.get('order', 0)
                if order_value > 0:
                    # User specified an order - shift other questions if needed
                    with transaction.atomic():
                        # Set this question's order
                        question.order = order_value

                        # Shift questions with order >= the new order down by 1
                        questionnaire.questions.filter(order__gte=order_value).update(order=models.F('order') + 1)
                else:
                    # Auto-assign at the end
                    question.order = next_order

                # Save the question
                question.save()
                logger.info(f"Country question saved with ID: {question.id}")

                # Add country choices
                from django.utils import timezone
                from django.db import connection
                import pycountry

                now = timezone.now()

                # Get list of countries
                try:
                    countries = list(pycountry.countries)
                    country_list = [{"name": country.name, "code": country.alpha_2} for country in countries]
                except (ImportError, AttributeError):
                    # Fallback list if pycountry is not available
                    country_list = [
                        {"name": "United States", "code": "US"},
                        {"name": "United Kingdom", "code": "GB"},
                        {"name": "Canada", "code": "CA"},
                        {"name": "Australia", "code": "AU"},
                        {"name": "Germany", "code": "DE"},
                        {"name": "France", "code": "FR"},
                        {"name": "Japan", "code": "JP"},
                        {"name": "China", "code": "CN"},
                        {"name": "India", "code": "IN"},
                        {"name": "Brazil", "code": "BR"},
                    ]

                # Create country choices
                for i, country in enumerate(country_list):
                    try:
                        country_name = country["name"]
                        country_code = country["code"]

                        # Use SQL to directly insert into the database
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                INSERT INTO surveys_questionchoice
                                (question_id, text, "order", score, is_correct, created_at, updated_at, metadata)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, [
                                question.id,
                                country_name,
                                i+1,
                                0,  # score
                                False,  # is_correct
                                now,
                                now,
                                json.dumps({"code": country_code})  # Store country code in metadata
                            ])

                        if i < 5:  # Log only the first few countries to avoid excessive logging
                            logger.info(f"Created country choice {i+1}: {country_name} ({country_code})")
                    except Exception as e:
                        logger.error(f"Error creating country choice: {e}")

                messages.success(request, 'Country question added successfully!')
                return redirect('surveys:question_list', pk=survey_pk)

            except Exception as e:
                # Log any exceptions
                logger.error(f"Error creating country question: {str(e)}")
                messages.error(request, f"Error creating country question: {str(e)}")
        else:
            # Log form validation errors
            logger.error(f"Form validation failed: {form.errors}")
            messages.error(request, "Please correct the errors in the form.")
    else:
        # For GET requests, initialize form with country question type
        form = QuestionForm(initial={
            'order': next_order,
            'question_type': 'country',
            'text': 'Select your country',
            'required': True
        })

    # Add debug information to the context
    context = {
        'form': form,
        'questionnaire': questionnaire,
        'is_country_question': True
    }

    # Add debug info in development
    if settings.DEBUG:
        post_data = None
        if request.method == 'POST':
            post_data = dict(request.POST)
            if 'csrfmiddlewaretoken' in post_data:
                post_data['csrfmiddlewaretoken'] = '[REDACTED]'

        context['debug_info'] = {
            'form_data': {field: form[field].value() for field in form.fields},
            'form_errors': form.errors if hasattr(form, 'errors') else None,
            'post_data': post_data,
        }

    return render(request, 'surveys/question_form.html', context)


@login_required
def question_delete(request, survey_pk, pk):
    """
    Delete a question
    """
    questionnaire = get_object_or_404(Questionnaire, pk=survey_pk)
    question = get_object_or_404(Question, pk=pk, survey=questionnaire)

    # Check if user has permission to delete this question
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to delete this question.")
        return redirect('surveys:question_detail', survey_pk=survey_pk, pk=pk)

    if request.method == 'POST':
        try:
            # First, manually delete any choices to avoid foreign key issues
            from django.db import connection

            # Use SQL to directly delete choices for this question
            with connection.cursor() as cursor:
                # First, check if there are any related records in feedback_answer_multiple_choices
                cursor.execute("""
                    SELECT COUNT(*) FROM feedback_answer_multiple_choices
                    WHERE questionchoice_id IN (
                        SELECT id FROM surveys_questionchoice WHERE question_id = %s
                    )
                """, [question.id])

                related_count = cursor.fetchone()[0]

                if related_count > 0:
                    # If there are related records, delete them first
                    cursor.execute("""
                        DELETE FROM feedback_answer_multiple_choices
                        WHERE questionchoice_id IN (
                            SELECT id FROM surveys_questionchoice WHERE question_id = %s
                        )
                    """, [question.id])

                # Now delete the choices
                cursor.execute("""
                    DELETE FROM surveys_questionchoice
                    WHERE question_id = %s
                """, [question.id])

            # Now delete the question
            question.delete()

            # Reorder remaining questions
            for i, q in enumerate(questionnaire.questions.all().order_by('order')):
                q.order = i + 1
                q.save()

        except Exception as e:
            messages.error(request, f"Error deleting question: {str(e)}")
            return redirect('surveys:question_detail', survey_pk=survey_pk, pk=pk)

        messages.success(request, 'Question deleted successfully!')
        return redirect('surveys:question_list', pk=survey_pk)

    return render(request, 'surveys/question_confirm_delete.html', {
        'questionnaire': questionnaire,
        'question': question
    })

@login_required
def country_question_create(request, survey_pk):
    """
    Create a new country question for a questionnaire
    This is a specialized version of question_create that automatically sets the question type to 'country'
    and populates it with a list of countries
    """
    questionnaire = get_object_or_404(Questionnaire, pk=survey_pk)

    # Check if user has permission to add questions to this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to add questions to this questionnaire.")
        return redirect('surveys:survey_detail', pk=survey_pk)

    # Get the next order number
    next_order = questionnaire.questions.count() + 1

    if request.method == 'POST':
        # Log the raw POST data for debugging
        logger.info(f"Country question creation POST data: {json.dumps(dict(request.POST))}")

        form = QuestionForm(request.POST)

        # Override the question_type to ensure it's 'country'
        form.data = form.data.copy()
        form.data['question_type'] = 'country'

        if form.is_valid():
            try:
                # Get the cleaned data from the form
                question_data = form.cleaned_data

                # Ensure question_type is 'country'
                question_data['question_type'] = 'country'

                # Try to get the QuestionType object
                try:
                    from .models import QuestionType
                    question_type_obj = QuestionType.objects.filter(code='country').first()
                    logger.info(f"Found QuestionType: {question_type_obj}")
                except Exception as e:
                    logger.error(f"Error getting QuestionType: {e}")
                    question_type_obj = None

                # Create the question
                question = Question(
                    survey=questionnaire,
                    text=question_data.get('text', 'Select your country'),
                    description=question_data.get('description', 'Please select your country from the list'),
                    question_type='country',
                    question_type_obj=question_type_obj,
                    required=question_data.get('required', True),
                    is_scored=question_data.get('is_scored', False),
                    is_visible=question_data.get('is_visible', True),
                    scoring_weight=question_data.get('scoring_weight', 1.0),
                    max_score=question_data.get('max_score', 0),
                    category=question_data.get('category', 'demographic')
                )

                # Handle order field
                order_value = question_data.get('order', 0)
                if order_value > 0:
                    # User specified an order - shift other questions if needed
                    with transaction.atomic():
                        # Set this question's order
                        question.order = order_value

                        # Shift questions with order >= the new order down by 1
                        questionnaire.questions.filter(order__gte=order_value).update(order=models.F('order') + 1)
                else:
                    # Auto-assign at the end
                    question.order = next_order

                # Save the question
                question.save()
                logger.info(f"Country question saved with ID: {question.id}")

                # List of countries to add as choices
                countries = [
                    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina",
                    "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados",
                    "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana",
                    "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon",
                    "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo",
                    "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica",
                    "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia",
                    "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana",
                    "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary",
                    "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan",
                    "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Korea, North", "Korea, South", "Kosovo", "Kuwait",
                    "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania",
                    "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands",
                    "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro",
                    "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand",
                    "Nicaragua", "Niger", "Nigeria", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine",
                    "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar",
                    "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
                    "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles",
                    "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa",
                    "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan",
                    "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia",
                    "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom",
                    "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen",
                    "Zambia", "Zimbabwe"
                ]

                # Add countries as choices
                # Import timezone for created_at and updated_at fields
                from django.utils import timezone
                now = timezone.now()

                for i, country in enumerate(countries):
                    try:
                        # Use direct SQL to insert the choice
                        # This bypasses model validation issues
                        from django.db import connection

                        # Use SQL to directly insert into the database
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                INSERT INTO surveys_questionchoice
                                (question_id, text, "order", score, is_correct, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, [
                                question.id,
                                country,
                                i+1,
                                0,
                                False,  # is_correct default value
                                now,
                                now
                            ])
                        logger.info(f"Created country choice {i+1}: {country}")
                    except Exception as e:
                        # Log the error and continue with the next country
                        logger.error(f"Error creating choice: {e}")
                        continue

                messages.success(request, 'Country question added successfully!')
                return redirect('surveys:question_list', pk=survey_pk)

            except Exception as e:
                # Log any exceptions
                logger.error(f"Error creating country question: {str(e)}")
                messages.error(request, f"Error creating country question: {str(e)}")
        else:
            # Log form validation errors
            logger.error(f"Form validation failed: {form.errors}")
            messages.error(request, "Please correct the errors in the form.")
    else:
        # Pre-populate the form with country question defaults
        initial_data = {
            'order': next_order,
            'text': 'Select your country',
            'description': 'Please select your country from the list',
            'question_type': 'country',
            'required': True,
            'category': 'demographic'
        }
        form = QuestionForm(initial=initial_data)

    context = {
        'form': form,
        'questionnaire': questionnaire,
        'is_country_question': True
    }

    return render(request, 'surveys/question_form.html', context)

@login_required
def generate_qr_code(request, pk):
    """
    Generate a QR code for a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, pk=pk)
    download = request.GET.get('download') == 'true'

    # Check if user has permission to view this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to view this questionnaire's QR code.")
        return redirect('surveys:survey_list')

    # If questionnaire already has a QR code and we're not downloading it, use the template
    if questionnaire.qr_code and not download:
        return render(request, 'surveys/qr_code.html', {'survey': questionnaire})

    # Generate a new QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    # Use the direct questionnaire access URL
    questionnaire_url = request.build_absolute_uri(f"/q/{questionnaire.pk}/")
    qr.add_data(questionnaire_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Save the QR code to the questionnaire if it doesn't exist
    if not questionnaire.qr_code:
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        questionnaire.qr_code.save(f"qr_{questionnaire.id}.png", File(buffer), save=True)

    # If download parameter is provided, return the image as a download
    if download:
        response = HttpResponse(content_type="image/png")
        response['Content-Disposition'] = f'attachment; filename="qr_code_{questionnaire.id}.png"'
        img.save(response, "PNG")
        return response

    # For direct image access (when used in img src), return the image directly
    if 'raw' in request.GET:
        response = HttpResponse(content_type="image/png")
        img.save(response, "PNG")
        return response

    # Otherwise, render the template
    return render(request, 'surveys/qr_code.html', {'survey': questionnaire})


def survey_respond(request, pk=None):
    """
    Public view for responding to a questionnaire via QR code or direct link
    Can be accessed by pk
    """
    # Get the questionnaire by pk
    if pk:
        questionnaire = get_object_or_404(Questionnaire, pk=pk)
    else:
        messages.error(request, "Invalid questionnaire link.")
        return redirect('core:home')

    # Check if questionnaire is active
    if questionnaire.status != 'active':
        messages.error(request, "This questionnaire is not currently active.")
        return redirect('core:home')

    # If the questionnaire requires authentication, check if user is logged in
    if questionnaire.requires_auth and not request.user.is_authenticated:
        messages.info(request, "Please log in to access this questionnaire.")
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

    # Get all questions for this questionnaire
    questions = questionnaire.questions.all().order_by('order')

    # Get the current question index from the query parameters, default to 1
    current_question_index = int(request.GET.get('question', 1))

    # Ensure the index is valid
    if current_question_index < 1:
        current_question_index = 1
    elif current_question_index > questions.count():
        current_question_index = questions.count()

    # Get the current question
    try:
        current_question = questions[current_question_index - 1]
    except IndexError:
        current_question = None

    # Calculate progress percentage
    progress_percentage = 0
    if questions.count() > 0:
        progress_percentage = (current_question_index / questions.count()) * 100

    return render(request, 'surveys/survey_respond.html', {
        'questionnaire': questionnaire,
        'questions': questions,
        'current_question': current_question,
        'current_question_index': current_question_index,
        'total_questions': questions.count(),
        'progress_percentage': progress_percentage,
        'next_question_index': min(current_question_index + 1, questions.count()),
        'prev_question_index': max(current_question_index - 1, 1)
    })


@login_required
def scoring_config_list(request, questionnaire_pk):
    """
    Display a list of scoring configurations for a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_pk)

    # Check if user has permission to view this questionnaire's scoring configs
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to view this questionnaire's scoring configurations.")
        return redirect('surveys:survey_list')

    scoring_configs = questionnaire.scoring_configs.all().order_by('-created_at')

    return render(request, 'surveys/scoring_config_list.html', {
        'questionnaire': questionnaire,
        'scoring_configs': scoring_configs
    })

@login_required
def scoring_config_create(request, questionnaire_pk):
    """
    Create a new scoring configuration for a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_pk)

    # Check if user has permission to add scoring configs to this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to add scoring configurations to this questionnaire.")
        return redirect('surveys:survey_detail', pk=questionnaire_pk)

    if request.method == 'POST':
        form = ScoringConfigForm(request.POST, questionnaire=questionnaire)
        if form.is_valid():
            scoring_config = form.save(commit=False)
            scoring_config.survey = questionnaire
            scoring_config.created_by = request.user
            scoring_config.save()
            messages.success(request, 'Scoring configuration created successfully!')
            return redirect('surveys:scoring_config_detail', questionnaire_pk=questionnaire_pk, pk=scoring_config.pk)
    else:
        form = ScoringConfigForm(questionnaire=questionnaire)

    return render(request, 'surveys/scoring_config_form.html', {
        'form': form,
        'questionnaire': questionnaire,
        'is_create': True
    })

@login_required
def scoring_config_detail(request, questionnaire_pk, pk):
    """
    Display scoring configuration details
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_pk)
    scoring_config = get_object_or_404(ScoringConfig, pk=pk, survey=questionnaire)

    # Check if user has permission to view this scoring config
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to view this scoring configuration.")
        return redirect('surveys:survey_list')

    return render(request, 'surveys/scoring_config_detail.html', {
        'questionnaire': questionnaire,
        'scoring_config': scoring_config
    })

@login_required
def scoring_config_edit(request, questionnaire_pk, pk):
    """
    Edit an existing scoring configuration
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_pk)
    scoring_config = get_object_or_404(ScoringConfig, pk=pk, survey=questionnaire)

    # Check if user has permission to edit this scoring config
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to edit this scoring configuration.")
        return redirect('surveys:scoring_config_detail', questionnaire_pk=questionnaire_pk, pk=pk)

    if request.method == 'POST':
        form = ScoringConfigForm(request.POST, instance=scoring_config, questionnaire=questionnaire)
        if form.is_valid():
            form.save()
            messages.success(request, 'Scoring configuration updated successfully!')
            return redirect('surveys:scoring_config_detail', questionnaire_pk=questionnaire_pk, pk=pk)
    else:
        form = ScoringConfigForm(instance=scoring_config, questionnaire=questionnaire)

    return render(request, 'surveys/scoring_config_form.html', {
        'form': form,
        'questionnaire': questionnaire,
        'scoring_config': scoring_config,
        'is_edit': True
    })

@login_required
def scoring_config_delete(request, questionnaire_pk, pk):
    """
    Delete a scoring configuration
    """
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_pk)
    scoring_config = get_object_or_404(ScoringConfig, pk=pk, survey=questionnaire)

    # Check if user has permission to delete this scoring config
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to delete this scoring configuration.")
        return redirect('surveys:scoring_config_detail', questionnaire_pk=questionnaire_pk, pk=pk)

    if request.method == 'POST':
        scoring_config.delete()
        messages.success(request, 'Scoring configuration deleted successfully!')
        return redirect('surveys:scoring_config_list', questionnaire_pk=questionnaire_pk)

    return render(request, 'surveys/scoring_config_confirm_delete.html', {
        'questionnaire': questionnaire,
        'scoring_config': scoring_config
    })

@login_required
def email_template_list(request):
    """
    Display a list of email templates
    """
    # Get templates created by the user or in their organizations
    user_templates = EmailTemplate.objects.filter(created_by=request.user)

    # Get templates from organizations the user is a member of
    org_templates = EmailTemplate.objects.filter(organization__members__user=request.user)

    # Combine and remove duplicates
    templates = (user_templates | org_templates).distinct().order_by('-created_at')

    return render(request, 'surveys/email_template_list.html', {
        'templates': templates
    })

@login_required
def email_template_create(request):
    """
    Create a new email template
    """
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, 'Email template created successfully!')
            return redirect('surveys:email_template_detail', pk=template.pk)
    else:
        form = EmailTemplateForm()

    return render(request, 'surveys/email_template_form.html', {
        'form': form,
        'is_create': True
    })

@login_required
def email_template_detail(request, pk):
    """
    Display email template details
    """
    template = get_object_or_404(EmailTemplate, pk=pk)

    # Check if user has permission to view this template
    if template.created_by != request.user and (template.organization and not template.organization.members.filter(user=request.user).exists()):
        messages.error(request, "You don't have permission to view this email template.")
        return redirect('surveys:email_template_list')

    return render(request, 'surveys/email_template_detail.html', {
        'template': template
    })

@login_required
def email_template_edit(request, pk):
    """
    Edit an existing email template
    """
    template = get_object_or_404(EmailTemplate, pk=pk)

    # Check if user has permission to edit this template
    if template.created_by != request.user and (template.organization and not template.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists()):
        messages.error(request, "You don't have permission to edit this email template.")
        return redirect('surveys:email_template_detail', pk=pk)

    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Email template updated successfully!')
            return redirect('surveys:email_template_detail', pk=pk)
    else:
        form = EmailTemplateForm(instance=template)

    return render(request, 'surveys/email_template_form.html', {
        'form': form,
        'template': template,
        'is_edit': True
    })

@login_required
def email_template_delete(request, pk):
    """
    Delete an email template
    """
    template = get_object_or_404(EmailTemplate, pk=pk)

    # Check if user has permission to delete this template
    if template.created_by != request.user and (template.organization and not template.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists()):
        messages.error(request, "You don't have permission to delete this email template.")
        return redirect('surveys:email_template_detail', pk=pk)

    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Email template deleted successfully!')
        return redirect('surveys:email_template_list')

    return render(request, 'surveys/email_template_confirm_delete.html', {
        'template': template
    })

@login_required
def survey_templates(request):
    """
    Display a list of template questionnaires
    """
    # Get template questionnaires
    templates = Questionnaire.objects.filter(is_template=True).order_by('-created_at')

    # Filter by category if provided
    category = request.GET.get('category')
    if category:
        templates = templates.filter(category=category)

    # Filter by search term if provided
    search = request.GET.get('search')
    if search:
        templates = templates.filter(
            models.Q(title__icontains=search) |
            models.Q(description__icontains=search)
        )

    context = {
        'templates': templates,
        'categories': Questionnaire.CATEGORY_CHOICES,
    }

    return render(request, 'surveys/survey_templates.html', context)

@login_required
def question_reorder(request, survey_pk):
    """
    Reorder questions for a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, pk=survey_pk)

    # Check if user has permission to reorder questions for this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        return HttpResponse(json.dumps({
            'success': False,
            'message': "You don't have permission to reorder questions for this questionnaire."
        }), content_type='application/json')

    if request.method == 'POST':
        try:
            # Get the question IDs from the request
            data = json.loads(request.body)
            question_ids = data.get('question_ids', [])

            # Log the received data
            logger.info(f"Reordering questions for questionnaire {questionnaire.id}")
            logger.info(f"Question IDs: {question_ids}")

            # Validate that all question IDs belong to this questionnaire
            questionnaire_question_ids = set(questionnaire.questions.values_list('id', flat=True))
            if not all(int(qid) in questionnaire_question_ids for qid in question_ids):
                return HttpResponse(json.dumps({
                    'success': False,
                    'message': "Invalid question IDs provided."
                }), content_type='application/json')

            # Update the order of each question
            with transaction.atomic():
                for i, question_id in enumerate(question_ids):
                    question = Question.objects.get(id=question_id)
                    question.order = i + 1
                    question.save(update_fields=['order'])

            return HttpResponse(json.dumps({
                'success': True,
                'message': "Questions reordered successfully!"
            }), content_type='application/json')

        except Exception as e:
            logger.error(f"Error reordering questions: {str(e)}")
            return HttpResponse(json.dumps({
                'success': False,
                'message': f"Error reordering questions: {str(e)}"
            }), content_type='application/json')

    # If not a POST request, return an error
    return HttpResponse(json.dumps({
        'success': False,
        'message': "Invalid request method."
    }), content_type='application/json')
