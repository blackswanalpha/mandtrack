import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.urls import reverse
from django.core.paginator import Paginator

from surveys.models import Survey
from feedback.models import Response as SurveyResponse, Answer
from analytics.services.gemini_service import GeminiService
from analytics.models import AIModel, AIAnalysisResult, AIInsight

logger = logging.getLogger(__name__)

@login_required
def batch_analysis_select(request):
    """
    Select responses for batch analysis
    """
    # Get all surveys the user has access to
    if request.user.is_staff:
        surveys = Survey.objects.all()
    else:
        # Get surveys created by the user or from organizations they belong to
        surveys = Survey.objects.filter(
            Q(created_by=request.user) | 
            Q(organization__members__user=request.user)
        ).distinct()
    
    # Get filter parameters
    survey_id = request.GET.get('survey_id')
    status = request.GET.get('status')
    risk_level = request.GET.get('risk_level')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search_query = request.GET.get('q')
    
    # Start with all responses
    responses = SurveyResponse.objects.all()
    
    # Apply access restrictions
    if not request.user.is_staff:
        responses = responses.filter(
            Q(survey__created_by=request.user) | 
            Q(survey__organization__members__user=request.user) |
            Q(respondent=request.user)
        ).distinct()
    
    # Apply filters
    if survey_id:
        responses = responses.filter(survey_id=survey_id)
    
    if status:
        responses = responses.filter(status=status)
    
    if risk_level:
        responses = responses.filter(risk_level=risk_level)
    
    if date_from:
        responses = responses.filter(created_at__gte=date_from)
    
    if date_to:
        responses = responses.filter(created_at__lte=date_to)
    
    if search_query:
        responses = responses.filter(
            Q(respondent__email__icontains=search_query) |
            Q(respondent_email__icontains=search_query) |
            Q(respondent_name__icontains=search_query) |
            Q(response_id__icontains=search_query)
        )
    
    # Annotate with answer count and order by most recent first
    responses = responses.annotate(answer_count=Count('answers')).order_by('-created_at')
    
    # Paginate the results
    paginator = Paginator(responses, 20)  # Show 20 responses per page
    page = request.GET.get('page', 1)
    responses = paginator.get_page(page)
    
    # Get status and risk level choices
    statuses = SurveyResponse.STATUS_CHOICES
    risk_levels = SurveyResponse.RISK_LEVEL_CHOICES
    
    context = {
        'surveys': surveys,
        'responses': responses,
        'statuses': statuses,
        'risk_levels': risk_levels,
        'selected_survey': survey_id,
        'selected_status': status,
        'selected_risk_level': risk_level,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
    }
    
    return render(request, 'analytics/batch_analysis_select.html', context)

