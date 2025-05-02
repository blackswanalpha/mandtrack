"""
Utility functions for generating PDF reports.
"""
import os
import tempfile
from datetime import datetime
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import base64
import logging

# Set up logger
logger = logging.getLogger(__name__)

def generate_clinical_report_pdf(report_data, response_data, questionnaire_data, user_data=None):
    """
    Generate a PDF clinical report based on the provided data.

    Args:
        report_data: Dictionary containing the report content
        response_data: Dictionary containing response information
        questionnaire_data: Dictionary containing questionnaire information
        user_data: Optional dictionary containing user information

    Returns:
        BytesIO object containing the PDF data
    """
    try:
        # Prepare context for template
        context = {
            'report': report_data,
            'response': response_data,
            'questionnaire': questionnaire_data,
            'user': user_data,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'logo_path': os.path.join(settings.STATIC_ROOT, 'img/logo.png'),
        }

        # Render HTML template
        html_string = render_to_string('analytics/pdf/clinical_report.html', context)

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
                            margin: 2cm;
                            @top-center {
                                content: "Clinical Report";
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
                            font-size: 11pt;
                            line-height: 1.5;
                            color: #333;
                        }
                        h1 {
                            font-size: 18pt;
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
                        .header {
                            text-align: center;
                            margin-bottom: 20px;
                        }
                        .logo {
                            max-height: 50px;
                            margin-bottom: 10px;
                        }
                        .patient-info {
                            background-color: #f8f9fa;
                            padding: 10px;
                            border-radius: 5px;
                            margin-bottom: 20px;
                        }
                        .patient-info-table {
                            width: 100%;
                            border-collapse: collapse;
                        }
                        .patient-info-table td {
                            padding: 5px;
                        }
                        .patient-info-label {
                            font-weight: bold;
                            width: 150px;
                        }
                        .section {
                            margin-bottom: 20px;
                        }
                        .risk-low {
                            color: #4CAF50;
                        }
                        .risk-medium {
                            color: #FFC107;
                        }
                        .risk-high {
                            color: #F44336;
                        }
                        .risk-critical {
                            color: #9C27B0;
                        }
                        .footer {
                            text-align: center;
                            font-size: 9pt;
                            color: #666;
                            margin-top: 30px;
                            padding-top: 10px;
                            border-top: 1px solid #eee;
                        }
                        .metadata {
                            font-size: 9pt;
                            color: #666;
                            margin-top: 30px;
                            padding-top: 10px;
                            border-top: 1px solid #eee;
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
                    ''')
                ]
            )

            # Read the generated PDF
            tmp.seek(0)
            pdf_data = tmp.read()

        # Clean up temporary file
        os.unlink(tmp.name)

        return pdf_data

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise

def generate_dashboard_report_pdf(questionnaire_data, stats_data, charts_data):
    """
    Generate a PDF dashboard report based on the provided data.

    Args:
        questionnaire_data: Dictionary containing questionnaire information
        stats_data: Dictionary containing statistics
        charts_data: Dictionary containing base64-encoded chart images

    Returns:
        BytesIO object containing the PDF data
    """
    try:
        # Prepare context for template
        context = {
            'questionnaire': questionnaire_data,
            'stats': stats_data,
            'charts': charts_data,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'logo_path': os.path.join(settings.STATIC_ROOT, 'img/logo.png'),
        }

        # Render HTML template
        html_string = render_to_string('analytics/pdf/dashboard_report.html', context)

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
                            size: letter landscape;
                            margin: 1.5cm;
                            @top-center {
                                content: "Dashboard Report - ''' + questionnaire_data.get('title', 'Questionnaire') + '''";
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
                            color: #333;
                            margin-top: 15px;
                            margin-bottom: 8px;
                        }
                        .header {
                            text-align: center;
                            margin-bottom: 20px;
                        }
                        .logo {
                            max-height: 40px;
                            margin-bottom: 10px;
                        }
                        .stats-container {
                            display: flex;
                            flex-wrap: wrap;
                            margin-bottom: 20px;
                        }
                        .stat-card {
                            width: 23%;
                            margin-right: 2%;
                            background-color: #f8f9fa;
                            padding: 10px;
                            border-radius: 5px;
                            margin-bottom: 10px;
                            text-align: center;
                        }
                        .stat-value {
                            font-size: 18pt;
                            font-weight: bold;
                            color: #2196F3;
                        }
                        .stat-label {
                            font-size: 9pt;
                            color: #666;
                        }
                        .chart-container {
                            margin-bottom: 20px;
                            page-break-inside: avoid;
                        }
                        .chart-title {
                            font-size: 12pt;
                            font-weight: bold;
                            margin-bottom: 5px;
                        }
                        .chart-description {
                            font-size: 9pt;
                            color: #666;
                            margin-bottom: 10px;
                        }
                        .chart-img {
                            max-width: 100%;
                            height: auto;
                        }
                        .footer {
                            text-align: center;
                            font-size: 9pt;
                            color: #666;
                            margin-top: 30px;
                            padding-top: 10px;
                            border-top: 1px solid #eee;
                        }
                        .two-column {
                            display: flex;
                            flex-wrap: wrap;
                        }
                        .column {
                            width: 48%;
                            margin-right: 2%;
                        }
                    ''')
                ]
            )

            # Read the generated PDF
            tmp.seek(0)
            pdf_data = tmp.read()

        # Clean up temporary file
        os.unlink(tmp.name)

        return pdf_data

    except Exception as e:
        logger.error(f"Error generating dashboard PDF: {str(e)}")
        raise

