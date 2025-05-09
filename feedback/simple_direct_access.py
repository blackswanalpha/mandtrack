from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
import logging

from surveys.models import Questionnaire

logger = logging.getLogger(__name__)

def simple_direct_questionnaire_view(request, pk=None):
    """
    Simple direct access to a questionnaire via QR code or URL
    This view just finds the questionnaire and redirects to the respond_to_questionnaire view
    """
    logger.info(f"Simple direct questionnaire access requested with pk={pk}")
    
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
    
    # Check if the questionnaire is active
    if questionnaire.status != 'active':
        logger.warning(f"Questionnaire {questionnaire.id} is not active (status: {questionnaire.status})")
        messages.error(request, "This questionnaire is not currently active.")
        return redirect('core:home')
    
    # Set session flags for direct access
    request.session['direct'] = True
    request.session['bypass_auth_redirect'] = True
    request.session['is_patient_questionnaire'] = True
    logger.info("Set session flags for direct access")
    
    # Redirect to the respond_to_questionnaire view
    redirect_url = f'/responses/questionnaire/{questionnaire.pk}/respond/?direct=true'
    logger.info(f"Redirecting to: {redirect_url}")
    return redirect(redirect_url)
