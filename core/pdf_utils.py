"""
PDF generation utilities for MindTrack.

This module provides utilities for generating PDF reports using WeasyPrint.
"""
import os
import tempfile
from datetime import datetime
from django.template.loader import render_to_string
from django.conf import settings
from django.http import HttpResponse
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration


class PDFGenerator:
    """
    PDF Generator for MindTrack reports.
    """
    def __init__(self, base_url=None):
        """
        Initialize the PDF generator.
        
        Args:
            base_url (str, optional): Base URL for resolving relative URLs in the HTML.
        """
        self.base_url = base_url or settings.SITE_URL
        self.font_config = FontConfiguration()
        self.default_css = CSS(string='''
            @page {
                size: A4;
                margin: 1cm;
                @top-right {
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 9pt;
                    color: #666;
                }
                @top-left {
                    content: "MindTrack Report";
                    font-size: 9pt;
                    color: #666;
                }
                @bottom-left {
                    content: "Generated on %s";
                    font-size: 9pt;
                    color: #666;
                }
                @bottom-right {
                    content: "© MindTrack";
                    font-size: 9pt;
                    color: #666;
                }
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.5;
                color: #333;
            }
            h1, h2, h3, h4, h5, h6 {
                font-weight: 600;
                margin-top: 1em;
                margin-bottom: 0.5em;
                color: #1f2937;
            }
            h1 {
                font-size: 24pt;
                border-bottom: 1px solid #e5e7eb;
                padding-bottom: 0.3em;
            }
            h2 {
                font-size: 18pt;
            }
            h3 {
                font-size: 14pt;
            }
            p {
                margin-top: 0.5em;
                margin-bottom: 0.5em;
            }
            table {
                width: 100%%;
                border-collapse: collapse;
                margin-top: 1em;
                margin-bottom: 1em;
            }
            th, td {
                padding: 0.5em;
                border: 1px solid #e5e7eb;
                text-align: left;
            }
            th {
                background-color: #f9fafb;
                font-weight: 600;
            }
            .header {
                text-align: center;
                margin-bottom: 2em;
            }
            .header img {
                max-width: 200px;
                margin-bottom: 1em;
            }
            .footer {
                margin-top: 2em;
                padding-top: 1em;
                border-top: 1px solid #e5e7eb;
                font-size: 9pt;
                color: #666;
                text-align: center;
            }
            .page-break {
                page-break-after: always;
            }
            .chart-container {
                margin: 1em 0;
                text-align: center;
            }
            .chart-container img {
                max-width: 100%%;
                height: auto;
            }
            .info-box {
                background-color: #f3f4f6;
                border-left: 4px solid #3b82f6;
                padding: 1em;
                margin: 1em 0;
            }
            .warning-box {
                background-color: #fef3c7;
                border-left: 4px solid #f59e0b;
                padding: 1em;
                margin: 1em 0;
            }
            .success-box {
                background-color: #d1fae5;
                border-left: 4px solid #10b981;
                padding: 1em;
                margin: 1em 0;
            }
            .error-box {
                background-color: #fee2e2;
                border-left: 4px solid #ef4444;
                padding: 1em;
                margin: 1em 0;
            }
            .score-container {
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 1em 0;
            }
            .score-circle {
                width: 100px;
                height: 100px;
                border-radius: 50%%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24pt;
                font-weight: bold;
                color: white;
            }
            .score-high {
                background-color: #10b981;
            }
            .score-medium {
                background-color: #f59e0b;
            }
            .score-low {
                background-color: #ef4444;
            }
            .two-column {
                column-count: 2;
                column-gap: 2em;
            }
        ''' % datetime.now().strftime('%Y-%m-%d %H:%M'))
    
    def generate_pdf_from_template(self, template_name, context, filename=None, extra_css=None):
        """
        Generate a PDF from a Django template.
        
        Args:
            template_name (str): Name of the template to render
            context (dict): Context data for the template
            filename (str, optional): Filename for the PDF
            extra_css (str or CSS, optional): Additional CSS to apply
        
        Returns:
            HttpResponse: PDF response
        """
        # Render the template to HTML
        html_string = render_to_string(template_name, context)
        
        # Create a temporary file to store the HTML
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
            tmp.write(html_string.encode('utf-8'))
            tmp_path = tmp.name
        
        try:
            # Generate the PDF
            html = HTML(filename=tmp_path, base_url=self.base_url)
            
            # Prepare CSS
            stylesheets = [self.default_css]
            if extra_css:
                if isinstance(extra_css, str):
                    stylesheets.append(CSS(string=extra_css))
                else:
                    stylesheets.append(extra_css)
            
            # Render the PDF
            pdf = html.write_pdf(
                stylesheets=stylesheets,
                font_config=self.font_config
            )
            
            # Create the HTTP response
            response = HttpResponse(pdf, content_type='application/pdf')
            
            # Set the filename
            if filename:
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
        finally:
            # Clean up the temporary file
            os.unlink(tmp_path)
    
    def generate_pdf_from_string(self, html_string, filename=None, extra_css=None):
        """
        Generate a PDF from an HTML string.
        
        Args:
            html_string (str): HTML content
            filename (str, optional): Filename for the PDF
            extra_css (str or CSS, optional): Additional CSS to apply
        
        Returns:
            HttpResponse: PDF response
        """
        # Create a temporary file to store the HTML
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
            tmp.write(html_string.encode('utf-8'))
            tmp_path = tmp.name
        
        try:
            # Generate the PDF
            html = HTML(filename=tmp_path, base_url=self.base_url)
            
            # Prepare CSS
            stylesheets = [self.default_css]
            if extra_css:
                if isinstance(extra_css, str):
                    stylesheets.append(CSS(string=extra_css))
                else:
                    stylesheets.append(extra_css)
            
            # Render the PDF
            pdf = html.write_pdf(
                stylesheets=stylesheets,
                font_config=self.font_config
            )
            
            # Create the HTTP response
            response = HttpResponse(pdf, content_type='application/pdf')
            
            # Set the filename
            if filename:
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
        finally:
            # Clean up the temporary file
            os.unlink(tmp_path)


# Create a global instance
pdf_generator = PDFGenerator()
