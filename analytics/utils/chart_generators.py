"""
Utility functions for generating charts and visualizations.
"""
import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import seaborn as sns
from io import BytesIO
import base64
from datetime import datetime, timedelta
from django.db.models import Count, Avg, Sum, F, Q
from django.utils import timezone
from surveys.models import Questionnaire, Question, QuestionChoice
from feedback.models import Response, Answer, AIAnalysis

def get_base64_chart(plt):
    """Convert matplotlib plot to base64 string for embedding in HTML"""
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_png).decode('utf-8')

def generate_response_distribution_chart(questionnaire_id):
    """Generate a chart showing the distribution of responses by risk level"""
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)
    responses = Response.objects.filter(survey=questionnaire)
    
    # Count responses by risk level
    risk_counts = responses.values('risk_level').annotate(count=Count('id')).order_by('risk_level')
    
    # Prepare data for plotting
    risk_levels = []
    counts = []
    colors = []
    
    for item in risk_counts:
        risk_level = item['risk_level']
        risk_levels.append(risk_level.capitalize())
        counts.append(item['count'])
        
        # Set colors based on risk level
        if risk_level == 'low':
            colors.append('#4CAF50')  # Green
        elif risk_level == 'medium':
            colors.append('#FFC107')  # Amber
        elif risk_level == 'high':
            colors.append('#F44336')  # Red
        elif risk_level == 'critical':
            colors.append('#9C27B0')  # Purple
        else:
            colors.append('#9E9E9E')  # Grey
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    bars = plt.bar(risk_levels, counts, color=colors)
    
    # Add labels and title
    plt.title(f'Response Distribution by Risk Level - {questionnaire.title}', fontsize=14)
    plt.xlabel('Risk Level', fontsize=12)
    plt.ylabel('Number of Responses', fontsize=12)
    
    # Add count labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                 f'{int(height)}', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Convert to base64 for embedding in HTML
    chart_base64 = get_base64_chart(plt)
    
    return chart_base64

def generate_score_distribution_chart(questionnaire_id):
    """Generate a histogram showing the distribution of scores"""
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)
    responses = Response.objects.filter(survey=questionnaire).exclude(score__isnull=True)
    
    if not responses.exists():
        return None
    
    # Get scores
    scores = [response.score for response in responses]
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    
    # Get scoring config for this questionnaire
    from surveys.models import ScoringConfig
    scoring_config = ScoringConfig.objects.filter(survey=questionnaire, is_active=True).first()
    
    if scoring_config and scoring_config.rules:
        # Create colored bins based on scoring rules
        bins = []
        colors = []
        labels = []
        
        for rule in scoring_config.rules:
            bins.extend([rule['min'], rule['max']])
            colors.append(rule.get('color', '#9E9E9E'))
            labels.append(rule.get('label', 'Unknown'))
        
        bins = sorted(list(set(bins)))  # Remove duplicates and sort
        
        # Create histogram with custom bins
        n, bins, patches = plt.hist(scores, bins=bins, alpha=0.7, edgecolor='black')
        
        # Color the bins according to scoring rules
        for i, patch in enumerate(patches):
            if i < len(colors):
                patch.set_facecolor(colors[i])
        
        # Add a legend
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=rule.get('color', '#9E9E9E'), 
                                edgecolor='black',
                                label=f"{rule.get('label', 'Unknown')} ({rule['min']}-{rule['max']})") 
                          for rule in scoring_config.rules]
        plt.legend(handles=legend_elements, title="Score Ranges")
    else:
        # Create a standard histogram
        plt.hist(scores, bins=10, alpha=0.7, color='#2196F3', edgecolor='black')
    
    # Add labels and title
    plt.title(f'Score Distribution - {questionnaire.title}', fontsize=14)
    plt.xlabel('Score', fontsize=12)
    plt.ylabel('Number of Responses', fontsize=12)
    
    plt.tight_layout()
    
    # Convert to base64 for embedding in HTML
    chart_base64 = get_base64_chart(plt)
    
    return chart_base64

