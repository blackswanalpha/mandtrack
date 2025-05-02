from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Questionnaire
from io import BytesIO
import qrcode

@login_required
def download_qr_code(request, pk):
    """
    Download a QR code for a questionnaire
    """

    questionnaire = get_object_or_404(Questionnaire, pk=pk)

    # Check if user has permission to view this questionnaire
    if questionnaire.created_by != request.user and not questionnaire.organization.members.filter(user=request.user).exists():
        return HttpResponse("Permission denied", status=403)

    # Get QR code parameters from request
    size = request.GET.get('size', 'medium')

    # Set box size based on requested size
    if size == 'small':
        box_size = 6
    elif size == 'large':
        box_size = 14
    else:  # medium
        box_size = 10

    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=4,
    )

    # Use the direct questionnaire access URL
    questionnaire_url = request.build_absolute_uri(f"/q/{questionnaire.pk}/")
    qr.add_data(questionnaire_url)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="white")

    # Save to buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")

    # Prepare response
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="image/png")
    response['Content-Disposition'] = f'attachment; filename="qr_code_{questionnaire.slug}.png"'

    return response