@login_required
def batch_analysis_run(request):
    """
    Run batch analysis on selected responses
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('analytics:batch_analysis_select')
    
    # Get selected response IDs
    response_ids = request.POST.getlist('response_ids')
    
    if not response_ids:
        messages.error(request, "No responses selected for analysis.")
        return redirect('analytics:batch_analysis_select')
    
    # Get analysis type
    analysis_type = request.POST.get('analysis_type', 'comprehensive')
    
    # Create a batch analysis job
    from analytics.models.batch import BatchAnalysisJob
    
    job = BatchAnalysisJob.objects.create(
        name=f"Batch Analysis {timezone.now().strftime('%Y-%m-%d %H:%M')}",
        analysis_type=analysis_type,
        status='pending',
        created_by=request.user,
        total_responses=len(response_ids)
    )
    
    # Add responses to the job
    job.responses.set(SurveyResponse.objects.filter(pk__in=response_ids))
    
    # Start the analysis process asynchronously
    # In a real implementation, this would be handled by a task queue like Celeron
    # For simplicity, we'll process it synchronously here
    try:
        process_batch_analysis(job.id)
        return redirect('analytics:batch_analysis_results', job_id=job.id)
    except Exception as e:
        logger.error(f"Error starting batch analysis: {str(e)}")
        messages.error(request, f"Error starting batch analysis: {str(e)}")
        return redirect('analytics:batch_analysis_select')

def process_batch_analysis(job_id):
    """
    Process a batch analysis job
    """
    # Get the job
    job = get_object_or_404(BatchAnalysisJob, pk=job_id)
    
    # Update job status
    job.status = 'processing'
    job.started_at = timezone.now()
    job.save()
    
    try:
        # Initialize the Gemini service
        gemini_service = GeminiService(api_key="AIzaSyAp5usIOWlm16BgN1tfGje4aD0YKVa1Mjc")
        
        # Get all responses for this job
        responses = job.responses.all()
        
        # Process each response
        processed_count = 0
        for response in responses:
            try:
                # Check if analysis already exists
                try:
                    analysis = response.analysis
                    # Skip if analysis already exists
                    job.skipped_responses += 1
                    job.save()
                    continue
                except:
                    pass
                
                # Get all answers for this response
                answers = Answer.objects.filter(response=response).select_related('question', 'selected_choice').prefetch_related('multiple_choices')
                
                # Prepare the data for analysis
                questionnaire_info = {
                    "title": response.survey.title,
                    "category": response.survey.category,
                    "description": response.survey.description,
                    "total_questions": answers.count(),
                    "scoring_method": "weighted_sum" if response.total_score is not None else "none"
                }
                
                # Format the answers for the API
                answer_data = []
                for answer in answers:
                    answer_item = {
                        "question_text": answer.question.text,
                        "question_type": answer.question.question_type,
                        "question_category": answer.question.category,
                        "is_scored": answer.question.is_scored,
                    }
                    
                    # Add the appropriate answer value based on question type
                    if answer.question.question_type in ['text', 'textarea']:
                        answer_item["answer"] = answer.text_answer
                    elif answer.question.question_type in ['radio', 'dropdown', 'single_choice']:
                        answer_item["answer"] = answer.selected_choice.text if answer.selected_choice else "No selection"
                    elif answer.question.question_type in ['checkbox', 'multiple_choice']:
                        answer_item["answer"] = [choice.text for choice in answer.multiple_choices.all()]
                    elif answer.question.question_type in ['scale', 'number']:
                        answer_item["answer"] = answer.numeric_value
                    
                    # Add score information if available
                    if hasattr(answer, 'score') and answer.score is not None:
                        answer_item["score"] = answer.score
                        answer_item["weight"] = answer.question.scoring_weight
                        answer_item["weighted_score"] = answer.score * answer.question.scoring_weight
                    
                    answer_data.append(answer_item)
                
                # Add respondent information
                respondent_info = {
                    "age": getattr(response, 'patient_age', None),
                    "gender": getattr(response, 'patient_gender', None),
                    "completion_time": getattr(response, 'completion_time', None),
                    "total_score": response.total_score,
                    "risk_level": response.risk_level
                }
                
                # Combine all data
                analysis_data = {
                    "questionnaire": questionnaire_info,
                    "respondent": respondent_info,
                    "answers": answer_data
                }
                
                # Generate the analysis using Gemini API
                if job.analysis_type == 'comprehensive':
                    result = gemini_service.analyze_questionnaire_data(analysis_data, questionnaire_info)
                elif job.analysis_type == 'insights':
                    result = gemini_service.generate_insights(analysis_data, questionnaire_info)
                else:
                    result = gemini_service.analyze_text(json.dumps(analysis_data), job.analysis_type)
                
                # Extract the analysis components
                summary = result.get('summary', f"Analysis for {response.survey.title}")
                detailed_analysis = result.get('detailed_analysis', "Analysis not available.")
                recommendations = result.get('recommendations', "No specific recommendations available.")
                
                # Create the raw data for storage
                raw_data = {
                    "gemini_response": result,
                    "analysis_data": analysis_data,
                    "generated_at": timezone.now().isoformat(),
                    "model": "gemini-1.5-pro",
                    "batch_job_id": job.id
                }
                
                # Create a new analysis
                from feedback.models import AIAnalysis
                analysis = AIAnalysis(
                    response=response,
                    summary=summary,
                    detailed_analysis=detailed_analysis,
                    recommendations=recommendations,
                    raw_data=raw_data,
                    model_used="Gemini Pro (Batch)",
                    created_by=job.created_by
                )
                analysis.save()
                
                # Update job progress
                processed_count += 1
                job.processed_responses = processed_count
                job.save()
                
            except Exception as e:
                logger.error(f"Error processing response {response.id}: {str(e)}")
                job.error_responses += 1
                job.error_details.append({
                    "response_id": str(response.id),
                    "error": str(e)
                })
                job.save()
        
        # Update job status
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.save()
        
        # Generate aggregate insights
        try:
            generate_aggregate_insights(job)
        except Exception as e:
            logger.error(f"Error generating aggregate insights: {str(e)}")
            job.notes = f"Error generating aggregate insights: {str(e)}"
            job.save()
        
    except Exception as e:
        logger.error(f"Error in batch analysis job: {str(e)}")
        job.status = 'failed'
        job.error_details.append({
            "error": str(e),
            "stage": "job_processing"
        })
        job.completed_at = timezone.now()
        job.save()

def generate_aggregate_insights(job):
    """
    Generate aggregate insights from a batch analysis job
    """
    # Get all analyses from this job
    from feedback.models import AIAnalysis
    analyses = AIAnalysis.objects.filter(
        raw_data__batch_job_id=job.id
    )
    
    if analyses.count() == 0:
        return
    
    # Get the first response to determine the survey
    first_response = job.responses.first()
    if not first_response:
        return
    
    survey = first_response.survey
    
    # Initialize the Gemini service
    gemini_service = GeminiService(api_key="AIzaSyAp5usIOWlm16BgN1tfGje4aD0YKVa1Mjc")
    
    # Prepare data for aggregate analysis
    analysis_summaries = []
    for analysis in analyses:
        analysis_summaries.append({
            "response_id": str(analysis.response.id),
            "summary": analysis.summary,
            "recommendations": analysis.recommendations,
            "score": analysis.response.total_score,
            "risk_level": analysis.response.risk_level,
            "insights": analysis.raw_data.get("gemini_response", {}).get("insights", {})
        })
    
    # Prepare the aggregate data
    aggregate_data = {
        "job_id": job.id,
        "job_name": job.name,
        "analysis_type": job.analysis_type,
        "survey": {
            "id": survey.id,
            "title": survey.title,
            "category": survey.category,
            "description": survey.description
        },
        "total_responses": job.total_responses,
        "processed_responses": job.processed_responses,
        "skipped_responses": job.skipped_responses,
        "error_responses": job.error_responses,
        "analyses": analysis_summaries
    }
    
    # Generate aggregate insights
    prompt = f"""
    You are an expert data analyst specializing in survey and questionnaire analysis.
    
    I'm going to provide you with a batch of analyses from multiple responses to the same questionnaire.
    Please analyze this data and provide aggregate insights, patterns, and recommendations.
    
    Batch Analysis Information:
    {json.dumps(aggregate_data, indent=2)}
    
    Please provide your analysis in the following JSON format:
    {{
        "summary": "Overall summary of the batch analysis",
        "key_patterns": [
            {{
                "pattern": "Description of pattern",
                "frequency": "Percentage or count of responses showing this pattern",
                "significance": "Why this pattern is significant"
            }}
        ],
        "common_recommendations": [
            {{
                "recommendation": "Common recommendation",
                "frequency": "How often this recommendation appears",
                "priority": "high/medium/low"
            }}
        ],
        "risk_distribution": {{
            "low": "Percentage of low risk responses",
            "medium": "Percentage of medium risk responses",
            "high": "Percentage of high risk responses",
            "critical": "Percentage of critical risk responses"
        }},
        "score_analysis": {{
            "average": "Average score",
            "median": "Median score",
            "range": "Range of scores",
            "distribution": "Description of score distribution"
        }},
        "insights": [
            {{
                "title": "Insight title",
                "description": "Detailed description of the insight",
                "supporting_data": "Reference to the data that supports this insight"
            }}
        ],
        "recommendations": [
            {{
                "title": "Recommendation title",
                "description": "Detailed description of the recommendation",
                "priority": "high/medium/low",
                "rationale": "Why this recommendation is important"
            }}
        ]
    }}
    
    Focus on finding meaningful patterns, correlations, and insights across all responses.
    """
    
    try:
        response = gemini_service.model.generate_content(prompt)
        result = json.loads(response.text)
        
        # Save the aggregate insights to the job
        job.aggregate_insights = result
        job.save()
        
        # Create AI insights from the aggregate analysis
        if "insights" in result:
            for insight_data in result["insights"]:
                AIInsight.objects.create(
                    title=insight_data.get("title", "Untitled Insight"),
                    description=insight_data.get("description", ""),
                    insight_type="pattern",
                    severity="medium",
                    questionnaire=survey,
                    supporting_data={"batch_job_id": job.id, "data": insight_data.get("supporting_data", "")},
                    created_at=timezone.now()
                )
        
    except Exception as e:
        logger.error(f"Error generating aggregate insights: {str(e)}")
        job.notes = f"Error generating aggregate insights: {str(e)}"
        job.save()

@login_required
def batch_analysis_results(request, job_id):
    """
    View results of a batch analysis job
    """
    # Get the job
    from analytics.models.batch import BatchAnalysisJob
    job = get_object_or_404(BatchAnalysisJob, pk=job_id)
    
    # Check if the user has permission to view this job
    if job.created_by != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to view this batch analysis job.")
        return redirect('analytics:batch_analysis_select')
    
    # Get all analyses from this job
    from feedback.models import AIAnalysis
    analyses = AIAnalysis.objects.filter(
        raw_data__batch_job_id=job.id
    ).select_related('response')
    
    context = {
        'job': job,
        'analyses': analyses,
    }
    
    return render(request, 'analytics/batch_analysis_results.html', context)

@login_required
def batch_analysis_aggregate(request, job_id):
    """
    View aggregate insights from a batch analysis job
    """
    # Get the job
    from analytics.models.batch import BatchAnalysisJob
    job = get_object_or_404(BatchAnalysisJob, pk=job_id)
    
    # Check if the user has permission to view this job
    if job.created_by != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to view this batch analysis job.")
        return redirect('analytics:batch_analysis_select')
    
    # Get insights related to this job
    insights = AIInsight.objects.filter(
        supporting_data__batch_job_id=job.id
    )
    
    context = {
        'job': job,
        'insights': insights,
    }
    
    return render(request, 'analytics/batch_analysis_aggregate.html', context)

@login_required
def batch_analysis_export(request, job_id):
    """
    Export batch analysis results
    """
    # Get the job
    from analytics.models.batch import BatchAnalysisJob
    job = get_object_or_404(BatchAnalysisJob, pk=job_id)
    
    # Check if the user has permission to export this job
    if job.created_by != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to export this batch analysis job.")
        return redirect('analytics:batch_analysis_select')
    
    # Get all analyses from this job
    from feedback.models import AIAnalysis
    analyses = AIAnalysis.objects.filter(
        raw_data__batch_job_id=job.id
    ).select_related('response')
    
    # Determine export format
    export_format = request.GET.get('format', 'json')
    
    if export_format == 'csv':
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="batch_analysis_{job_id}.csv"'
        
        import csv
        writer = csv.writer(response)
        
        # Write header row
        writer.writerow(['Response ID', 'Survey', 'Status', 'Score', 'Risk Level', 'Summary', 'Recommendations'])
        
        # Write data rows
        for analysis in analyses:
            writer.writerow([
                analysis.response.id,
                analysis.response.survey.title,
                analysis.response.get_status_display(),
                analysis.response.total_score,
                analysis.response.get_risk_level_display(),
                analysis.summary,
                analysis.recommendations
            ])
        
        return response
    
    else:  # JSON format
        # Create JSON response
        data = {
            'job': {
                'id': job.id,
                'name': job.name,
                'analysis_type': job.analysis_type,
                'status': job.status,
                'created_at': job.created_at.isoformat(),
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'total_responses': job.total_responses,
                'processed_responses': job.processed_responses,
                'skipped_responses': job.skipped_responses,
                'error_responses': job.error_responses,
            },
            'aggregate_insights': job.aggregate_insights,
            'analyses': []
        }
        
        for analysis in analyses:
            data['analyses'].append({
                'response_id': str(analysis.response.id),
                'survey': analysis.response.survey.title,
                'status': analysis.response.status,
                'score': analysis.response.total_score,
                'risk_level': analysis.response.risk_level,
                'summary': analysis.summary,
                'detailed_analysis': analysis.detailed_analysis,
                'recommendations': analysis.recommendations,
                'created_at': analysis.created_at.isoformat()
            })
        
        response = JsonResponse(data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="batch_analysis_{job_id}.json"'
        return response
