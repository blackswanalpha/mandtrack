from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.forms import modelformset_factory
from django.utils import timezone
from .models import Questionnaire, Question, QuestionChoice, QRCode, ScoringConfig, EmailTemplate, Survey
from .forms import SurveyForm, QuestionForm, QuestionChoiceForm
import qrcode
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

@login_required
def survey_list(request):
    """
    Display a list of all surveys
    """
    # Get surveys created by the user or in their organizations
    user_surveys = Survey.objects.filter(created_by=request.user)

    # Get surveys from organizations the user is a member of
    org_surveys = Survey.objects.filter(organization__members__user=request.user)

    # Combine and remove duplicates
    surveys = (user_surveys | org_surveys).distinct()

    # Filter by category if provided
    category = request.GET.get('category')
    if category:
        surveys = surveys.filter(category=category)

    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        surveys = surveys.filter(status=status)

    # Get template surveys
    try:
        # Try to get template surveys if the field exists
        template_surveys = Survey.objects.filter(is_template=True)
    except Exception as e:
        # If 'is_template' field doesn't exist, use an empty queryset
        print(f"Error filtering by is_template in survey_list: {e}")
        template_surveys = Survey.objects.none()

    context = {
        'surveys': surveys,
        'template_surveys': template_surveys,
        'categories': Survey.CATEGORY_CHOICES,
        'statuses': Survey.STATUS_CHOICES,
    }

    return render(request, 'surveys/survey_list.html', context)

@login_required
def survey_create(request):
    """
    Create a new survey
    """
    if request.method == 'POST':
        form = SurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.created_by = request.user
            survey.save()

            # If cloning from a template
            template_id = request.POST.get('template_id')
            if template_id:
                try:
                    # Try to get the template survey
                    try:
                        # First try with is_template filter
                        template = get_object_or_404(Survey, pk=template_id, is_template=True)
                    except Exception as e:
                        # If is_template field doesn't exist, just get by ID
                        print(f"Error filtering by is_template: {e}")
                        template = get_object_or_404(Survey, pk=template_id)

                    # Clone questions from template
                    for template_question in template.questions.all():
                        question = Question.objects.create(
                            survey=survey,
                            text=template_question.text,
                            description=template_question.description,
                            question_type=template_question.question_type,
                            required=template_question.required,
                            order=template_question.order
                        )
                        # Clone choices if applicable
                        for template_choice in template_question.choices.all():
                            QuestionChoice.objects.create(
                                question=question,
                                text=template_choice.text,
                                order=template_choice.order,
                                score=template_choice.score
                            )
                except Exception as e:
                    # If there's an error with the template, log it but continue
                    print(f"Error cloning template: {e}")
                    # The survey is still created, just without template questions

            messages.success(request, 'Survey created successfully!')
            return redirect('surveys:survey_detail', pk=survey.pk)
    else:
        form = SurveyForm()

    # Get template surveys for cloning
    try:
        # Try to get template surveys if the field exists
        template_surveys = Survey.objects.filter(is_template=True)
    except Exception as e:
        # If 'is_template' field doesn't exist, use an empty queryset
        print(f"Error filtering by is_template in survey_create: {e}")
        template_surveys = Survey.objects.none()

    return render(request, 'surveys/survey_form.html', {
        'form': form,
        'template_surveys': template_surveys
    })

@login_required
def survey_detail(request, pk):
    """
    Display survey details
    """
    survey = get_object_or_404(Survey, pk=pk)

    # Check if user has permission to view this survey
    if survey.created_by != request.user and not survey.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to view this survey.")
        return redirect('surveys:survey_list')

    questions = survey.questions.all().order_by('order')

    # Get response count
    response_count = survey.get_response_count()

    context = {
        'survey': survey,
        'questions': questions,
        'response_count': response_count,
    }

    return render(request, 'surveys/survey_detail.html', context)

@login_required
def survey_edit(request, pk):
    """
    Edit an existing survey
    """
    survey = get_object_or_404(Survey, pk=pk)

    # Check if user has permission to edit this survey
    if survey.created_by != request.user and not survey.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to edit this survey.")
        return redirect('surveys:survey_detail', pk=pk)

    if request.method == 'POST':
        form = SurveyForm(request.POST, instance=survey)
        if form.is_valid():
            form.save()
            messages.success(request, 'Survey updated successfully!')
            return redirect('surveys:survey_detail', pk=pk)
    else:
        form = SurveyForm(instance=survey)

    return render(request, 'surveys/survey_form.html', {
        'form': form,
        'survey': survey,
        'is_edit': True
    })