def generate_response_trend_chart(questionnaire_id, days=30):
    """Generate a line chart showing response trends over time"""
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)
    
    # Get date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get responses in date range
    responses = Response.objects.filter(
        survey=questionnaire,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).order_by('created_at')
    
    if not responses.exists():
        return None
    
    # Group responses by date
    response_dates = responses.values('created_at__date').annotate(
        count=Count('id'),
        avg_score=Avg('score')
    ).order_by('created_at__date')
    
    # Prepare data for plotting
    dates = [item['created_at__date'] for item in response_dates]
    counts = [item['count'] for item in response_dates]
    avg_scores = [item['avg_score'] for item in response_dates]
    
    # Create the chart with two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot response counts
    color = 'tab:blue'
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Number of Responses', color=color, fontsize=12)
    ax1.plot(dates, counts, color=color, marker='o', linestyle='-', linewidth=2, markersize=8)
    ax1.tick_params(axis='y', labelcolor=color)
    
    # Create second y-axis for average scores
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Average Score', color=color, fontsize=12)
    ax2.plot(dates, avg_scores, color=color, marker='s', linestyle='--', linewidth=2, markersize=8)
    ax2.tick_params(axis='y', labelcolor=color)
    
    # Format x-axis dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 10)))
    plt.gcf().autofmt_xdate()
    
    # Add title and grid
    plt.title(f'Response Trend - {questionnaire.title} (Last {days} Days)', fontsize=14)
    ax1.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Convert to base64 for embedding in HTML
    chart_base64 = get_base64_chart(plt)
    
    return chart_base64

def generate_question_response_chart(question_id):
    """Generate a chart showing the distribution of answers for a specific question"""
    question = Question.objects.get(id=question_id)
    
    if question.question_type not in ['single_choice', 'multiple_choice', 'scale']:
        return None
    
    # Get all answers for this question
    answers = Answer.objects.filter(question=question)
    
    if not answers.exists():
        return None
    
    # For single choice questions, count by selected choice
    if question.question_type == 'single_choice':
        # Count answers by selected choice
        choice_counts = answers.values('selected_choice__text').annotate(
            count=Count('id')
        ).order_by('selected_choice__order')
        
        # Prepare data for plotting
        choices = [item['selected_choice__text'] for item in choice_counts if item['selected_choice__text']]
        counts = [item['count'] for item in choice_counts if item['selected_choice__text']]
        
        # Create the chart
        plt.figure(figsize=(10, 6))
        
        # Use horizontal bar chart if there are many choices or long choice texts
        if len(choices) > 5 or any(len(str(choice)) > 15 for choice in choices):
            bars = plt.barh(choices, counts, color='#2196F3')
            
            # Add count labels
            for i, bar in enumerate(bars):
                width = bar.get_width()
                plt.text(width + 0.3, bar.get_y() + bar.get_height()/2,
                         f'{int(width)}', ha='left', va='center')
            
            plt.xlabel('Number of Responses', fontsize=12)
            plt.ylabel('Answer Choice', fontsize=12)
        else:
            bars = plt.bar(choices, counts, color='#2196F3')
            
            # Add count labels
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                         f'{int(height)}', ha='center', va='bottom')
            
            plt.xlabel('Answer Choice', fontsize=12)
            plt.ylabel('Number of Responses', fontsize=12)
            plt.xticks(rotation=45, ha='right')
    
    # For scale questions, show a histogram
    elif question.question_type == 'scale':
        # Extract numeric values from answers
        values = []
        for answer in answers:
            try:
                if answer.value and isinstance(answer.value, dict) and 'value' in answer.value:
                    values.append(float(answer.value['value']))
            except (ValueError, TypeError):
                continue
        
        if not values:
            return None
        
        # Create the chart
        plt.figure(figsize=(10, 6))
        plt.hist(values, bins=10, color='#2196F3', edgecolor='black', alpha=0.7)
        plt.xlabel('Scale Value', fontsize=12)
        plt.ylabel('Number of Responses', fontsize=12)
    
    # Add title
    plt.title(f'Response Distribution - {question.text[:50]}{"..." if len(question.text) > 50 else ""}', fontsize=14)
    plt.tight_layout()
    
    # Convert to base64 for embedding in HTML
    chart_base64 = get_base64_chart(plt)
    
    return chart_base64

def generate_ai_sentiment_chart(questionnaire_id):
    """Generate a chart showing sentiment analysis from AI results"""
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)
    
    # Get all responses for this questionnaire
    responses = Response.objects.filter(survey=questionnaire)
    
    # Get AI analyses for these responses
    analyses = AIAnalysis.objects.filter(response__in=responses)
    
    if not analyses.exists():
        return None
    
    # Count analyses by sentiment/risk level
    sentiment_counts = {}
    
    for analysis in analyses:
        # Try to extract sentiment from insights
        sentiment = None
        
        # First check if we have a risk level in the response
        if analysis.response.risk_level:
            sentiment = analysis.response.risk_level
        # Then check if we have sentiment in the insights
        elif analysis.insights and isinstance(analysis.insights, dict):
            if 'sentiment' in analysis.insights:
                sentiment = analysis.insights['sentiment']
            elif 'key_points' in analysis.insights:
                # Try to extract sentiment from key points
                for point in analysis.insights['key_points']:
                    if 'range' in point.lower():
                        for level in ['low', 'medium', 'high', 'critical']:
                            if level in point.lower():
                                sentiment = level
                                break
        
        if sentiment:
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
    
    if not sentiment_counts:
        return None
    
    # Prepare data for plotting
    sentiments = list(sentiment_counts.keys())
    counts = list(sentiment_counts.values())
    
    # Define colors for different sentiments
    colors = []
    for sentiment in sentiments:
        if sentiment.lower() == 'low' or sentiment.lower() == 'positive':
            colors.append('#4CAF50')  # Green
        elif sentiment.lower() == 'medium' or sentiment.lower() == 'neutral':
            colors.append('#FFC107')  # Amber
        elif sentiment.lower() == 'high' or sentiment.lower() == 'negative':
            colors.append('#F44336')  # Red
        elif sentiment.lower() == 'critical':
            colors.append('#9C27B0')  # Purple
        else:
            colors.append('#9E9E9E')  # Grey
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    plt.pie(counts, labels=sentiments, colors=colors, autopct='%1.1f%%', startangle=90, shadow=True)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    
    plt.title(f'AI Analysis Sentiment Distribution - {questionnaire.title}', fontsize=14)
    
    # Convert to base64 for embedding in HTML
    chart_base64 = get_base64_chart(plt)
    
    return chart_base64

