from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Avg
from django.utils import timezone
from django.conf import settings

import os
import csv
import json
import tempfile
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

from surveys.models import Questionnaire
from feedback.models import Response, Answer
from groups.models import Organization
from analytics.models.reports import Report, ReportSchedule

@login_required
def report_dashboard(request):
    """
    Display the reports dashboard
    """
    # Get recent reports for this user
    reports = Report.objects.filter(created_by=request.user).order_by('-created_at')[:5]

    context = {
        'reports': reports,
    }

    return render(request, 'analytics/reports/report_dashboard.html', context)

@login_required
def report_list(request):
    """
    Display a list of all reports
    """
    # Get all reports for this user
    reports = Report.objects.filter(created_by=request.user).order_by('-created_at')

    # Apply filters if provided
    report_type = request.GET.get('type')
    if report_type:
        reports = reports.filter(report_type=report_type)

    status = request.GET.get('status')
    if status:
        reports = reports.filter(status=status)

    # Search by title or description
    search = request.GET.get('search')
    if search:
        reports = reports.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    # Paginate the results
    page = request.GET.get('page', 1)
    paginator = Paginator(reports, 10)

    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)

    context = {
        'reports': reports,
        'report_types': Report.REPORT_TYPE_CHOICES,
        'status_choices': Report.STATUS_CHOICES,
    }

    return render(request, 'analytics/reports/report_list.html', context)

@login_required
def report_detail(request, pk):
    """
    Display details of a report
    """
    report = get_object_or_404(Report, pk=pk)

    # Check if user has permission to view this report
    if report.created_by != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to view this report.")
        return redirect('analytics:report_list')

    context = {
        'report': report,
    }

    return render(request, 'analytics/reports/report_detail.html', context)

@login_required
def report_delete(request, pk):
    """
    Delete a report
    """
    report = get_object_or_404(Report, pk=pk)

    # Check if user has permission to delete this report
    if report.created_by != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to delete this report.")
        return redirect('analytics:report_detail', pk=pk)

    if request.method == 'POST':
        # Delete the report file if it exists
        if report.file:
            if os.path.isfile(report.file.path):
                os.remove(report.file.path)

        # Delete the report
        report.delete()

        messages.success(request, "Report deleted successfully.")
        return redirect('analytics:report_list')

    context = {
        'report': report,
    }

    return render(request, 'analytics/reports/report_confirm_delete.html', context)

