from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.conf import settings

from groups.models import Organization
from surveys.models import Questionnaire, QRCode
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64

@login_required
def organization_qr_codes(request, org_id):
    """
    Display QR codes for an organization's questionnaires
    """
    organization = get_object_or_404(Organization, pk=org_id)

    # Check if user has permission to view this organization
    if not request.user.is_staff:
        member = organization.members.filter(user=request.user, is_active=True).first()
        if not member:
            messages.error(request, "You don't have permission to view this organization's QR codes.")
            return redirect('groups:organization_list')

    # Get all questionnaires for this organization
    questionnaires = Questionnaire.objects.filter(organization=organization, is_active=True)

    # Get QR codes for each questionnaire
    qr_codes = {}
    for questionnaire in questionnaires:
        qr_codes[questionnaire.id] = QRCode.objects.filter(survey=questionnaire)

    context = {
        'organization': organization,
        'questionnaires': questionnaires,
        'qr_codes': qr_codes,
    }

    return render(request, 'organizations/qr_codes.html', context)

@login_required
def generate_organization_qr_code(request, org_id, questionnaire_id):
    """
    Generate a QR code for a specific questionnaire in an organization
    """
    organization = get_object_or_404(Organization, pk=org_id)
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id, organization=organization)

    # Check if user has permission to edit this organization
    if not request.user.is_staff:
        member = organization.members.filter(user=request.user, is_active=True).first()
        if not member or member.role not in ['admin', 'manager']:
            messages.error(request, "You don't have permission to generate QR codes for this organization.")
            return redirect('organizations:organization_qr_codes', org_id=org_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')

        if not name:
            messages.error(request, "Name is required.")
            return redirect('organizations:generate_organization_qr_code', org_id=org_id, questionnaire_id=questionnaire_id)

        # Create the QR code object first to get an ID
        qr_code = QRCode.objects.create(
            survey=questionnaire,
            name=name,
            description=description,
            url="",  # Temporary placeholder
            created_by=request.user
        )

        # Now create the QR code URL that redirects to member access page
        url = request.build_absolute_uri(reverse('members:qr_member_access', kwargs={'qr_code_id': qr_code.id}))

        # Update the QR code with the correct URL
        qr_code.url = url
        qr_code.save()

        # Create the QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Create the QR code image
        img = qr.make_image(fill_color="black", back_color="white")

        # Add organization logo if available
        if organization.logo:
            try:
                # Open the logo image
                logo = Image.open(organization.logo.path)

                # Resize the logo to fit in the QR code
                logo_size = int(img.size[0] * 0.2)  # 20% of QR code size
                logo = logo.resize((logo_size, logo_size))

                # Calculate position to center the logo
                pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)

                # Create a white background for the logo
                logo_bg = Image.new('RGBA', (logo_size + 10, logo_size + 10), (255, 255, 255, 255))
                logo_bg.paste(logo, (5, 5))

                # Paste the logo onto the QR code
                img.paste(logo_bg, pos, logo_bg)
            except Exception as e:
                # If there's an error adding the logo, just continue without it
                print(f"Error adding logo to QR code: {e}")

        # Save the QR code image to a buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        # QR code object already created above

        # Save the image to the QR code object
        qr_code.image.save(f"qr_{name.lower().replace(' ', '_')}.png", buffer, save=True)

        messages.success(request, "QR code generated successfully.")
        return redirect('organizations:organization_qr_codes', org_id=org_id)

    context = {
        'organization': organization,
        'questionnaire': questionnaire,
    }

    return render(request, 'organizations/generate_qr_code.html', context)

@login_required
def view_qr_code(request, org_id, qr_code_id):
    """
    View a specific QR code
    """
    organization = get_object_or_404(Organization, pk=org_id)
    qr_code = get_object_or_404(QRCode, pk=qr_code_id)
    questionnaire = qr_code.survey

    # Check if the questionnaire belongs to the organization
    if questionnaire.organization != organization:
        messages.error(request, "This QR code does not belong to this organization.")
        return redirect('organizations:organization_qr_codes', org_id=org_id)

    # Check if user has permission to view this organization
    if not request.user.is_staff:
        member = organization.members.filter(user=request.user, is_active=True).first()
        if not member:
            messages.error(request, "You don't have permission to view this organization's QR codes.")
            return redirect('groups:organization_list')

    context = {
        'organization': organization,
        'qr_code': qr_code,
        'questionnaire': questionnaire,
    }

    return render(request, 'organizations/view_qr_code.html', context)

@login_required
def download_qr_code(request, org_id, qr_code_id):
    """
    Download a QR code image
    """
    organization = get_object_or_404(Organization, pk=org_id)
    qr_code = get_object_or_404(QRCode, pk=qr_code_id)
    questionnaire = qr_code.survey

    # Check if the questionnaire belongs to the organization
    if questionnaire.organization != organization:
        messages.error(request, "This QR code does not belong to this organization.")
        return redirect('organizations:organization_qr_codes', org_id=org_id)

    # Check if user has permission to view this organization
    if not request.user.is_staff:
        member = organization.members.filter(user=request.user, is_active=True).first()
        if not member:
            messages.error(request, "You don't have permission to download this organization's QR codes.")
            return redirect('groups:organization_list')

    # Increment the access count
    qr_code.increment_access_count()

    # Return the QR code image
    response = HttpResponse(content_type="image/png")
    response['Content-Disposition'] = f'attachment; filename="{qr_code.name.lower().replace(" ", "_")}_qr_code.png"'

    # Open the image and write it to the response
    qr_code.image.open()
    response.write(qr_code.image.read())
    qr_code.image.close()

    return response

@login_required
def delete_qr_code(request, org_id, qr_code_id):
    """
    Delete a QR code
    """
    organization = get_object_or_404(Organization, pk=org_id)
    qr_code = get_object_or_404(QRCode, pk=qr_code_id)
    questionnaire = qr_code.survey

    # Check if the questionnaire belongs to the organization
    if questionnaire.organization != organization:
        messages.error(request, "This QR code does not belong to this organization.")
        return redirect('organizations:organization_qr_codes', org_id=org_id)

    # Check if user has permission to edit this organization
    if not request.user.is_staff:
        member = organization.members.filter(user=request.user, is_active=True).first()
        if not member or member.role not in ['admin', 'manager']:
            messages.error(request, "You don't have permission to delete QR codes for this organization.")
            return redirect('organizations:organization_qr_codes', org_id=org_id)

    if request.method == 'POST':
        # Delete the QR code
        qr_code.delete()

        messages.success(request, "QR code deleted successfully.")
        return redirect('organizations:organization_qr_codes', org_id=org_id)

    context = {
        'organization': organization,
        'qr_code': qr_code,
        'questionnaire': questionnaire,
    }

    return render(request, 'organizations/delete_qr_code.html', context)
