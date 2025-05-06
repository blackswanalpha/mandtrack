"""
PDF generation utilities using WeasyPrint.
"""
import os
import logging
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone

# Import WeasyPrint if available
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

logger = logging.getLogger(__name__)


def generate_pdf_from_template(template_path, context, filename=None):
    """
    Generate a PDF from a template.
    
    Args:
        template_path (str): Path to the template file
        context (dict): Context data for the template
        filename (str, optional): Filename for the PDF. Defaults to None.
        
    Returns:
        HttpResponse: PDF response
    """
    if not WEASYPRINT_AVAILABLE:
        logger.error("WeasyPrint is not installed. Cannot generate PDF.")
        return HttpResponse("PDF generation is not available. WeasyPrint is not installed.", 
                           content_type="text/plain", status=500)
    
    # Add current date/time to context if not present
    if 'now' not in context:
        context['now'] = timezone.now()
    
    # Render the template to HTML
    html_string = render_to_string(template_path, context)
    
    # Create a PDF from the HTML
    html = HTML(string=html_string, base_url=settings.BASE_DIR)
    
    # Load default CSS
    css_files = [
        os.path.join(settings.STATIC_ROOT, 'css', 'pdf_base.css'),
    ]
    
    css_list = []
    for css_file in css_files:
        if os.path.exists(css_file):
            css_list.append(CSS(filename=css_file))
    
    # Generate PDF
    pdf = html.write_pdf(stylesheets=css_list)
    
    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    
    # Set filename
    if filename:
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    else:
        response['Content-Disposition'] = 'attachment; filename="document.pdf"'
    
    return response


def generate_pdf_from_html(html_string, filename=None, css_files=None):
    """
    Generate a PDF from an HTML string.
    
    Args:
        html_string (str): HTML content
        filename (str, optional): Filename for the PDF. Defaults to None.
        css_files (list, optional): List of CSS files to include. Defaults to None.
        
    Returns:
        HttpResponse: PDF response
    """
    if not WEASYPRINT_AVAILABLE:
        logger.error("WeasyPrint is not installed. Cannot generate PDF.")
        return HttpResponse("PDF generation is not available. WeasyPrint is not installed.", 
                           content_type="text/plain", status=500)
    
    # Create a PDF from the HTML
    html = HTML(string=html_string, base_url=settings.BASE_DIR)
    
    # Load CSS files
    css_list = []
    
    # Add default CSS
    default_css = os.path.join(settings.STATIC_ROOT, 'css', 'pdf_base.css')
    if os.path.exists(default_css):
        css_list.append(CSS(filename=default_css))
    
    # Add custom CSS files
    if css_files:
        for css_file in css_files:
            if os.path.exists(css_file):
                css_list.append(CSS(filename=css_file))
    
    # Generate PDF
    pdf = html.write_pdf(stylesheets=css_list)
    
    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    
    # Set filename
    if filename:
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    else:
        response['Content-Disposition'] = 'attachment; filename="document.pdf"'
    
    return response
