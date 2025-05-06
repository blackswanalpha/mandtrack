from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from surveys.models import Questionnaire, Question

def client_questionnaire_response(request, questionnaire_pk):
    """
    Client view for responding to a questionnaire with minimal layout
    This view is public and doesn't require authentication
    """
    # Get the questionnaire
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_pk)

    # Check if this is an organization-specific questionnaire
    if questionnaire.organization:
        # If user is authenticated, check if they are a member of the organization
        if request.user.is_authenticated:
            user_is_member = questionnaire.organization.members.filter(user=request.user, is_active=True).exists()
            if not user_is_member:
                messages.error(request, "You don't have permission to access this questionnaire.")
                return render(request, 'errors/organization_access_denied.html')
        else:
            # If user is not authenticated and this is an organization questionnaire, deny access
            messages.error(request, "You need to be logged in to access this organization's questionnaire.")
            return render(request, 'errors/organization_access_denied.html')

    # Get all questions for this questionnaire using the 'survey' field
    questions = Question.objects.filter(survey=questionnaire).order_by('order')

    # Set a flag to bypass the middleware redirects
    request.session['bypass_auth_redirect'] = True

    # Render the template
    return render(request, 'client/questionnaire_response.html', {
        'questionnaire': questionnaire,
        'questions': questions,
        'is_public_view': True,  # Flag to indicate this is a public view
    })
