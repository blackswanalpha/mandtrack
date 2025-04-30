from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.utils import timezone
import uuid

from .models import User, UserProfile, ClientLoginHistory
from surveys.models import Questionnaire, QRCode

def qr_scan(request):
    """
    View for scanning QR codes
    """
    return render(request, 'users/qr_scan.html')

def qr_email_entry(request):
    """
    View for entering email after scanning QR code
    """
    # Check if QR code is in session
    qr_code_value = request.session.get('qr_code')
    if not qr_code_value:
        messages.error(request, "No QR code found. Please scan a QR code first.")
        return redirect('qr_scan')
    
    # Handle form submission
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, "Please enter your email address.")
            return render(request, 'users/qr_email_entry.html')
        
        # Check if QR code exists
        try:
            qr_code = QRCode.objects.get(id=qr_code_value)
        except QRCode.DoesNotExist:
            try:
                # Try to find by URL
                qr_code = QRCode.objects.get(url=qr_code_value)
            except QRCode.DoesNotExist:
                messages.error(request, "Invalid QR code. Please try again.")
                return redirect('qr_scan')
        
        # Check if QR code is active
        if not qr_code.is_active:
            messages.error(request, "This QR code is no longer active.")
            return redirect('qr_scan')
        
        # Check if QR code has expired
        if qr_code.expires_at and qr_code.expires_at < timezone.now():
            messages.error(request, "This QR code has expired.")
            return redirect('qr_scan')
        
        # Check if questionnaire exists and is active
        questionnaire = qr_code.questionnaire
        if not questionnaire or not questionnaire.is_active:
            messages.error(request, "The questionnaire associated with this QR code is not available.")
            return redirect('qr_scan')
        
        # Check if user exists
        user = User.objects.filter(email=email).first()
        
        if not user:
            # Create a new user with the provided email
            username = f"user_{uuid.uuid4().hex[:8]}"
            user = User.objects.create_user(
                username=username,
                email=email,
                password=uuid.uuid4().hex,  # Random password
                role='user',
                email_verified=True
            )
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            messages.success(request, f"Account created with email {email}. You can now access the questionnaire.")
        
        # Record access
        qr_code.access_count += 1
        qr_code.save()
        
        # Store user ID and questionnaire ID in session
        request.session['qr_user_id'] = str(user.id)
        request.session['qr_questionnaire_id'] = str(questionnaire.id)
        
        # Redirect to questionnaire
        return redirect('survey_respond', pk=questionnaire.id)
    
    return render(request, 'users/qr_email_entry.html', {
        'qr_code': qr_code_value
    })
