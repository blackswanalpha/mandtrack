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

from surveys.models import Questionnaire, Question, QRCode, QuestionChoice
from feedback.models import Response, Answer, AIAnalysis
from .models import Member, MemberAccess
from core.pdf_utils import pdf_generator

# Import other necessary modules
import qrcode
from io import BytesIO
from django.core.files import File
from django.db import models
import logging

# Set up logging
logger = logging.getLogger(__name__)

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

            # Save the question with the updated question_type
            question_instance.save()

            # Log the question update for debugging
            print(f"Question updated with type: {question_instance.question_type}")

            # Handle choices for multiple choice questions
            if question.question_type in ['single_choice', 'multiple_choice']:
                # First, delete existing choices
                question.choices.all().delete()

                # Then create new ones
                choice_texts = request.POST.getlist('choice_text')
                choice_scores = request.POST.getlist('choice_score')

                for i, (text, score) in enumerate(zip(choice_texts, choice_scores)):
                    if text:  # Only create choices with text
                        try:
                            score_value = float(score) if score else 0
                        except ValueError:
                            score_value = 0

                        # Create the choice using the custom manager that handles created_at and updated_at
                        QuestionChoice.objects.create(
                            question=question,
                            text=text,
                            order=i+1,
                            score=score_value
                        )

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