def generate_ai_recommendations_chart(questionnaire_id):
    """Generate a chart showing common recommendations from AI analyses"""
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)
    
    # Get all responses for this questionnaire
    responses = Response.objects.filter(survey=questionnaire)
    
    # Get AI analyses for these responses
    analyses = AIAnalysis.objects.filter(response__in=responses)
    
    if not analyses.exists():
        return None
    
    # Extract and count recommendation keywords
    from collections import Counter
    import re
    
    # Common keywords to look for in recommendations
    keywords = [
        'therapy', 'cbt', 'medication', 'exercise', 'mindfulness', 
        'meditation', 'sleep', 'diet', 'social', 'support', 'self-care',
        'monitoring', 'follow-up', 'assessment', 'referral', 'intervention',
        'counseling', 'relaxation', 'stress management', 'coping'
    ]
    
    keyword_counts = Counter()
    
    for analysis in analyses:
        if analysis.recommendations:
            # Convert to lowercase for case-insensitive matching
            recommendations = analysis.recommendations.lower()
            
            # Count occurrences of each keyword
            for keyword in keywords:
                # Use word boundaries to match whole words
                pattern = r'\b' + re.escape(keyword) + r'\b'
                count = len(re.findall(pattern, recommendations))
                if count > 0:
                    keyword_counts[keyword] += 1
    
    # Get the top 10 keywords
    top_keywords = keyword_counts.most_common(10)
    
    if not top_keywords:
        return None
    
    # Prepare data for plotting
    keywords = [item[0].capitalize() for item in top_keywords]
    counts = [item[1] for item in top_keywords]
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    
    # Use horizontal bar chart for better readability
    bars = plt.barh(keywords, counts, color='#2196F3')
    
    # Add count labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width + 0.3, bar.get_y() + bar.get_height()/2,
                 f'{int(width)}', ha='left', va='center')
    
    plt.xlabel('Frequency', fontsize=12)
    plt.ylabel('Recommendation Keywords', fontsize=12)
    plt.title(f'Common AI Recommendations - {questionnaire.title}', fontsize=14)
    
    plt.tight_layout()
    
    # Convert to base64 for embedding in HTML
    chart_base64 = get_base64_chart(plt)
    
    return chart_base64

