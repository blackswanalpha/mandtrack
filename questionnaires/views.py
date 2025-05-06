from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from surveys.models import Questionnaire
import logging

logger = logging.getLogger(__name__)

@login_required
def questionnaire_settings(request, id):
    """
    Display and handle the questionnaire settings form
    """
    try:
        questionnaire = get_object_or_404(Questionnaire, pk=id)

        # Check if user has permission to edit this questionnaire
        if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
            messages.error(request, "You don't have permission to edit this questionnaire's settings.")
            return redirect('surveys:survey_list')

        if request.method == 'POST':
            # Process form submission
            try:
                # Update basic settings
                questionnaire.title = request.POST.get('title', questionnaire.title)
                questionnaire.status = request.POST.get('status', questionnaire.status)
                questionnaire.category = request.POST.get('category', questionnaire.category)
                questionnaire.type = request.POST.get('type', questionnaire.type)

                # Update advanced settings
                questionnaire.is_active = request.POST.get('is_active') == 'on'
                questionnaire.is_adaptive = request.POST.get('is_adaptive') == 'on'
                questionnaire.is_qr_enabled = request.POST.get('is_qr_enabled') == 'on'
                questionnaire.is_public = request.POST.get('is_public') == 'on'
                questionnaire.allow_anonymous = request.POST.get('allow_anonymous') == 'on'
                questionnaire.requires_auth = request.POST.get('requires_auth') == 'on'

                # Update version, language, and time limit
                try:
                    questionnaire.version = int(request.POST.get('version', 1))
                except (ValueError, TypeError):
                    questionnaire.version = 1

                questionnaire.language = request.POST.get('language', 'en')

                try:
                    questionnaire.time_limit = int(request.POST.get('time_limit', 0))
                except (ValueError, TypeError):
                    questionnaire.time_limit = 0

                # Update tags
                tags_input = request.POST.get('tags', '')
                if tags_input:
                    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                    questionnaire.tags = tags
                else:
                    questionnaire.tags = []

                # Save the questionnaire
                questionnaire.save()

                messages.success(request, "Questionnaire settings updated successfully!")
                return redirect('questionnaire_settings', id=questionnaire.id)

            except Exception as e:
                logger.error(f"Error updating questionnaire settings: {e}")
                messages.error(request, f"Error updating questionnaire settings: {e}")

        # Render the settings form
        return render(request, 'questionnaires/settings.html', {
            'questionnaire': questionnaire,
        })

    except Exception as e:
        logger.error(f"Error in questionnaire_settings view: {e}")
        messages.error(request, f"An error occurred: {e}")
        return redirect('surveys:survey_list')
