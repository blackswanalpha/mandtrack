from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
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
    org_qr_codes = QRCode.objects.filter(questionnaire__organization__members__user=request.user)

    # Combine and remove duplicates
    qr_codes = (user_qr_codes | org_qr_codes).distinct().order_by('-created_at')

    return render(request, 'surveys/qr_code_list.html', {
        'qr_codes': qr_codes
    })

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

            # Generate URL for the QR code
            questionnaire = qr_code.questionnaire
            qr_code.url = request.build_absolute_uri(
                reverse('surveys:survey_respond_slug', kwargs={'slug': questionnaire.slug})
            )

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
    if qr_code.created_by != request.user and not qr_code.questionnaire.organization.members.filter(user=request.user).exists():
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
    existing_qr_codes = QRCode.objects.filter(questionnaire=questionnaire, created_by=request.user)
    if existing_qr_codes.exists():
        # Use the most recent QR code
        qr_code = existing_qr_codes.first()
        messages.info(request, "Using existing QR code for this questionnaire.")
    else:
        # Create a new QR code
        questionnaire_url = request.build_absolute_uri(
            reverse('surveys:survey_respond_slug', kwargs={'slug': questionnaire.slug})
        )

        qr_code = QRCode(
            questionnaire=questionnaire,
            name=f"QR Code for {questionnaire.title}",
            description=f"QR Code for accessing {questionnaire.title}",
            url=questionnaire_url,
            is_active=True,
            created_by=request.user
        )
        qr_code.save()
        messages.success(request, "QR code generated successfully.")

    return redirect('surveys:qr_code_detail', pk=qr_code.pk)
