"""
PDF generation utilities for assessments
"""
from django.template.loader import render_to_string
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

# Check if WeasyPrint is available
try:
    from weasyprint import HTML, CSS
    from weasyprint.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("WeasyPrint is not installed. PDF generation will not be available.")

def generate_assessment_pdf(assessment, filename=None):
    """
    Generate a PDF report for an assessment

    Args:
        assessment: Assessment object
        filename: Optional filename for the PDF

    Returns:
        HttpResponse with PDF content
    """
    if not WEASYPRINT_AVAILABLE:
        logger.error("WeasyPrint is not installed. Cannot generate PDF.")
        return HttpResponse("PDF generation is not available. WeasyPrint is not installed.",
                           content_type="text/plain", status=500)

    # Prepare context for template
    context = {
        'assessment': assessment,
        'response': assessment.response,
        'patient_id': assessment.response.patient_identifier or 'Anonymous',
        'risk_level': assessment.get_risk_level(),
        'assessment_date': assessment.assessment_date,
        'consultation_status': assessment.get_consultation_recommended_display(),
        'consultation_urgency': assessment.consultation_urgency,
        'assessor': assessment.assessor.get_full_name() if assessment.assessor else 'System',
        'generated_at': timezone.now(),
        'logo_path': os.path.join(settings.STATIC_ROOT, 'img/logo.png'),
    }

    # Render HTML template
    html_string = render_to_string('assessments/pdf/assessment_report.html', context)

    # Configure fonts
    font_config = FontConfiguration()

    # Create temporary file for PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        # Generate PDF
        HTML(string=html_string).write_pdf(
            tmp.name,
            font_config=font_config,
            stylesheets=[
                CSS(string='''
                    @page {
                        size: letter;
                        margin: 1.5cm;
                        @top-center {
                            content: "Patient Assessment Report";
                            font-size: 9pt;
                            color: #666;
                        }
                        @bottom-center {
                            content: "Page " counter(page) " of " counter(pages);
                            font-size: 9pt;
                            color: #666;
                        }
                    }
                    body {
                        font-family: Arial, sans-serif;
                        font-size: 10pt;
                        line-height: 1.5;
                        color: #333;
                    }
                    h1 {
                        font-size: 16pt;
                        color: #2196F3;
                        margin-bottom: 10px;
                    }
                    h2 {
                        font-size: 14pt;
                        color: #333;
                        margin-top: 20px;
                        margin-bottom: 10px;
                        border-bottom: 1px solid #eee;
                        padding-bottom: 5px;
                    }
                    h3 {
                        font-size: 12pt;
                        color: #555;
                        margin-top: 15px;
                        margin-bottom: 5px;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 15px;
                    }
                    th, td {
                        padding: 8px;
                        border: 1px solid #ddd;
                        text-align: left;
                    }
                    th {
                        background-color: #f5f5f5;
                        font-weight: bold;
                    }
                    .header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 20px;
                    }
                    .logo {
                        max-width: 150px;
                        max-height: 50px;
                    }
                    .risk-badge {
                        display: inline-block;
                        padding: 3px 8px;
                        border-radius: 12px;
                        font-size: 9pt;
                        font-weight: bold;
                    }
                    .risk-low {
                        background-color: #d1fae5;
                        color: #065f46;
                    }
                    .risk-medium {
                        background-color: #fef3c7;
                        color: #92400e;
                    }
                    .risk-high {
                        background-color: #fee2e2;
                        color: #b91c1c;
                    }
                    .risk-critical {
                        background-color: #7f1d1d;
                        color: #fee2e2;
                    }
                    .metadata-table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    .metadata-table td {
                        padding: 3px;
                    }
                    .metadata-label {
                        font-weight: bold;
                        width: 150px;
                    }
                    .section {
                        margin-bottom: 20px;
                        padding: 15px;
                        border: 1px solid #eee;
                        border-radius: 5px;
                        background-color: #f9f9f9;
                    }
                    .consultation-badge {
                        display: inline-block;
                        padding: 3px 8px;
                        border-radius: 12px;
                        font-size: 9pt;
                        font-weight: bold;
                    }
                    .consultation-not_required {
                        background-color: #e5e7eb;
                        color: #374151;
                    }
                    .consultation-recommended {
                        background-color: #dbeafe;
                        color: #1e40af;
                    }
                    .consultation-required {
                        background-color: #fef3c7;
                        color: #92400e;
                    }
                    .consultation-scheduled {
                        background-color: #e0e7ff;
                        color: #3730a3;
                    }
                    .consultation-completed {
                        background-color: #d1fae5;
                        color: #065f46;
                    }
                ''')
            ]
        )

        # Read the generated PDF
        tmp.seek(0)
        pdf_data = tmp.read()

    # Clean up temporary file
    os.unlink(tmp.name)

    # Create response
    response = HttpResponse(pdf_data, content_type='application/pdf')

    # Set filename
    if filename:
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    else:
        patient_id = assessment.response.patient_identifier or 'anonymous'
        date_str = assessment.assessment_date.strftime('%Y%m%d')
        response['Content-Disposition'] = f'attachment; filename="assessment_{patient_id}_{date_str}.pdf"'

    return response