@login_required
def survey_delete(request, pk):
    """
    Delete a survey
    """
    survey = get_object_or_404(Survey, pk=pk)

    # Check if user has permission to delete this survey
    if survey.created_by != request.user and not survey.organization.members.filter(user=request.user, role='admin').exists():
        messages.error(request, "You don't have permission to delete this survey.")
        return redirect('surveys:survey_detail', pk=pk)

    if request.method == 'POST':
        survey.delete()
        messages.success(request, 'Survey deleted successfully!')
        return redirect('surveys:survey_list')

    return render(request, 'surveys/survey_confirm_delete.html', {'survey': survey})

@login_required
def question_list(request, pk):
    """
    Display a list of questions for a survey
    """
    survey = get_object_or_404(Survey, pk=pk)

    # Check if user has permission to view this survey's questions
    if survey.created_by != request.user and not survey.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to view this survey's questions.")
        return redirect('surveys:survey_list')

    questions = survey.questions.all().order_by('order')

    return render(request, 'surveys/question_list.html', {
        'survey': survey,
        'questions': questions
    })

@login_required
def question_create(request, survey_pk):
    """
    Create a new question for a survey
    """
    survey = get_object_or_404(Survey, pk=survey_pk)

    # Check if user has permission to add questions to this survey
    if survey.created_by != request.user and not survey.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to add questions to this survey.")
        return redirect('surveys:survey_detail', pk=survey_pk)

    # Get the next order number
    next_order = survey.questions.count() + 1

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        choice_formset = None

        if form.is_valid():
            question = form.save(commit=False)
            question.survey = survey

            # Set the order automatically if not provided or is zero
            if not form.cleaned_data.get('order') or form.cleaned_data.get('order') == 0:
                question.order = next_order

            question.save()

            # Handle choices for multiple choice questions
            if question.question_type in ['radio', 'checkbox', 'dropdown']:
                choice_texts = request.POST.getlist('choice_text')
                choice_scores = request.POST.getlist('choice_score')

                for i, (text, score) in enumerate(zip(choice_texts, choice_scores)):
                    if text:  # Only create choices with text
                        QuestionChoice.objects.create(
                            question=question,
                            text=text,
                            order=i+1,
                            score=int(score) if score else 0
                        )

            messages.success(request, 'Question added successfully!')
            return redirect('surveys:question_list', pk=survey_pk)
    else:
        form = QuestionForm(initial={'order': next_order})
        choice_formset = None

    return render(request, 'surveys/question_form.html', {
        'form': form,
        'choice_formset': choice_formset,
        'survey': survey
    })

@login_required
def country_question_create(request, survey_pk):
    """
    Create a new country question for a survey with minimal input
    """
    survey = get_object_or_404(Survey, pk=survey_pk)

    # Check if user has permission to add questions to this survey
    if survey.created_by != request.user and not survey.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to add questions to this survey.")
        return redirect('surveys:survey_detail', pk=survey_pk)

    # Get the next order number
    next_order = survey.questions.count() + 1

    if request.method == 'POST':
        # Get the question text from the form
        question_text = request.POST.get('text', 'What country are you from?')
        description = request.POST.get('description', '')
        required = request.POST.get('required', 'on') == 'on'

        # Create the question
        question = Question(
            survey=survey,
            text=question_text,
            description=description,
            question_type='country',
            required=required,
            order=next_order,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # Try to get the QuestionType object for 'country'
        try:
            from surveys.models.question_type import QuestionType
            question_type_obj = QuestionType.objects.filter(code='country').first()
            if question_type_obj:
                question.question_type_obj = question_type_obj
        except Exception as e:
            logger.error(f"Error setting question_type_obj: {e}")

        question.save()

        messages.success(request, 'Country question added successfully!')
        return redirect('surveys:question_list', pk=survey_pk)

    # For GET requests, render the country question form
    return render(request, 'surveys/country_question_form.html', {
        'survey': survey,
        'next_order': next_order
    })

@login_required
def question_detail(request, survey_pk, pk):
    """
    Display question details
    """
    survey = get_object_or_404(Survey, pk=survey_pk)
    question = get_object_or_404(Question, pk=pk, survey=survey)

    # Check if user has permission to view this question
    if survey.created_by != request.user and not survey.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to view this question.")
        return redirect('surveys:survey_list')

    choices = question.choices.all().order_by('order')

    return render(request, 'surveys/question_detail.html', {
        'survey': survey,
        'question': question,
        'choices': choices
    })

@login_required
def question_edit(request, survey_pk, pk):
    """
    Edit an existing question
    """
    survey = get_object_or_404(Survey, pk=survey_pk)
    question = get_object_or_404(Question, pk=pk, survey=survey)

    # Check if user has permission to edit this question
    if survey.created_by != request.user and not survey.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to edit this question.")
        return redirect('surveys:question_detail', survey_pk=survey_pk, pk=pk)

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)

        if form.is_valid():
            form.save()

            # Handle choices for multiple choice questions
            if question.question_type in ['radio', 'checkbox', 'dropdown']:
                # First, delete existing choices
                question.choices.all().delete()

                # Then create new ones
                choice_texts = request.POST.getlist('choice_text')
                choice_scores = request.POST.getlist('choice_score')

                for i, (text, score) in enumerate(zip(choice_texts, choice_scores)):
                    if text:  # Only create choices with text
                        QuestionChoice.objects.create(
                            question=question,
                            text=text,
                            order=i+1,
                            score=int(score) if score else 0
                        )

            messages.success(request, 'Question updated successfully!')
            return redirect('surveys:question_detail', survey_pk=survey_pk, pk=pk)
    else:
        form = QuestionForm(instance=question)

    choices = question.choices.all().order_by('order')

    return render(request, 'surveys/question_form.html', {
        'form': form,
        'survey': survey,
        'question': question,
        'choices': choices,
        'is_edit': True
    })