@login_required
def report_response_summary(request):
    """
    Generate a response summary report
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        questionnaire_id = request.POST.get('questionnaire')
        report_format = request.POST.get('report_format')
        date_range = request.POST.get('date_range')

        if not title or not questionnaire_id or not report_format:
            messages.error(request, "Title, questionnaire, and report format are required.")
            return redirect('analytics:report_response_summary')

        questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)

        # Check if user has permission to view this questionnaire
        if not request.user.is_staff and questionnaire.created_by != request.user:
            if questionnaire.organization:
                # Check if user is a member of the organization
                if not questionnaire.organization.members.filter(user=request.user, is_active=True).exists():
                    messages.error(request, "You don't have permission to generate reports for this questionnaire.")
                    return redirect('analytics:report_response_summary')
            else:
                messages.error(request, "You don't have permission to generate reports for this questionnaire.")
                return redirect('analytics:report_response_summary')

        # Parse date range
        start_date = None
        end_date = None

        if date_range == 'last_7_days':
            end_date = timezone.now()
            start_date = end_date - timedelta(days=7)
        elif date_range == 'last_30_days':
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
        elif date_range == 'last_90_days':
            end_date = timezone.now()
            start_date = end_date - timedelta(days=90)
        elif date_range == 'custom':
            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')

            if start_date_str and end_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                except ValueError:
                    messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
                    return redirect('analytics:report_response_summary')

        # Create the report
        report = Report.objects.create(
            title=title,
            description=description,
            report_type='response_summary',
            report_format=report_format,
            parameters={
                'questionnaire_id': questionnaire_id,
                'date_range': date_range,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
            },
            questionnaire=questionnaire,
            organization=questionnaire.organization,
            created_by=request.user,
            status='processing'
        )

        # Generate the report (in a real application, this would be done asynchronously)
        try:
            # Get responses for this questionnaire
            responses_query = Response.objects.filter(questionnaire=questionnaire)

            # Apply date filters if provided
            if start_date and end_date:
                responses_query = responses_query.filter(created_at__gte=start_date, created_at__lte=end_date)

            responses = responses_query.all()

            # Generate the report based on the format
            if report_format == 'pdf':
                # This would typically use a PDF generation library like ReportLab or WeasyPrint
                # For now, we'll just create a placeholder file
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(b'PDF Report Placeholder')
                    temp_file_path = temp_file.name

                # Save the file to the report
                with open(temp_file_path, 'rb') as f:
                    report.file.save(f'response_summary_{report.id}.pdf', f)

                # Clean up the temporary file
                os.remove(temp_file_path)

            elif report_format == 'csv':
                # Create a CSV file
                with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
                    writer = csv.writer(temp_file)

                    # Write header
                    writer.writerow(['Response ID', 'Created At', 'Completed At', 'Email', 'Gender', 'Age', 'Completion Status'])

                    # Write data
                    for response in responses:
                        writer.writerow([
                            str(response.id),
                            response.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                            response.completed_at.strftime('%Y-%m-%d %H:%M:%S') if response.completed_at else 'Not completed',
                            response.email or 'N/A',
                            response.gender or 'N/A',
                            response.age or 'N/A',
                            'Completed' if response.completed_at else 'In Progress'
                        ])

                    temp_file_path = temp_file.name

                # Save the file to the report
                with open(temp_file_path, 'rb') as f:
                    report.file.save(f'response_summary_{report.id}.csv', f)

                # Clean up the temporary file
                os.remove(temp_file_path)

            elif report_format == 'excel':
                # Create an Excel file using pandas
                df = pd.DataFrame([
                    {
                        'Response ID': str(response.id),
                        'Created At': response.created_at,
                        'Completed At': response.completed_at or 'Not completed',
                        'Email': response.email or 'N/A',
                        'Gender': response.gender or 'N/A',
                        'Age': response.age or 'N/A',
                        'Completion Status': 'Completed' if response.completed_at else 'In Progress'
                    }
                    for response in responses
                ])

                with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
                    df.to_excel(temp_file.name, index=False)
                    temp_file_path = temp_file.name

                # Save the file to the report
                with open(temp_file_path, 'rb') as f:
                    report.file.save(f'response_summary_{report.id}.xlsx', f)

                # Clean up the temporary file
                os.remove(temp_file_path)

            elif report_format == 'json':
                # Create a JSON file
                data = [
                    {
                        'response_id': str(response.id),
                        'created_at': response.created_at.isoformat(),
                        'completed_at': response.completed_at.isoformat() if response.completed_at else None,
                        'email': response.email,
                        'gender': response.gender,
                        'age': response.age,
                        'completion_status': 'Completed' if response.completed_at else 'In Progress'
                    }
                    for response in responses
                ]

                with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
                    json.dump(data, temp_file, indent=2)
                    temp_file_path = temp_file.name

                # Save the file to the report
                with open(temp_file_path, 'rb') as f:
                    report.file.save(f'response_summary_{report.id}.json', f)

                # Clean up the temporary file
                os.remove(temp_file_path)

            elif report_format == 'html':
                # Create an HTML file
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Response Summary - {questionnaire.title}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        h1 {{ color: #333; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                        tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    </style>
                </head>
                <body>
                    <h1>Response Summary - {questionnaire.title}</h1>
                    <p>Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Total Responses: {responses.count()}</p>

                    <h2>Responses</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Response ID</th>
                                <th>Created At</th>
                                <th>Completed At</th>
                                <th>Email</th>
                                <th>Gender</th>
                                <th>Age</th>
                                <th>Completion Status</th>
                            </tr>
                        </thead>
                        <tbody>
                """

                for response in responses:
                    html_content += f"""
                            <tr>
                                <td>{response.id}</td>
                                <td>{response.created_at.strftime('%Y-%m-%d %H:%M:%S')}</td>
                                <td>{response.completed_at.strftime('%Y-%m-%d %H:%M:%S') if response.completed_at else 'Not completed'}</td>
                                <td>{response.email or 'N/A'}</td>
                                <td>{response.gender or 'N/A'}</td>
                                <td>{response.age or 'N/A'}</td>
                                <td>{'Completed' if response.completed_at else 'In Progress'}</td>
                            </tr>
                    """

                html_content += """
                        </tbody>
                    </table>
                </body>
                </html>
                """

                with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
                    temp_file.write(html_content.encode('utf-8'))
                    temp_file_path = temp_file.name

                # Save the file to the report
                with open(temp_file_path, 'rb') as f:
                    report.file.save(f'response_summary_{report.id}.html', f)

                # Clean up the temporary file
                os.remove(temp_file_path)

            # Mark the report as completed
            report.mark_as_completed()

            messages.success(request, "Report generated successfully.")
            return redirect('analytics:report_detail', pk=report.id)

        except Exception as e:
            # Mark the report as failed
            report.mark_as_failed(str(e))

            messages.error(request, f"Error generating report: {str(e)}")
            return redirect('analytics:report_response_summary')

    # Get all questionnaires the user has access to
    if request.user.is_staff:
        questionnaires = Questionnaire.objects.all()
    else:
        # Get questionnaires created by the user
        user_questionnaires = Questionnaire.objects.filter(created_by=request.user)

        # Get questionnaires from organizations the user is a member of
        org_memberships = request.user.organization_memberships.filter(is_active=True)
        org_ids = [membership.organization_id for membership in org_memberships]
        org_questionnaires = Questionnaire.objects.filter(organization__in=org_ids)

        # Combine the querysets
        questionnaires = user_questionnaires | org_questionnaires

    context = {
        'questionnaires': questionnaires,
        'report_formats': Report.REPORT_FORMAT_CHOICES,
    }

    return render(request, 'analytics/reports/report_response_summary_form.html', context)