def generate_demographic_analysis_chart(questionnaire_id, demographic_field='patient_age'):
    """Generate a chart showing score distribution by demographic factors"""
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)
    
    # Get all responses for this questionnaire with scores
    responses = Response.objects.filter(
        survey=questionnaire
    ).exclude(score__isnull=True)
    
    if not responses.exists():
        return None
    
    if demographic_field == 'patient_age':
        # Create age groups
        age_groups = {
            '18-25': (18, 25),
            '26-35': (26, 35),
            '36-45': (36, 45),
            '46-55': (46, 55),
            '56+': (56, 120)
        }
        
        # Group responses by age
        grouped_data = {}
        for group_name, (min_age, max_age) in age_groups.items():
            group_responses = responses.filter(
                patient_age__gte=min_age,
                patient_age__lte=max_age
            )
            if group_responses.exists():
                scores = [r.score for r in group_responses if r.score is not None]
                if scores:
                    grouped_data[group_name] = scores
        
        # Create box plot
        plt.figure(figsize=(12, 6))
        
        # Prepare data for box plot
        data = []
        labels = []
        for group_name, scores in grouped_data.items():
            if scores:
                data.append(scores)
                labels.append(f"{group_name}\n(n={len(scores)})")
        
        if not data:
            return None
        
        # Create the box plot
        box = plt.boxplot(data, patch_artist=True, labels=labels)
        
        # Color the boxes
        colors = ['#2196F3', '#4CAF50', '#FFC107', '#F44336', '#9C27B0']
        for patch, color in zip(box['boxes'], colors[:len(data)]):
            patch.set_facecolor(color)
        
        plt.title(f'Score Distribution by Age Group - {questionnaire.title}', fontsize=14)
        plt.ylabel('Score', fontsize=12)
        plt.grid(axis='y', alpha=0.3)
    
    elif demographic_field == 'patient_gender':
        # Group responses by gender
        gender_groups = responses.values('patient_gender').annotate(
            avg_score=Avg('score'),
            count=Count('id')
        ).order_by('patient_gender')
        
        if not gender_groups:
            return None
        
        # Prepare data for plotting
        genders = []
        avg_scores = []
        counts = []
        
        for group in gender_groups:
            gender = group['patient_gender']
            if gender:
                # Capitalize and format gender label
                if gender == 'prefer_not_to_say':
                    gender_label = 'Prefer Not to Say'
                else:
                    gender_label = gender.capitalize()
                
                genders.append(f"{gender_label}\n(n={group['count']})")
                avg_scores.append(group['avg_score'])
                counts.append(group['count'])
        
        if not genders:
            return None
        
        # Create the chart
        plt.figure(figsize=(10, 6))
        
        # Create bar chart
        bars = plt.bar(genders, avg_scores, color=['#2196F3', '#F44336', '#4CAF50', '#9C27B0'])
        
        # Add score labels
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                     f'{height:.1f}', ha='center', va='bottom')
        
        plt.title(f'Average Score by Gender - {questionnaire.title}', fontsize=14)
        plt.ylabel('Average Score', fontsize=12)
        plt.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Convert to base64 for embedding in HTML
    chart_base64 = get_base64_chart(plt)
    
    return chart_base64

def generate_completion_time_chart(questionnaire_id):
    """Generate a chart showing distribution of completion times"""
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)
    
    # Get all completed responses for this questionnaire
    responses = Response.objects.filter(
        survey=questionnaire,
        status='completed',
        completion_time__isnull=False
    )
    
    if not responses.exists():
        return None
    
    # Get completion times in minutes
    completion_times = [r.completion_time / 60 for r in responses if r.completion_time]
    
    if not completion_times:
        return None
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    
    # Create histogram
    plt.hist(completion_times, bins=10, color='#2196F3', edgecolor='black', alpha=0.7)
    
    # Add labels and title
    plt.title(f'Completion Time Distribution - {questionnaire.title}', fontsize=14)
    plt.xlabel('Completion Time (minutes)', fontsize=12)
    plt.ylabel('Number of Responses', fontsize=12)
    
    # Add average line
    avg_time = sum(completion_times) / len(completion_times)
    plt.axvline(x=avg_time, color='red', linestyle='--', linewidth=2)
    plt.text(avg_time + 0.2, plt.ylim()[1] * 0.9, f'Average: {avg_time:.1f} min', 
             color='red', fontsize=10, va='center')
    
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    # Convert to base64 for embedding in HTML
    chart_base64 = get_base64_chart(plt)
    
    return chart_base64

def generate_comparative_analysis_chart(questionnaire_ids):
    """Generate a chart comparing average scores across multiple questionnaires"""
    if not questionnaire_ids or len(questionnaire_ids) < 2:
        return None
    
    # Get questionnaires
    questionnaires = Questionnaire.objects.filter(id__in=questionnaire_ids)
    
    # Prepare data for plotting
    titles = []
    avg_scores = []
    std_devs = []
    response_counts = []
    
    for questionnaire in questionnaires:
        # Get responses with scores
        responses = Response.objects.filter(
            survey=questionnaire
        ).exclude(score__isnull=True)
        
        if responses.exists():
            scores = [r.score for r in responses if r.score is not None]
            if scores:
                titles.append(questionnaire.title[:20] + "..." if len(questionnaire.title) > 20 else questionnaire.title)
                avg_scores.append(sum(scores) / len(scores))
                std_devs.append(np.std(scores))
                response_counts.append(len(scores))
    
    if not titles:
        return None
    
    # Create the chart
    plt.figure(figsize=(12, 6))
    
    # Create bar chart with error bars
    bars = plt.bar(titles, avg_scores, yerr=std_devs, capsize=10, color='#2196F3', alpha=0.7)
    
    # Add score and count labels
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + std_devs[i] + 0.5,
                 f'Avg: {avg_scores[i]:.1f}\nn={response_counts[i]}', 
                 ha='center', va='bottom', fontsize=9)
    
    # Add labels and title
    plt.title('Comparative Analysis of Average Scores', fontsize=14)
    plt.ylabel('Average Score', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    # Convert to base64 for embedding in HTML
    chart_base64 = get_base64_chart(plt)
    
    return chart_base64