@login_required
def question_delete(request, survey_pk, pk):
    """
    Delete a question
    """
    survey = get_object_or_404(Survey, pk=survey_pk)
    question = get_object_or_404(Question, pk=pk, survey=survey)

    # Check if user has permission to delete this question
    if survey.created_by != request.user and not survey.organization.members.filter(user=request.user, role__in=['admin', 'manager']).exists():
        messages.error(request, "You don't have permission to delete this question.")
        return redirect('surveys:question_detail', survey_pk=survey_pk, pk=pk)

    if request.method == 'POST':
        # Delete the question
        question.delete()

        # Reorder remaining questions
        for i, q in enumerate(survey.questions.all().order_by('order')):
            q.order = i + 1
            q.save()

        messages.success(request, 'Question deleted successfully!')
        return redirect('surveys:question_list', pk=survey_pk)

    return render(request, 'surveys/question_confirm_delete.html', {
        'survey': survey,
        'question': question
    })

@login_required
def generate_qr_code(request, pk):
    """
    Generate a QR code for a survey
    """
    survey = get_object_or_404(Survey, pk=pk)

    # Check if user has permission to view this survey
    if survey.created_by != request.user and not survey.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to view this survey's QR code.")
        return redirect('surveys:survey_list')

    # If survey already has a QR code, use that
    if survey.qr_code:
        return render(request, 'surveys/qr_code.html', {'survey': survey})

    # Otherwise, generate a new one
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    # Use the survey's URL
    survey_url = request.build_absolute_uri(f"/surveys/{survey.pk}/")
    qr.add_data(survey_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Save the QR code to the survey
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    survey.qr_code.save(f"qr_{survey.pk}.png", buffer, save=True)

    return render(request, 'surveys/qr_code.html', {'survey': survey})


def survey_respond(request, pk=None):
    """
    Public view for responding to a survey via QR code or direct link
    Can be accessed by pk
    """
    # Get the survey by pk
    if pk:
        survey = get_object_or_404(Survey, pk=pk)
    else:
        messages.error(request, "Invalid survey link.")
        return redirect('core:home')

    # Check if survey is active
    if survey.status != 'active':
        messages.error(request, "This survey is not currently active.")
        return redirect('core:home')

    # If the survey requires authentication, check if user is logged in
    if survey.requires_auth and not request.user.is_authenticated:
        messages.info(request, "Please log in to access this survey.")
        return redirect('account_login')

    # Track QR code access if accessed via QR code
    qr_code_id = request.GET.get('qr')
    if qr_code_id:
        try:
            qr_code = survey.qr_codes.get(pk=qr_code_id, is_active=True)
            qr_code.access_count += 1
            qr_code.save()
        except:
            # If QR code doesn't exist or isn't active, just continue
            pass

    # Get all questions for this survey
    questions = survey.questions.all().order_by('order')

    # Handle form submission
    if request.method == 'POST':
        # Get patient information
        patient_email = request.POST.get('patient_email')
        patient_age = request.POST.get('patient_age')
        patient_gender = request.POST.get('patient_gender')

        # Create a new response with patient information
        from feedback.models import Response
        import uuid

        # Generate a UUID for anonymous patients
        patient_identifier = str(uuid.uuid4())

        # Create the response
        response = Response(
            survey=survey,
            patient_identifier=patient_identifier,
            patient_email=patient_email,
            patient_age=patient_age if patient_age else None,
            patient_gender=patient_gender,
            status='completed',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        response.save()

        # Process answers
        for question in questions:
            answer_key = f'question_{question.id}'
            answer_value = request.POST.get(answer_key)

            if answer_value:
                from feedback.models import Answer
                Answer.objects.create(
                    response=response,
                    question=question,
                    answer_text=answer_value
                )

        messages.success(request, "Thank you for completing the questionnaire!")
        return redirect('core:home')

    # Render the questionnaire form
    return render(request, 'surveys/survey_respond.html', {
        'survey': survey,
        'questions': questions
    })
