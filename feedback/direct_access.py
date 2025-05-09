from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
import logging

from surveys.models import Questionnaire, Question, QuestionChoice
from .models import Response, Answer

logger = logging.getLogger(__name__)

def direct_questionnaire_view(request, pk=None):
    """
    Direct access to a questionnaire via QR code or URL
    This is a simplified version that directly redirects to the respond_to_questionnaire view
    """
    logger.info(f"Direct questionnaire access requested with pk={pk}")

    # Get the questionnaire by UUID
    try:
        questionnaire = Questionnaire.objects.get(pk=pk)
        logger.info(f"Found questionnaire by exact ID match: {questionnaire.id}")
    except Questionnaire.DoesNotExist:
        logger.warning(f"No questionnaire found with exact ID: {pk}")
        try:
            # Try to find by ID containing the UUID
            questionnaires = Questionnaire.objects.filter(id__icontains=pk)
            if questionnaires.exists():
                questionnaire = questionnaires.first()
                logger.info(f"Found questionnaire by partial ID match: {questionnaire.id}")
            else:
                # Get active questionnaires to show as alternatives
                active_questionnaires = Questionnaire.objects.filter(status='active').order_by('-created_at')[:5]
                return render(request, 'errors/questionnaire_not_found.html', {
                    'uuid': pk,
                    'active_questionnaires': active_questionnaires
                })
        except Exception as e:
            logger.error(f"Error finding questionnaire: {str(e)}")
            messages.error(request, "An error occurred while accessing the questionnaire.")
            return redirect('core:home')
    except Exception as e:
        logger.error(f"Unexpected error finding questionnaire: {str(e)}")
        messages.error(request, "An error occurred while accessing the questionnaire.")
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

    # Get all questions for this questionnaire
    questions = Question.objects.filter(survey=questionnaire).order_by('order').prefetch_related('choices')

    # Handle form submission
    if request.method == 'POST':
        # Check if this is a bio data submission
        if 'submit_bio_data' in request.POST:
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
                return render(request, 'feedback/direct_questionnaire.html', {
                    'questionnaire': questionnaire,
                    'questions': questions,
                    'bio_data_collected': False,
                    'bio_data_error': True,
                    'bio_data_values': bio_data_values,
                })

            # Create a new response
            response = Response(
                survey=questionnaire,
                user=request.user if request.user.is_authenticated else None,
                status='in_progress',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                patient_email=patient_email,
                patient_gender=patient_gender
            )

            # Handle patient age
            try:
                response.patient_age = int(patient_age)
                if response.patient_age < 1 or response.patient_age > 120:
                    messages.error(request, "Age must be between 1 and 120.")
                    return render(request, 'feedback/direct_questionnaire.html', {
                        'questionnaire': questionnaire,
                        'questions': questions,
                        'bio_data_collected': False,
                        'bio_data_error': True,
                        'bio_data_values': bio_data_values,
                    })
            except ValueError:
                messages.error(request, "Age must be a valid number.")
                return render(request, 'feedback/direct_questionnaire.html', {
                    'questionnaire': questionnaire,
                    'questions': questions,
                    'bio_data_collected': False,
                    'bio_data_error': True,
                    'bio_data_values': bio_data_values,
                })

            response.save()

            # Start the timer now that bio data has been collected
            request.session['response_start_time'] = timezone.now().timestamp()
            request.session['current_response_id'] = str(response.id)
            request.session['bio_data_collected'] = True

            # Redirect back to the same page to show questions
            messages.success(request, "Patient information saved. Please complete the questionnaire.")
            return render(request, 'feedback/direct_questionnaire.html', {
                'questionnaire': questionnaire,
                'questions': questions,
                'bio_data_collected': True,
                'response': response,
            })

        # Handle questionnaire submission
        elif 'submit_questionnaire' in request.POST:
            # Get the response ID from the session
            response_id = request.session.get('current_response_id')
            if not response_id:
                messages.error(request, "Your session has expired. Please start again.")
                return redirect('core:home')

            # Get the response
            response = get_object_or_404(Response, pk=response_id)

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
                        answer.save()

                    elif question.question_type == 'single_choice':
                        choice_id = request.POST.get(answer_key)
                        if choice_id:
                            try:
                                answer.selected_choice = get_object_or_404(QuestionChoice, pk=choice_id)
                            except:
                                messages.error(request, f"Invalid choice selected for question: {question.text}")
                        elif question.required:
                            messages.error(request, f"Please select an option for question: {question.text}")
                        answer.save()

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
                            messages.error(request, f"Please select at least one option for question: {question.text}")

                        for choice_id in choice_ids:
                            try:
                                choice = get_object_or_404(QuestionChoice, pk=choice_id)
                                answer.multiple_choices.add(choice)
                            except:
                                messages.error(request, f"Invalid choice selected for question: {question.text}")

                    elif question.question_type == 'number' or question.question_type == 'scale':
                        try:
                            answer.numeric_value = float(request.POST.get(answer_key, 0))
                        except ValueError:
                            messages.error(request, f"Invalid number format for question: {question.text}")
                            answer.numeric_value = 0
                        answer.save()

                    elif question.question_type == 'date':
                        try:
                            date_str = request.POST.get(answer_key, '')
                            if date_str:
                                from datetime import datetime
                                answer.date_value = datetime.strptime(date_str, '%Y-%m-%d').date()
                            answer.save()
                        except ValueError:
                            messages.error(request, f"Invalid date format for question: {question.text}")
                            answer.save()

                    elif question.question_type == 'time':
                        try:
                            time_str = request.POST.get(answer_key, '')
                            if time_str:
                                from datetime import datetime
                                answer.time_value = datetime.strptime(time_str, '%H:%M').time()
                            answer.save()
                        except ValueError:
                            messages.error(request, f"Invalid time format for question: {question.text}")
                            answer.save()

                    elif question.question_type == 'country':
                        answer.text_answer = request.POST.get(answer_key, '')
                        answer.save()

                    else:
                        # Default fallback for any other question type
                        answer.text_answer = request.POST.get(answer_key, '')
                        answer.save()

                except Exception as e:
                    logger.error(f"Error processing answer for question {question.id}: {str(e)}")
                    messages.error(request, f"Error processing answer for question: {question.text}")
                    answer.text_answer = request.POST.get(answer_key, '')
                    answer.save()

            # Mark the response as completed
            response.status = 'completed'
            response.completed_at = timezone.now()
            response.save()

            # Calculate completion time if we have a start time in session
            if request.session.get('response_start_time'):
                start_time = request.session.get('response_start_time')
                end_time = timezone.now().timestamp()
                completion_time_seconds = int(end_time - start_time)

                # Update the response with the completion time
                response.completion_time = completion_time_seconds
                response.save(update_fields=['completion_time'])

            # Clear session data
            for key in ['current_response_id', 'response_start_time', 'bio_data_collected']:
                if key in request.session:
                    del request.session[key]

            # Show success message
            messages.success(request, 'Thank you for your response!')
            return render(request, 'feedback/response_complete.html', {'response': response})

    # For GET requests, show the questionnaire form
    bio_data_collected = request.session.get('bio_data_collected', False)
    response = None

    if bio_data_collected and request.session.get('current_response_id'):
        try:
            response = Response.objects.get(pk=request.session.get('current_response_id'))
        except Response.DoesNotExist:
            bio_data_collected = False
            if 'current_response_id' in request.session:
                del request.session['current_response_id']
            if 'bio_data_collected' in request.session:
                del request.session['bio_data_collected']

    return render(request, 'feedback/direct_questionnaire.html', {
        'questionnaire': questionnaire,
        'questions': questions,
        'bio_data_collected': bio_data_collected,
        'response': response,
    })
