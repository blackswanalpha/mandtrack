"""
Utility functions for generating response-specific visualizations.
"""
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from io import BytesIO
import base64
from django.db.models import Count, Avg
from feedback.models import Response, Answer, AIAnalysis
from surveys.models import Question, QuestionChoice
import re
import json
from collections import Counter
from textblob import TextBlob

def get_base64_chart(plt):
    """Convert matplotlib plot to base64 string for embedding in HTML"""
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_png).decode('utf-8')

def generate_response_answer_distribution(response_id):
    """
    Generate a chart showing the distribution of answers for a specific response
    compared to average scores for each question
    """
    # Get the response and its answers
    response = Response.objects.get(id=response_id)
    questionnaire = response.survey
    
    # Get all questions for this questionnaire
    questions = Question.objects.filter(questionnaire=questionnaire).order_by('order')
    
    # Get all responses for this questionnaire to calculate averages
    all_responses = Response.objects.filter(survey=questionnaire)
    
    # Prepare data for plotting
    question_labels = []
    response_scores = []
    avg_scores = []
    
    for question in questions:
        if question.is_scored:
            # Get this response's answer for this question
            try:
                answer = Answer.objects.get(response=response, question=question)
                if answer.score is not None:
                    response_scores.append(answer.score)
                    question_labels.append(f"Q{question.order}")
                    
                    # Calculate average score for this question across all responses
                    avg_score = Answer.objects.filter(
                        question=question, 
                        response__in=all_responses
                    ).exclude(score__isnull=True).aggregate(Avg('score'))['score__avg'] or 0
                    
                    avg_scores.append(avg_score)
            except Answer.DoesNotExist:
                continue
    
    if not question_labels:
        return None
    
    # Create the chart
    plt.figure(figsize=(12, 6))
    
    x = np.arange(len(question_labels))
    width = 0.35
    
    plt.bar(x - width/2, response_scores, width, label='This Response', color='#2196F3')
    plt.bar(x + width/2, avg_scores, width, label='Average', color='#FF9800')
    
    plt.xlabel('Questions', fontsize=12)
    plt.ylabel('Score', fontsize=12)
    plt.title('Response Scores vs. Average Scores', fontsize=14)
    plt.xticks(x, question_labels)
    plt.legend()
    
    plt.tight_layout()
    
    # Convert to base64 for embedding in HTML
    chart_base64 = get_base64_chart(plt)
    
    return chart_base64

def generate_response_sentiment_analysis(response_id):
    """
    Generate a chart showing sentiment analysis of text answers
    """
    # Get the response and its answers
    response = Response.objects.get(id=response_id)
    
    # Get text answers
    text_answers = Answer.objects.filter(
        response=response, 
        text_answer__isnull=False
    ).exclude(text_answer='')
    
    if not text_answers.exists():
        return None
    
    # Analyze sentiment for each text answer
    sentiments = []
    labels = []
    
    for answer in text_answers:
        if answer.text_answer and len(answer.text_answer.strip()) > 0:
            # Use TextBlob for sentiment analysis
            blob = TextBlob(answer.text_answer)
            sentiment = blob.sentiment.polarity  # Range: -1 (negative) to 1 (positive)
            
            sentiments.append(sentiment)
            labels.append(f"Q{answer.question.order}")
    
    if not sentiments:
        return None
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    
    # Create a colormap based on sentiment values
    colors = ['#F44336' if s < -0.25 else '#FFC107' if s < 0.25 else '#4CAF50' for s in sentiments]
    
    plt.bar(labels, sentiments, color=colors)
    plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    
    plt.xlabel('Questions', fontsize=12)
    plt.ylabel('Sentiment (-1 to 1)', fontsize=12)
    plt.title('Sentiment Analysis of Text Answers', fontsize=14)
    
    # Add a legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#F44336', label='Negative'),
        Patch(facecolor='#FFC107', label='Neutral'),
        Patch(facecolor='#4CAF50', label='Positive')
    ]
    plt.legend(handles=legend_elements)
    
    plt.tight_layout()
    
    # Convert to base64 for embedding in HTML
    chart_base64 = get_base64_chart(plt)
    
    return chart_base64

def generate_response_completion_time_comparison(response_id):
    """
    Generate a chart comparing this response's completion time with others
    """
    # Get the response
    response = Response.objects.get(id=response_id)
    questionnaire = response.survey
    
    # Check if completion time exists
    if not response.completion_time:
        return None
    
    # Get completion times for all responses to this questionnaire
    all_responses = Response.objects.filter(
        survey=questionnaire, 
        completion_time__isnull=False
    )
    
    completion_times = [r.completion_time / 60 for r in all_responses]  # Convert to minutes
    
    if not completion_times:
        return None
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    
    # Create histogram
    plt.hist(completion_times, bins=10, alpha=0.7, color='#2196F3', edgecolor='black')
    
    # Add a line for this response's completion time
    this_completion_time = response.completion_time / 60
    plt.axvline(x=this_completion_time, color='red', linestyle='--', linewidth=2)
    plt.text(this_completion_time + 0.1, plt.ylim()[1] * 0.9, 'This Response', 
             color='red', fontsize=12, va='center')
    
    # Add average line
    avg_time = sum(completion_times) / len(completion_times)
    plt.axvline(x=avg_time, color='green', linestyle='--', linewidth=2)
    plt.text(avg_time + 0.1, plt.ylim()[1] * 0.8, f'Average: {avg_time:.1f} min', 
             color='green', fontsize=12, va='center')
    
    # Add labels and title
    plt.title('Completion Time Comparison', fontsize=14)
    plt.xlabel('Completion Time (minutes)', fontsize=12)
    plt.ylabel('Number of Responses', fontsize=12)
    
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    # Convert to base64 for embedding in HTML
    chart_base64 = get_base64_chart(plt)
    
    return chart_base64

