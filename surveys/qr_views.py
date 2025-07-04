from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET
from .models import Questionnaire, QRCode
from .forms import QRCodeForm
import qrcode
from io import BytesIO
from django.core.files import File

@login_required
def qr_code_list(request):
    """
    Display a list of QR codes
    """
    # Get QR codes created by the user or in their organizations
    user_qr_codes = QRCode.objects.filter(created_by=request.user)

    # Get QR codes from organizations the user is a member of
    org_qr_codes = QRCode.objects.filter(survey__organization__members__user=request.user)

    # Combine and remove duplicates
    qr_codes = (user_qr_codes | org_qr_codes).distinct().order_by('-created_at')

    return render(request, 'surveys/qr_code_list.html', {
        'qr_codes': qr_codes
    })

@login_required
@require_GET
def qr_code_list_redirect(request):
    """
    Redirect to the QR codes list page
    """
    # Check if we're coming from /questionnaires/qr-codes/
    if request.path.startswith('/questionnaires/'):
        return redirect('/questionnaires/qr-codes/list/')
    else:
        return redirect('/qr/codes/list/')

@login_required
def qr_code_create(request):
    """
    Create a new QR code
    """
    if request.method == 'POST':
        form = QRCodeForm(request.POST, user=request.user)
        if form.is_valid():
            qr_code = form.save(commit=False)
            qr_code.created_by = request.user

            # Generate URL for the QR code that redirects directly to the questionnaire
            questionnaire = qr_code.survey
            # Use the questionnaire ID directly without any formatting
            qr_code.url = request.build_absolute_uri(f"/q/{questionnaire.id}/?qr={qr_code.id}")

            qr_code.save()
            messages.success(request, 'QR code created successfully.')
            return redirect('surveys:qr_code_detail', pk=qr_code.pk)
    else:
        form = QRCodeForm(user=request.user)

    return render(request, 'surveys/qr_code_form.html', {
        'form': form,
        'is_create': True
    })

@login_required
def qr_code_detail(request, pk):
    """
    Display QR code details
    """
    qr_code = get_object_or_404(QRCode, pk=pk)

    # Check if user has permission to view this QR code
    questionnaire = qr_code.survey
    if qr_code.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to view this QR code.")
        return redirect('surveys:qr_code_list')

    return render(request, 'surveys/qr_code_detail.html', {
        'qr_code': qr_code
    })

@login_required
def generate_survey_qr_code(request, pk):
    """
    Generate a QR code for a questionnaire
    """
    questionnaire = get_object_or_404(Questionnaire, pk=pk)

    # Check if user has permission to view this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        messages.error(request, "You don't have permission to generate a QR code for this questionnaire.")
        return redirect('surveys:survey_list')

    # Check if a QR code already exists for this questionnaire
    existing_qr_codes = QRCode.objects.filter(survey=questionnaire, created_by=request.user)
    if existing_qr_codes.exists():
        # Use the most recent QR code
        qr_code = existing_qr_codes.first()
        messages.info(request, "Using existing QR code for this questionnaire.")
    else:
        # Create a new QR code that redirects directly to the questionnaire
        qr_code = QRCode(
            survey=questionnaire,
            name=f"QR Code for {questionnaire.title}",
            description=f"QR Code for accessing {questionnaire.title}",
            is_active=True,
            created_by=request.user
        )
        qr_code.save()

        # Now update with the correct URL that includes the QR code ID
        # Use the questionnaire ID directly without any formatting
        qr_code.url = request.build_absolute_uri(f"/q/{questionnaire.id}/?qr={qr_code.id}")
        qr_code.save()
        messages.success(request, "QR code generated successfully.")

    # Use the correct URL name with the integer pk
    return redirect('surveys:qr_code_detail', pk=qr_code.pk)