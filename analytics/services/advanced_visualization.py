import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import seaborn as sns
from io import BytesIO
import base64
from django.db.models import Count, Avg, F, Q
from feedback.models import Response, Answer
from groups.models import Organization, OrganizationMember
from surveys.models import Questionnaire, Question

class AdvancedVisualizationService:
    """
    Service for generating advanced visualizations for analytics
    """
    
    @staticmethod
    def generate_radar_chart(member, organization, questionnaire=None):
        """
        Generate a radar chart comparing a member's scores across different categories
        
        Args:
            member: OrganizationMember instance
            organization: Organization instance
            questionnaire: Optional Questionnaire instance to filter by
            
        Returns:
            dict: Chart data and image
        """
        # Get responses for this member
        responses_query = Response.objects.filter(
            user=member.user,
            survey__organization=organization,
            status='completed'
        )
        
        # Filter by questionnaire if provided
        if questionnaire:
            responses_query = responses_query.filter(survey=questionnaire)
        
        # If no responses, return empty data
        if not responses_query.exists():
            return {
                'success': False,
                'message': 'No completed responses found for this member.',
                'chart_data': None,
                'chart_image': None
            }
        
        # Get all questionnaires this member has responded to
        questionnaires = Questionnaire.objects.filter(
            pk__in=responses_query.values_list('survey', flat=True)
        )
        
        # Calculate average scores by category
        category_scores = {}
        for q in questionnaires:
            if not q.category:
                continue
                
            # Get responses for this questionnaire
            q_responses = responses_query.filter(survey=q)
            
            # Calculate average score
            avg_score = q_responses.aggregate(Avg('score'))['score__avg'] or 0
            
            # Add to category scores
            if q.category in category_scores:
                category_scores[q.category]['scores'].append(avg_score)
            else:
                category_scores[q.category] = {
                    'scores': [avg_score],
                    'display_name': q.get_category_display()
                }
        
        # Calculate average score for each category
        categories = []
        scores = []
        for category, data in category_scores.items():
            categories.append(data['display_name'])
            scores.append(sum(data['scores']) / len(data['scores']))
        
        # If no categories, return empty data
        if not categories:
            return {
                'success': False,
                'message': 'No category data found for radar chart.',
                'chart_data': None,
                'chart_image': None
            }
        
        # Create radar chart
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, polar=True)
        
        # Number of categories
        N = len(categories)
        
        # Angle of each axis
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Close the loop
        
        # Add the first point at the end to close the polygon
        scores_plot = scores.copy()
        scores_plot += scores_plot[:1]
        
        # Plot data
        ax.plot(angles, scores_plot, linewidth=2, linestyle='solid', label=member.user.get_full_name() or member.user.email)
        ax.fill(angles, scores_plot, alpha=0.25)
        
        # Set category labels
        plt.xticks(angles[:-1], categories)
        
        # Set y-axis limits
        ax.set_ylim(0, 100)
        
        # Add title
        plt.title(f"Category Scores for {member.user.get_full_name() or member.user.email}", size=15, y=1.1)
        
        # Add legend
        plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        
        # Save chart to BytesIO
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        
        # Convert to base64 for embedding in HTML
        chart_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        # Prepare chart data for JSON
        chart_data = {
            'categories': categories,
            'scores': scores
        }
        
        return {
            'success': True,
            'chart_data': chart_data,
            'chart_image': chart_image
        }
    
    @staticmethod
    def generate_heatmap(organization, questionnaire=None, time_period=30):
        """
        Generate a heatmap of response patterns
        
        Args:
            organization: Organization instance
            questionnaire: Optional Questionnaire instance to filter by
            time_period: Number of days to include (default: 30)
            
        Returns:
            dict: Chart data and image
        """
        # Get responses for this organization
        responses_query = Response.objects.filter(
            survey__organization=organization,
            status='completed'
        )
        
        # Filter by questionnaire if provided
        if questionnaire:
            responses_query = responses_query.filter(survey=questionnaire)
        
        # Filter by time period
        from django.utils import timezone
        from datetime import timedelta
        start_date = timezone.now() - timedelta(days=time_period)
        responses_query = responses_query.filter(created_at__gte=start_date)
        
        # If no responses, return empty data
        if not responses_query.exists():
            return {
                'success': False,
                'message': 'No completed responses found for the selected criteria.',
                'chart_data': None,
                'chart_image': None
            }
        
        # Get all members who have responded
        member_ids = responses_query.values_list('user', flat=True).distinct()
        members = OrganizationMember.objects.filter(
            organization=organization,
            user__in=member_ids
        ).select_related('user')
        
        # Get all questionnaires that have been responded to
        questionnaire_ids = responses_query.values_list('survey', flat=True).distinct()
        questionnaires = Questionnaire.objects.filter(pk__in=questionnaire_ids)
        
        # Create a matrix of response counts
        matrix = []
        member_labels = []
        questionnaire_labels = []
        
        for member in members:
            member_name = member.user.get_full_name() or member.user.email
            member_labels.append(member_name)
            
            row = []
            for q in questionnaires:
                count = responses_query.filter(user=member.user, survey=q).count()
                row.append(count)
                
                if q.title not in questionnaire_labels:
                    questionnaire_labels.append(q.title)
            
            matrix.append(row)
        
        # If no data, return empty data
        if not matrix or not member_labels or not questionnaire_labels:
            return {
                'success': False,
                'message': 'Insufficient data for heatmap.',
                'chart_data': None,
                'chart_image': None
            }
        
        # Convert to numpy array
        matrix = np.array(matrix)
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.heatmap(matrix, annot=True, fmt="d", cmap="YlGnBu", 
                   xticklabels=questionnaire_labels, yticklabels=member_labels)
        
        plt.title(f"Response Counts by Member and Questionnaire (Last {time_period} days)")
        plt.ylabel("Member")
        plt.xlabel("Questionnaire")
        plt.xticks(rotation=45, ha='right')
        
        # Save chart to BytesIO
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        
        # Convert to base64 for embedding in HTML
        chart_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        # Prepare chart data for JSON
        chart_data = {
            'member_labels': member_labels,
            'questionnaire_labels': questionnaire_labels,
            'matrix': matrix.tolist()
        }
        
        return {
            'success': True,
            'chart_data': chart_data,
            'chart_image': chart_image
        }
    
    @staticmethod
    def generate_bubble_chart(organization, questionnaire=None):
        """
        Generate a bubble chart showing score, completion time, and risk level
        
        Args:
            organization: Organization instance
            questionnaire: Optional Questionnaire instance to filter by
            
        Returns:
            dict: Chart data and image
        """
        # Get responses for this organization
        responses_query = Response.objects.filter(
            survey__organization=organization,
            status='completed',
            score__isnull=False,
            completion_time__isnull=False
        )
        
        # Filter by questionnaire if provided
        if questionnaire:
            responses_query = responses_query.filter(survey=questionnaire)
        
        # If no responses, return empty data
        if not responses_query.exists():
            return {
                'success': False,
                'message': 'No completed responses with score and completion time found.',
                'chart_data': None,
                'chart_image': None
            }
        
        # Extract data for bubble chart
        data = []
        for response in responses_query:
            # Skip responses with missing data
            if response.score is None or response.completion_time is None:
                continue
                
            # Get member name
            member_name = "Anonymous"
            if response.user:
                member_name = response.user.get_full_name() or response.user.email
            
            # Get risk level color
            if response.risk_level == 'high':
                color = 'red'
            elif response.risk_level == 'medium':
                color = 'orange'
            else:
                color = 'green'
            
            # Add to data
            data.append({
                'x': response.score,
                'y': response.completion_time / 60,  # Convert seconds to minutes
                'size': 100,  # Fixed size for now
                'color': color,
                'name': member_name,
                'questionnaire': response.survey.title,
                'date': response.created_at.strftime('%Y-%m-%d'),
                'risk_level': response.get_risk_level_display()
            })
        
        # If no data, return empty data
        if not data:
            return {
                'success': False,
                'message': 'Insufficient data for bubble chart.',
                'chart_data': None,
                'chart_image': None
            }
        
        # Create bubble chart
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Plot bubbles
        for item in data:
            ax.scatter(item['x'], item['y'], s=item['size'], c=item['color'], alpha=0.6, edgecolors='w')
        
        # Add labels and title
        plt.title("Score vs. Completion Time by Risk Level")
        plt.xlabel("Score")
        plt.ylabel("Completion Time (minutes)")
        
        # Add legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10, label='Low Risk'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=10, label='Medium Risk'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='High Risk')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        # Save chart to BytesIO
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        
        # Convert to base64 for embedding in HTML
        chart_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        # Prepare chart data for JSON
        chart_data = {
            'data': data
        }
        
        return {
            'success': True,
            'chart_data': chart_data,
            'chart_image': chart_image
        }
    
    @staticmethod
    def generate_timeline_chart(member, organization, time_period=90):
        """
        Generate a timeline chart showing scores over time
        
        Args:
            member: OrganizationMember instance
            organization: Organization instance
            time_period: Number of days to include (default: 90)
            
        Returns:
            dict: Chart data and image
        """
        # Get responses for this member
        responses_query = Response.objects.filter(
            user=member.user,
            survey__organization=organization,
            status='completed',
            score__isnull=False
        ).order_by('created_at')
        
        # Filter by time period
        from django.utils import timezone
        from datetime import timedelta
        start_date = timezone.now() - timedelta(days=time_period)
        responses_query = responses_query.filter(created_at__gte=start_date)
        
        # If no responses, return empty data
        if not responses_query.exists():
            return {
                'success': False,
                'message': 'No completed responses found for this member in the selected time period.',
                'chart_data': None,
                'chart_image': None
            }
        
        # Extract data for timeline chart
        dates = []
        scores = []
        questionnaires = []
        
        for response in responses_query:
            dates.append(response.created_at)
            scores.append(response.score)
            questionnaires.append(response.survey.title)
        
        # Create timeline chart
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot scores over time
        ax.plot(dates, scores, 'o-', linewidth=2, markersize=8)
        
        # Add labels and title
        plt.title(f"Score Timeline for {member.user.get_full_name() or member.user.email}")
        plt.xlabel("Date")
        plt.ylabel("Score")
        
        # Format x-axis dates
        fig.autofmt_xdate()
        
        # Add grid
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Save chart to BytesIO
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        
        # Convert to base64 for embedding in HTML
        chart_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        # Prepare chart data for JSON
        chart_data = {
            'dates': [d.strftime('%Y-%m-%d') for d in dates],
            'scores': scores,
            'questionnaires': questionnaires
        }
        
        return {
            'success': True,
            'chart_data': chart_data,
            'chart_image': chart_image
        }