def extract_keywords_from_analysis(ai_analysis):
    """
    Extract keywords from AI analysis text
    """
    if not ai_analysis:
        return None
    
    # Combine all text fields
    all_text = ' '.join([
        ai_analysis.summary or '',
        ai_analysis.detailed_analysis or '',
        ai_analysis.recommendations or ''
    ])
    
    # Extract key phrases and insights
    insights = []
    if ai_analysis.insights and 'key_points' in ai_analysis.insights:
        insights = ai_analysis.insights['key_points']
    
    # Common English stop words to filter out
    stop_words = set([
        'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what', 'when',
        'where', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'some',
        'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
        'can', 'will', 'just', 'should', 'now', 'to', 'of', 'in', 'for', 'on', 'with',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
        'do', 'does', 'did', 'doing', 'would', 'could', 'should', 'may', 'might', 'must',
        'this', 'that', 'these', 'those', 'there', 'their', 'they', 'it', 'its', 'from'
    ])
    
    # Extract words from all text
    words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
    words = [word for word in words if word not in stop_words]
    
    # Count word frequencies
    word_counts = Counter(words)
    
    # Get top keywords
    top_keywords = word_counts.most_common(10)
    
    return top_keywords

def generate_ai_keywords_chart(response_id):
    """
    Generate a chart showing top keywords from AI analysis
    """
    # Get the response and its AI analysis
    response = Response.objects.get(id=response_id)
    
    try:
        ai_analysis = AIAnalysis.objects.get(response=response)
    except AIAnalysis.DoesNotExist:
        return None
    
    # Extract keywords
    top_keywords = extract_keywords_from_analysis(ai_analysis)
    
    if not top_keywords:
        return None
    
    # Prepare data for plotting
    keywords = [item[0].capitalize() for item in top_keywords]
    counts = [item[1] for item in top_keywords]
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    
    # Use horizontal bar chart for better readability
    y_pos = np.arange(len(keywords))
    plt.barh(y_pos, counts, color='#673AB7')
    plt.yticks(y_pos, keywords)
    
    # Add count labels
    for i, count in enumerate(counts):
        plt.text(count + 0.1, i, str(count), va='center')
    
    # Add labels and title
    plt.title('Top Keywords in AI Analysis', fontsize=14)
    plt.xlabel('Frequency', fontsize=12)
    
    plt.tight_layout()
    
    # Convert to base64 for embedding in HTML
    chart_base64 = get_base64_chart(plt)
    
    return chart_base64

def generate_response_radar_chart(response_id):
    """
    Generate a radar chart showing response scores across different categories
    """
    # Get the response and its answers
    response = Response.objects.get(id=response_id)
    questionnaire = response.survey
    
    # Get all questions for this questionnaire
    questions = Question.objects.filter(questionnaire=questionnaire).order_by('order')
    
    # Group questions by category
    categories = {}
    for question in questions:
        if question.is_scored:
            category = question.category or 'General'
            if category not in categories:
                categories[category] = {'questions': [], 'score': 0, 'count': 0}
            categories[category]['questions'].append(question)
    
    # Calculate average score for each category
    for category, data in categories.items():
        total_score = 0
        count = 0
        for question in data['questions']:
            try:
                answer = Answer.objects.get(response=response, question=question)
                if answer.score is not None:
                    total_score += answer.score
                    count += 1
            except Answer.DoesNotExist:
                continue
        
        if count > 0:
            data['score'] = total_score / count
            data['count'] = count
    
    # Filter out categories with no scores
    categories = {k: v for k, v in categories.items() if v['count'] > 0}
    
    if not categories:
        return None
    
    # Prepare data for radar chart
    category_names = list(categories.keys())
    scores = [categories[cat]['score'] for cat in category_names]
    
    # Create the radar chart
    plt.figure(figsize=(10, 8))
    
    # Number of variables
    N = len(category_names)
    
    # What will be the angle of each axis in the plot
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Close the loop
    
    # Add the first point again to close the loop
    scores += scores[:1]
    
    # Set up the plot
    ax = plt.subplot(111, polar=True)
    
    # Draw one axis per variable and add labels
    plt.xticks(angles[:-1], category_names, size=12)
    
    # Draw the chart
    ax.plot(angles, scores, linewidth=2, linestyle='solid', color='#2196F3')
    ax.fill(angles, scores, alpha=0.25, color='#2196F3')
    
    # Add a title
    plt.title('Response Scores by Category', size=15, y=1.1)
    
    # Convert to base64 for embedding in HTML
    chart_base64 = get_base64_chart(plt)
    
    return chart_base64
