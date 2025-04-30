from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def home(request):
    """
    Home page view
    Always shows the landing page regardless of authentication status
    """
    return render(request, 'core/home.html')

def about(request):
    """
    About page view
    """
    return render(request, 'core/about.html')

def contact(request):
    """
    Contact page view
    """
    if request.method == 'POST':
        # Process the form data (in a real app, you'd save this to the database or send an email)
        # Commented out to avoid unused variable warnings
        # name = request.POST.get('name')
        # email = request.POST.get('email')
        # subject = request.POST.get('subject')
        # message = request.POST.get('message')

        # In a real app, you would validate the data and save it to the database or send an email

        # Check if this is an HTMX request
        if request.headers.get('HX-Request'):
            # Return just the success message for HTMX
            return render(request, 'core/partials/contact_success.html')
        else:
            # Add a success message for traditional form submission
            messages.success(request, 'Your message has been sent. We will get back to you soon!')

    return render(request, 'core/contact.html')

@login_required
def dashboard(_):
    """
    Dashboard view (requires login)
    Redirects to the new dashboard app
    """
    return redirect('dashboard:user_dashboard')
