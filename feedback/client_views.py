from django.shortcuts import render, get_object_or_404
from surveys.models import Questionnaire, Question

def client_questionnaire_response(request, questionnaire_pk):
    """
    Client view for responding to a questionnaire with minimal layout
    This view is public and doesn't require authentication
    """
    # Get the questionnaire
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_pk)

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