def generate_comparative_report_pdf(title, description, comparison_data, charts_data):
    """
    Generate a PDF comparative analysis report.

    Args:
        title: Report title
        description: Report description
        comparison_data: Dictionary containing comparison data
        charts_data: Dictionary containing base64-encoded chart images

    Returns:
        BytesIO object containing the PDF data
    """
    try:
        # Prepare context for template
        context = {
            'title': title,
            'description': description,
            'comparison_data': comparison_data,
            'charts': charts_data,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'logo_path': os.path.join(settings.STATIC_ROOT, 'img/logo.png'),
        }

        # Render HTML template
        html_string = render_to_string('analytics/pdf/comparative_report.html', context)

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
                            size: letter landscape;
                            margin: 1.5cm;
                            @top-center {
                                content: "Comparative Analysis Report";
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
                            color: #333;
                            margin-top: 15px;
                            margin-bottom: 8px;
                        }
                        .header {
                            text-align: center;
                            margin-bottom: 20px;
                        }
                        .logo {
                            max-height: 40px;
                            margin-bottom: 10px;
                        }
                        .chart-container {
                            margin-bottom: 20px;
                            page-break-inside: avoid;
                        }
                        .chart-title {
                            font-size: 12pt;
                            font-weight: bold;
                            margin-bottom: 5px;
                        }
                        .chart-description {
                            font-size: 9pt;
                            color: #666;
                            margin-bottom: 10px;
                        }
                        .chart-img {
                            max-width: 100%;
                            height: auto;
                        }
                        .footer {
                            text-align: center;
                            font-size: 9pt;
                            color: #666;
                            margin-top: 30px;
                            padding-top: 10px;
                            border-top: 1px solid #eee;
                        }
                        .comparison-table {
                            width: 100%;
                            border-collapse: collapse;
                            margin-bottom: 20px;
                        }
                        .comparison-table th {
                            background-color: #f0f0f0;
                            padding: 8px;
                            text-align: left;
                            font-weight: bold;
                            border: 1px solid #ddd;
                        }
                        .comparison-table td {
                            padding: 8px;
                            border: 1px solid #ddd;
                        }
                        .comparison-table tr:nth-child(even) {
                            background-color: #f8f8f8;
                        }
                    ''')
                ]
            )

            # Read the generated PDF
            tmp.seek(0)
            pdf_data = tmp.read()

        # Clean up temporary file
        os.unlink(tmp.name)

        return pdf_data

    except Exception as e:
        logger.error(f"Error generating comparative PDF: {str(e)}")
        raise

def generate_batch_report_pdf(grouped_responses):
    """
    Generate a PDF batch report

    Args:
        grouped_responses: Dictionary mapping questionnaires to lists of responses

    Returns:
        BytesIO object containing the PDF data
    """
    try:
        # Prepare context for template
        context = {
            'grouped_responses': grouped_responses,
            'questionnaire_count': len(grouped_responses),
            'response_count': sum(len(responses) for responses in grouped_responses.values()),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'logo_path': os.path.join(settings.STATIC_ROOT, 'img/logo.png'),
        }

        # Render HTML template
        html_string = render_to_string('analytics/pdf/batch_report.html', context)

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
                                content: "Batch Report";
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
                            color: #333;
                            margin-top: 15px;
                            margin-bottom: 8px;
                        }
                        .header {
                            text-align: center;
                            margin-bottom: 20px;
                        }
                        .logo {
                            max-height: 40px;
                            margin-bottom: 10px;
                        }
                        .questionnaire-section {
                            margin-bottom: 30px;
                            page-break-inside: avoid;
                        }
                        .questionnaire-title {
                            font-size: 14pt;
                            font-weight: bold;
                            color: #333;
                            margin-bottom: 10px;
                            padding-bottom: 5px;
                            border-bottom: 1px solid #eee;
                        }
                        .response-table {
                            width: 100%;
                            border-collapse: collapse;
                            margin-bottom: 20px;
                        }
                        .response-table th {
                            background-color: #f0f0f0;
                            padding: 8px;
                            text-align: left;
                            font-weight: bold;
                            border: 1px solid #ddd;
                        }
                        .response-table td {
                            padding: 8px;
                            border: 1px solid #ddd;
                        }
                        .response-table tr:nth-child(even) {
                            background-color: #f8f8f8;
                        }
                        .footer {
                            text-align: center;
                            font-size: 9pt;
                            color: #666;
                            margin-top: 30px;
                            padding-top: 10px;
                            border-top: 1px solid #eee;
                        }
                        .summary-section {
                            margin-bottom: 20px;
                        }
                        .summary-table {
                            width: 100%;
                            border-collapse: collapse;
                            margin-bottom: 20px;
                        }
                        .summary-table th {
                            background-color: #f0f0f0;
                            padding: 8px;
                            text-align: left;
                            font-weight: bold;
                            border: 1px solid #ddd;
                        }
                        .summary-table td {
                            padding: 8px;
                            border: 1px solid #ddd;
                        }
                        .summary-table tr:nth-child(even) {
                            background-color: #f8f8f8;
                        }
                    ''')
                ]
            )

            # Read the generated PDF
            tmp.seek(0)
            pdf_data = tmp.read()

        # Clean up temporary file
        os.unlink(tmp.name)

        return pdf_data

    except Exception as e:
        logger.error(f"Error generating batch report PDF: {str(e)}")
        raise
