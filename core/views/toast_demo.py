"""
Views for demonstrating the toast notification system.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def toast_demo(request):
    """
    Demonstrate the toast notification system
    """
    return render(request, 'core/toast_demo.html')

@login_required
def enhanced_toast_demo(request):
    """
    Demonstrate the enhanced toast notification system
    """
    return render(request, 'core/toast_demo_enhanced.html')

@login_required
def show_toast(request, toast_type):
    """
    Show a toast notification of the specified type
    """
    if toast_type == 'success':
        messages.success(request, 'This is a success toast notification!')
    elif toast_type == 'error':
        messages.error(request, 'This is an error toast notification!')
    elif toast_type == 'warning':
        messages.warning(request, 'This is a warning toast notification!')
    else:
        messages.info(request, 'This is an info toast notification!')

    return redirect('core:toast_demo')