@login_required
def report_trend_analysis(request):
    """
    Generate a trend analysis report
    """
    # Similar to report_response_summary, but for trend analysis
    # This would be implemented with time-series analysis

    context = {
        'questionnaires': Questionnaire.objects.all(),
        'report_formats': Report.REPORT_FORMAT_CHOICES,
    }

    return render(request, 'analytics/reports/report_trend_analysis_form.html', context)

@login_required
def report_ai_insights(request):
    """
    Generate an AI insights report
    """
    # This would be implemented with AI analysis

    context = {
        'questionnaires': Questionnaire.objects.all(),
        'report_formats': Report.REPORT_FORMAT_CHOICES,
    }

    return render(request, 'analytics/reports/report_ai_insights_form.html', context)

@login_required
def report_demographic_analysis(request):
    """
    Generate a demographic analysis report
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        questionnaire_id = request.POST.get('questionnaire')
        demographic_type = request.POST.get('demographic_type', 'age')
        report_format = request.POST.get('report_format')
        date_range = request.POST.get('date_range')

        if not title or not questionnaire_id or not report_format:
            messages.error(request, "Title, questionnaire, and report format are required.")
            return redirect('analytics:report_demographic_analysis')

        questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)

        # Check if user has permission to view this questionnaire
        if not request.user.is_staff and questionnaire.created_by != request.user:
            if questionnaire.organization:
                # Check if user is a member of the organization
                if not questionnaire.organization.members.filter(user=request.user, is_active=True).exists():
                    messages.error(request, "You don't have permission to generate reports for this questionnaire.")
                    return redirect('analytics:report_demographic_analysis')
            else:
                messages.error(request, "You don't have permission to generate reports for this questionnaire.")
                return redirect('analytics:report_demographic_analysis')

        # Parse date range
        start_date = None
        end_date = None

        if date_range == 'last_7_days':
            end_date = timezone.now()
            start_date = end_date - timedelta(days=7)
        elif date_range == 'last_30_days':
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
        elif date_range == 'last_90_days':
            end_date = timezone.now()
            start_date = end_date - timedelta(days=90)
        elif date_range == 'custom':
            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')

            if start_date_str and end_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                except ValueError:
                    messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
                    return redirect('analytics:report_demographic_analysis')

        # Create the report
        report = Report.objects.create(
            title=title,
            description=description,
            report_type='demographic_analysis',
            report_format=report_format,
            parameters={
                'questionnaire_id': questionnaire_id,
                'demographic_type': demographic_type,
                'date_range': date_range,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
            },
            questionnaire=questionnaire,
            organization=questionnaire.organization,
            created_by=request.user,
            status='processing'
        )

        # Generate the report (in a real application, this would be done asynchronously)
        try:
            # Get responses for this questionnaire
            responses_query = Response.objects.filter(survey=questionnaire)

            # Apply date filters if provided
            if start_date and end_date:
                responses_query = responses_query.filter(created_at__gte=start_date, created_at__lte=end_date)

            responses = responses_query.all()

            # Generate demographic analysis based on the type
            if demographic_type == 'age':
                # Define age groups
                age_groups = {
                    '18-25': (18, 25),
                    '26-35': (26, 35),
                    '36-45': (36, 45),
                    '46-55': (46, 55),
                    '56+': (56, 120)
                }

                # Calculate statistics for each age group
                age_stats = {}
                for group_name, (min_age, max_age) in age_groups.items():
                    group_responses = responses.filter(
                        patient_age__gte=min_age,
                        patient_age__lte=max_age
                    )
                    age_stats[group_name] = {
                        'count': group_responses.count(),
                        'avg_score': group_responses.exclude(score__isnull=True).aggregate(Avg('score'))['score__avg'] or 0,
                        'completion_rate': (group_responses.filter(status='completed').count() / group_responses.count() * 100) if group_responses.count() > 0 else 0
                    }

                # Generate age distribution chart
                plt.figure(figsize=(10, 6))
                groups = list(age_stats.keys())
                counts = [age_stats[group]['count'] for group in groups]

                plt.bar(groups, counts)
                plt.title('Response Distribution by Age Group')
                plt.xlabel('Age Group')
                plt.ylabel('Number of Responses')
                plt.grid(axis='y', alpha=0.3)

                # Save chart to buffer
                buffer = BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                chart_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()

                # Generate report content based on format
                if report_format == 'pdf':
                    # This would typically use a PDF generation library like ReportLab or WeasyPrint
                    # For now, we'll just create a placeholder file
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                        temp_file.write(b'PDF Report Placeholder')
                        temp_file_path = temp_file.name

                    # Save the file to the report
                    with open(temp_file_path, 'rb') as f:
                        report.file.save(f'demographic_analysis_{report.id}.pdf', f)

                    # Clean up the temporary file
                    os.remove(temp_file_path)

                elif report_format == 'html':
                    # Create an HTML file
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Demographic Analysis - {questionnaire.title}</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; }}
                            h1, h2 {{ color: #333; }}
                            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                            th {{ background-color: #f2f2f2; }}
                            tr:nth-child(even) {{ background-color: #f9f9f9; }}
                            .chart {{ margin: 20px 0; max-width: 100%; }}
                        </style>
                    </head>
                    <body>
                        <h1>Demographic Analysis - {questionnaire.title}</h1>
                        <p>Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p>Analysis by Age Group</p>

                        <div class="chart">
                            <img src="data:image/png;base64,{chart_data}" alt="Age Distribution Chart" style="max-width: 100%;">
                        </div>

                        <h2>Age Group Statistics</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>Age Group</th>
                                    <th>Number of Responses</th>
                                    <th>Average Score</th>
                                    <th>Completion Rate</th>
                                </tr>
                            </thead>
                            <tbody>
                    """

                    for group, stats in age_stats.items():
                        html_content += f"""
                                <tr>
                                    <td>{group}</td>
                                    <td>{stats['count']}</td>
                                    <td>{stats['avg_score']:.2f}</td>
                                    <td>{stats['completion_rate']:.1f}%</td>
                                </tr>
                        """

                    html_content += """
                            </tbody>
                        </table>
                    </body>
                    </html>
                    """

                    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
                        temp_file.write(html_content.encode('utf-8'))
                        temp_file_path = temp_file.name

                    # Save the file to the report
                    with open(temp_file_path, 'rb') as f:
                        report.file.save(f'demographic_analysis_{report.id}.html', f)

                    # Clean up the temporary file
                    os.remove(temp_file_path)

            elif demographic_type == 'gender':
                # Calculate statistics for each gender
                gender_stats = {}
                for gender in ['male', 'female', 'other', 'prefer_not_to_say']:
                    gender_responses = responses.filter(patient_gender=gender)
                    gender_stats[gender] = {
                        'count': gender_responses.count(),
                        'avg_score': gender_responses.exclude(score__isnull=True).aggregate(Avg('score'))['score__avg'] or 0,
                        'completion_rate': (gender_responses.filter(status='completed').count() / gender_responses.count() * 100) if gender_responses.count() > 0 else 0
                    }

                # Generate gender distribution chart
                plt.figure(figsize=(10, 6))
                groups = list(gender_stats.keys())
                counts = [gender_stats[group]['count'] for group in groups]

                plt.bar(groups, counts)
                plt.title('Response Distribution by Gender')
                plt.xlabel('Gender')
                plt.ylabel('Number of Responses')
                plt.grid(axis='y', alpha=0.3)

                # Save chart to buffer
                buffer = BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                chart_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()

                # Generate report content based on format
                if report_format == 'pdf':
                    # This would typically use a PDF generation library like ReportLab or WeasyPrint
                    # For now, we'll just create a placeholder file
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                        temp_file.write(b'PDF Report Placeholder')
                        temp_file_path = temp_file.name

                    # Save the file to the report
                    with open(temp_file_path, 'rb') as f:
                        report.file.save(f'demographic_analysis_{report.id}.pdf', f)

                    # Clean up the temporary file
                    os.remove(temp_file_path)

                elif report_format == 'html':
                    # Create an HTML file
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Demographic Analysis - {questionnaire.title}</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; }}
                            h1, h2 {{ color: #333; }}
                            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                            th {{ background-color: #f2f2f2; }}
                            tr:nth-child(even) {{ background-color: #f9f9f9; }}
                            .chart {{ margin: 20px 0; max-width: 100%; }}
                        </style>
                    </head>
                    <body>
                        <h1>Demographic Analysis - {questionnaire.title}</h1>
                        <p>Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p>Analysis by Gender</p>

                        <div class="chart">
                            <img src="data:image/png;base64,{chart_data}" alt="Gender Distribution Chart" style="max-width: 100%;">
                        </div>

                        <h2>Gender Statistics</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>Gender</th>
                                    <th>Number of Responses</th>
                                    <th>Average Score</th>
                                    <th>Completion Rate</th>
                                </tr>
                            </thead>
                            <tbody>
                    """

                    for gender, stats in gender_stats.items():
                        gender_display = gender.capitalize() if gender != 'prefer_not_to_say' else 'Prefer not to say'
                        html_content += f"""
                                <tr>
                                    <td>{gender_display}</td>
                                    <td>{stats['count']}</td>
                                    <td>{stats['avg_score']:.2f}</td>
                                    <td>{stats['completion_rate']:.1f}%</td>
                                </tr>
                        """

                    html_content += """
                            </tbody>
                        </table>
                    </body>
                    </html>
                    """

                    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
                        temp_file.write(html_content.encode('utf-8'))
                        temp_file_path = temp_file.name

                    # Save the file to the report
                    with open(temp_file_path, 'rb') as f:
                        report.file.save(f'demographic_analysis_{report.id}.html', f)

                    # Clean up the temporary file
                    os.remove(temp_file_path)

            # Mark the report as completed
            report.mark_as_completed()

            messages.success(request, "Demographic analysis report generated successfully.")
            return redirect('analytics:report_detail', pk=report.id)

        except Exception as e:
            # Mark the report as failed
            report.mark_as_failed(str(e))

            messages.error(request, f"Error generating report: {str(e)}")
            return redirect('analytics:report_demographic_analysis')

    # Get all questionnaires the user has access to
    if request.user.is_staff:
        questionnaires = Questionnaire.objects.all()
    else:
        # Get questionnaires created by the user
        user_questionnaires = Questionnaire.objects.filter(created_by=request.user)

        # Get questionnaires from organizations the user is a member of
        org_memberships = request.user.organization_memberships.filter(is_active=True)
        org_ids = [membership.organization_id for membership in org_memberships]
        org_questionnaires = Questionnaire.objects.filter(organization__in=org_ids)

        # Combine the querysets
        questionnaires = user_questionnaires | org_questionnaires

    context = {
        'questionnaires': questionnaires,
        'report_formats': Report.REPORT_FORMAT_CHOICES,
    }

    return render(request, 'analytics/reports/report_demographic_analysis_form.html', context)

@login_required
def report_risk_assessment(request):
    """
    Generate a risk assessment report
    """
    # This would be implemented with risk assessment analysis

    context = {
        'questionnaires': Questionnaire.objects.all(),
        'report_formats': Report.REPORT_FORMAT_CHOICES,
    }

    return render(request, 'analytics/reports/report_risk_assessment_form.html', context)

@login_required
def report_custom_export(request):
    """
    Generate a custom export report
    """
    # This would be implemented with custom export options

    context = {
        'questionnaires': Questionnaire.objects.all(),
        'report_formats': Report.REPORT_FORMAT_CHOICES,
    }

    return render(request, 'analytics/reports/report_custom_export_form.html', context)

@login_required
def report_schedule_list(request):
    """
    Display a list of report schedules
    """
    # Get all report schedules for this user
    schedules = ReportSchedule.objects.filter(created_by=request.user).order_by('next_run')

    context = {
        'schedules': schedules,
    }

    return render(request, 'analytics/reports/report_schedule_list.html', context)

@login_required
def report_schedule_create(request):
    """
    Create a new report schedule
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        report_type = request.POST.get('report_type')
        report_format = request.POST.get('report_format')
        frequency = request.POST.get('frequency')
        questionnaire_id = request.POST.get('questionnaire')

        if not name or not report_type or not report_format or not frequency:
            messages.error(request, "Name, report type, report format, and frequency are required.")
            return redirect('analytics:report_schedule_create')

        # Get the questionnaire if provided
        questionnaire = None
        if questionnaire_id:
            questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)

            # Check if user has permission to view this questionnaire
            if not request.user.is_staff and questionnaire.created_by != request.user:
                if questionnaire.organization:
                    # Check if user is a member of the organization
                    if not questionnaire.organization.members.filter(user=request.user, is_active=True).exists():
                        messages.error(request, "You don't have permission to schedule reports for this questionnaire.")
                        return redirect('analytics:report_schedule_create')
                else:
                    messages.error(request, "You don't have permission to schedule reports for this questionnaire.")
                    return redirect('analytics:report_schedule_create')

        # Create the schedule
        schedule = ReportSchedule.objects.create(
            name=name,
            description=description,
            report_type=report_type,
            report_format=report_format,
            frequency=frequency,
            next_run=timezone.now(),  # Will be updated by update_next_run
            questionnaire=questionnaire,
            organization=questionnaire.organization if questionnaire else None,
            created_by=request.user
        )

        # Update the next run time
        schedule.update_next_run()

        messages.success(request, "Report schedule created successfully.")
        return redirect('analytics:report_schedule_list')

    # Get all questionnaires the user has access to
    if request.user.is_staff:
        questionnaires = Questionnaire.objects.all()
    else:
        # Get questionnaires created by the user
        user_questionnaires = Questionnaire.objects.filter(created_by=request.user)

        # Get questionnaires from organizations the user is a member of
        org_memberships = request.user.organization_memberships.filter(is_active=True)
        org_ids = [membership.organization_id for membership in org_memberships]
        org_questionnaires = Questionnaire.objects.filter(organization__in=org_ids)

        # Combine the querysets
        questionnaires = user_questionnaires | org_questionnaires

    context = {
        'questionnaires': questionnaires,
        'report_types': Report.REPORT_TYPE_CHOICES,
        'report_formats': Report.REPORT_FORMAT_CHOICES,
        'frequency_choices': ReportSchedule.FREQUENCY_CHOICES,
    }

    return render(request, 'analytics/reports/report_schedule_form.html', context)

@login_required
def report_schedule_edit(request, pk):
    """
    Edit a report schedule
    """
    schedule = get_object_or_404(ReportSchedule, pk=pk)

    # Check if user has permission to edit this schedule
    if schedule.created_by != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to edit this report schedule.")
        return redirect('analytics:report_schedule_list')

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        report_type = request.POST.get('report_type')
        report_format = request.POST.get('report_format')
        frequency = request.POST.get('frequency')
        questionnaire_id = request.POST.get('questionnaire')
        is_active = request.POST.get('is_active') == 'on'

        if not name or not report_type or not report_format or not frequency:
            messages.error(request, "Name, report type, report format, and frequency are required.")
            return redirect('analytics:report_schedule_edit', pk=pk)

        # Get the questionnaire if provided
        questionnaire = None
        if questionnaire_id:
            questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)

            # Check if user has permission to view this questionnaire
            if not request.user.is_staff and questionnaire.created_by != request.user:
                if questionnaire.organization:
                    # Check if user is a member of the organization
                    if not questionnaire.organization.members.filter(user=request.user, is_active=True).exists():
                        messages.error(request, "You don't have permission to schedule reports for this questionnaire.")
                        return redirect('analytics:report_schedule_edit', pk=pk)
                else:
                    messages.error(request, "You don't have permission to schedule reports for this questionnaire.")
                    return redirect('analytics:report_schedule_edit', pk=pk)

        # Update the schedule
        schedule.name = name
        schedule.description = description
        schedule.report_type = report_type
        schedule.report_format = report_format
        schedule.frequency = frequency
        schedule.questionnaire = questionnaire
        schedule.organization = questionnaire.organization if questionnaire else None
        schedule.is_active = is_active
        schedule.save()

        # Update the next run time if the frequency changed
        if schedule.frequency != frequency:
            schedule.update_next_run()

        messages.success(request, "Report schedule updated successfully.")
        return redirect('analytics:report_schedule_list')

    # Get all questionnaires the user has access to
    if request.user.is_staff:
        questionnaires = Questionnaire.objects.all()
    else:
        # Get questionnaires created by the user
        user_questionnaires = Questionnaire.objects.filter(created_by=request.user)

        # Get questionnaires from organizations the user is a member of
        org_memberships = request.user.organization_memberships.filter(is_active=True)
        org_ids = [membership.organization_id for membership in org_memberships]
        org_questionnaires = Questionnaire.objects.filter(organization__in=org_ids)

        # Combine the querysets
        questionnaires = user_questionnaires | org_questionnaires

    context = {
        'schedule': schedule,
        'questionnaires': questionnaires,
        'report_types': Report.REPORT_TYPE_CHOICES,
        'report_formats': Report.REPORT_FORMAT_CHOICES,
        'frequency_choices': ReportSchedule.FREQUENCY_CHOICES,
    }

    return render(request, 'analytics/reports/report_schedule_form.html', context)

@login_required
def report_schedule_delete(request, pk):
    """
    Delete a report schedule
    """
    schedule = get_object_or_404(ReportSchedule, pk=pk)

    # Check if user has permission to delete this schedule
    if schedule.created_by != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to delete this report schedule.")
        return redirect('analytics:report_schedule_list')

    if request.method == 'POST':
        # Delete the schedule
        schedule.delete()

        messages.success(request, "Report schedule deleted successfully.")
        return redirect('analytics:report_schedule_list')

    context = {
        'schedule': schedule,
    }

    return render(request, 'analytics/reports/report_schedule_confirm_delete.html', context)
