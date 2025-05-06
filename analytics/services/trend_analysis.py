import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import seaborn as sns
from io import BytesIO
import base64
from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone
from datetime import timedelta
from feedback.models import Response, Answer
from groups.models import Organization, OrganizationMember
from surveys.models import Questionnaire, Question

class TrendAnalysisService:
    """
    Service for analyzing trends in responses over time
    """
    
    @staticmethod
    def analyze_member_trends(member, organization, time_period=90):
        """
        Analyze trends in a member's responses over time
        
        Args:
            member: OrganizationMember instance
            organization: Organization instance
            time_period: Number of days to include (default: 90)
            
        Returns:
            dict: Analysis results
        """
        # Get responses for this member within the time period
        start_date = timezone.now() - timedelta(days=time_period)
        responses = Response.objects.filter(
            user=member.user,
            survey__organization=organization,
            status='completed',
            created_at__gte=start_date
        ).order_by('created_at')
        
        # If no responses, return empty analysis
        if not responses.exists():
            return {
                'success': False,
                'message': 'No completed responses found for this member in the selected time period.',
                'trends': [],
                'charts': {}
            }
        
        # Convert responses to DataFrame for analysis
        response_data = []
        for response in responses:
            response_data.append({
                'id': str(response.id),
                'survey_title': response.survey.title if hasattr(response, 'survey') else 'Unknown',
                'survey_category': response.survey.get_category_display() if hasattr(response, 'survey') and hasattr(response.survey, 'get_category_display') else 'Unknown',
                'score': response.score,
                'risk_level': response.risk_level,
                'created_at': response.created_at,
                'completion_time': response.completion_time
            })
        
        df = pd.DataFrame(response_data)
        
        # If DataFrame is empty, return empty analysis
        if df.empty:
            return {
                'success': False,
                'message': 'No valid data found for trend analysis.',
                'trends': [],
                'charts': {}
            }
        
        # Perform trend analysis
        trends = []
        charts = {}
        
        # 1. Score Trend Analysis
        if 'score' in df.columns and not df['score'].isna().all():
            # Calculate rolling average
            df = df.sort_values('created_at')
            df['date'] = df['created_at'].dt.date
            
            # Group by date and calculate average score
            score_by_date = df.groupby('date')['score'].mean().reset_index()
            
            # Calculate trend line
            if len(score_by_date) > 1:
                x = np.arange(len(score_by_date))
                y = score_by_date['score'].values
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                
                # Determine trend direction
                trend_direction = "improving" if z[0] > 0 else "declining"
                trend_strength = abs(z[0])
                
                # Add trend to results
                trends.append({
                    'type': 'score',
                    'direction': trend_direction,
                    'strength': float(trend_strength),
                    'description': f"Score is {trend_direction} over time",
                    'details': f"Average score has been {trend_direction} at a rate of {trend_strength:.2f} points per response."
                })
                
                # Create score trend chart
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(score_by_date['date'], score_by_date['score'], 'o-', label='Average Score')
                ax.plot(score_by_date['date'], p(x), '--', label='Trend Line')
                ax.set_title(f"Score Trend Over Time")
                ax.set_xlabel("Date")
                ax.set_ylabel("Score")
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.legend()
                
                # Format x-axis dates
                fig.autofmt_xdate()
                
                # Save chart to BytesIO
                buffer = BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                
                # Convert to base64 for embedding in HTML
                charts['score_trend'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()
        
        # 2. Risk Level Analysis
        if 'risk_level' in df.columns:
            # Count occurrences of each risk level
            risk_counts = df['risk_level'].value_counts()
            
            # Check if risk levels are changing over time
            df = df.sort_values('created_at')
            df['risk_numeric'] = df['risk_level'].map({
                'low': 1,
                'medium': 2,
                'high': 3,
                'critical': 4,
                'unknown': 0
            })
            
            # Calculate rolling average of risk level
            if len(df) > 1 and not df['risk_numeric'].isna().all():
                # Group by date and calculate average risk level
                risk_by_date = df.groupby('date')['risk_numeric'].mean().reset_index()
                
                # Calculate trend line
                if len(risk_by_date) > 1:
                    x = np.arange(len(risk_by_date))
                    y = risk_by_date['risk_numeric'].values
                    z = np.polyfit(x, y, 1)
                    p = np.poly1d(z)
                    
                    # Determine trend direction
                    trend_direction = "increasing" if z[0] > 0 else "decreasing"
                    trend_strength = abs(z[0])
                    
                    # Add trend to results
                    trends.append({
                        'type': 'risk_level',
                        'direction': trend_direction,
                        'strength': float(trend_strength),
                        'description': f"Risk level is {trend_direction} over time",
                        'details': f"Average risk level has been {trend_direction} at a rate of {trend_strength:.2f} per response."
                    })
                    
                    # Create risk level trend chart
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(risk_by_date['date'], risk_by_date['risk_numeric'], 'o-', label='Average Risk Level')
                    ax.plot(risk_by_date['date'], p(x), '--', label='Trend Line')
                    ax.set_title(f"Risk Level Trend Over Time")
                    ax.set_xlabel("Date")
                    ax.set_ylabel("Risk Level (1=Low, 4=Critical)")
                    ax.grid(True, linestyle='--', alpha=0.7)
                    ax.legend()
                    
                    # Format x-axis dates
                    fig.autofmt_xdate()
                    
                    # Save chart to BytesIO
                    buffer = BytesIO()
                    plt.tight_layout()
                    plt.savefig(buffer, format='png', dpi=100)
                    buffer.seek(0)
                    
                    # Convert to base64 for embedding in HTML
                    charts['risk_trend'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    plt.close()
            
            # Create risk level distribution chart
            if not risk_counts.empty:
                fig, ax = plt.subplots(figsize=(8, 6))
                colors = ['green', 'yellow', 'red', 'darkred', 'gray']
                risk_counts.plot(kind='bar', ax=ax, color=colors)
                ax.set_title(f"Risk Level Distribution")
                ax.set_xlabel("Risk Level")
                ax.set_ylabel("Count")
                
                # Save chart to BytesIO
                buffer = BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                
                # Convert to base64 for embedding in HTML
                charts['risk_distribution'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()
        
        # 3. Completion Time Analysis
        if 'completion_time' in df.columns and not df['completion_time'].isna().all():
            # Convert to minutes for better readability
            df['completion_minutes'] = df['completion_time'] / 60
            
            # Group by date and calculate average completion time
            time_by_date = df.groupby('date')['completion_minutes'].mean().reset_index()
            
            # Calculate trend line
            if len(time_by_date) > 1:
                x = np.arange(len(time_by_date))
                y = time_by_date['completion_minutes'].values
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                
                # Determine trend direction
                trend_direction = "increasing" if z[0] > 0 else "decreasing"
                trend_strength = abs(z[0])
                
                # Add trend to results
                trends.append({
                    'type': 'completion_time',
                    'direction': trend_direction,
                    'strength': float(trend_strength),
                    'description': f"Completion time is {trend_direction} over time",
                    'details': f"Average completion time has been {trend_direction} at a rate of {trend_strength:.2f} minutes per response."
                })
                
                # Create completion time trend chart
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(time_by_date['date'], time_by_date['completion_minutes'], 'o-', label='Average Completion Time')
                ax.plot(time_by_date['date'], p(x), '--', label='Trend Line')
                ax.set_title(f"Completion Time Trend Over Time")
                ax.set_xlabel("Date")
                ax.set_ylabel("Completion Time (minutes)")
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.legend()
                
                # Format x-axis dates
                fig.autofmt_xdate()
                
                # Save chart to BytesIO
                buffer = BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                
                # Convert to base64 for embedding in HTML
                charts['time_trend'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()
        
        # 4. Survey Category Analysis
        if 'survey_category' in df.columns and not df['survey_category'].isna().all():
            # Group by category and calculate average score
            category_scores = df.groupby('survey_category')['score'].mean().reset_index()
            
            # Create category score chart
            if not category_scores.empty and len(category_scores) > 1:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(x='survey_category', y='score', data=category_scores, ax=ax)
                ax.set_title(f"Average Score by Category")
                ax.set_xlabel("Category")
                ax.set_ylabel("Average Score")
                
                # Rotate x-axis labels if needed
                plt.xticks(rotation=45, ha='right')
                
                # Save chart to BytesIO
                buffer = BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                
                # Convert to base64 for embedding in HTML
                charts['category_scores'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()
        
        # Return the analysis results
        return {
            'success': True,
            'trends': trends,
            'charts': charts
        }
    
    @staticmethod
    def analyze_organization_trends(organization, time_period=90):
        """
        Analyze trends in an organization's responses over time
        
        Args:
            organization: Organization instance
            time_period: Number of days to include (default: 90)
            
        Returns:
            dict: Analysis results
        """
        # Get responses for this organization within the time period
        start_date = timezone.now() - timedelta(days=time_period)
        responses = Response.objects.filter(
            survey__organization=organization,
            status='completed',
            created_at__gte=start_date
        ).order_by('created_at')
        
        # If no responses, return empty analysis
        if not responses.exists():
            return {
                'success': False,
                'message': 'No completed responses found for this organization in the selected time period.',
                'trends': [],
                'charts': {}
            }
        
        # Convert responses to DataFrame for analysis
        response_data = []
        for response in responses:
            response_data.append({
                'id': str(response.id),
                'survey_title': response.survey.title if hasattr(response, 'survey') else 'Unknown',
                'survey_category': response.survey.get_category_display() if hasattr(response, 'survey') and hasattr(response.survey, 'get_category_display') else 'Unknown',
                'score': response.score,
                'risk_level': response.risk_level,
                'created_at': response.created_at,
                'user_id': response.user.id if response.user else None,
                'user_name': response.user.get_full_name() if response.user else 'Anonymous'
            })
        
        df = pd.DataFrame(response_data)
        
        # If DataFrame is empty, return empty analysis
        if df.empty:
            return {
                'success': False,
                'message': 'No valid data found for trend analysis.',
                'trends': [],
                'charts': {}
            }
        
        # Perform trend analysis
        trends = []
        charts = {}
        
        # 1. Response Volume Analysis
        df['date'] = df['created_at'].dt.date
        responses_by_date = df.groupby('date').size().reset_index(name='count')
        
        # Calculate trend line
        if len(responses_by_date) > 1:
            x = np.arange(len(responses_by_date))
            y = responses_by_date['count'].values
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            
            # Determine trend direction
            trend_direction = "increasing" if z[0] > 0 else "decreasing"
            trend_strength = abs(z[0])
            
            # Add trend to results
            trends.append({
                'type': 'response_volume',
                'direction': trend_direction,
                'strength': float(trend_strength),
                'description': f"Response volume is {trend_direction} over time",
                'details': f"The number of responses has been {trend_direction} at a rate of {trend_strength:.2f} per day."
            })
            
            # Create response volume chart
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(responses_by_date['date'], responses_by_date['count'], 'o-', label='Response Count')
            ax.plot(responses_by_date['date'], p(x), '--', label='Trend Line')
            ax.set_title(f"Response Volume Over Time")
            ax.set_xlabel("Date")
            ax.set_ylabel("Number of Responses")
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.legend()
            
            # Format x-axis dates
            fig.autofmt_xdate()
            
            # Save chart to BytesIO
            buffer = BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            
            # Convert to base64 for embedding in HTML
            charts['volume_trend'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
        
        # 2. Average Score Analysis
        if 'score' in df.columns and not df['score'].isna().all():
            # Group by date and calculate average score
            score_by_date = df.groupby('date')['score'].mean().reset_index()
            
            # Calculate trend line
            if len(score_by_date) > 1:
                x = np.arange(len(score_by_date))
                y = score_by_date['score'].values
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                
                # Determine trend direction
                trend_direction = "improving" if z[0] > 0 else "declining"
                trend_strength = abs(z[0])
                
                # Add trend to results
                trends.append({
                    'type': 'score',
                    'direction': trend_direction,
                    'strength': float(trend_strength),
                    'description': f"Average score is {trend_direction} over time",
                    'details': f"The average score has been {trend_direction} at a rate of {trend_strength:.2f} points per day."
                })
                
                # Create score trend chart
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(score_by_date['date'], score_by_date['score'], 'o-', label='Average Score')
                ax.plot(score_by_date['date'], p(x), '--', label='Trend Line')
                ax.set_title(f"Average Score Trend Over Time")
                ax.set_xlabel("Date")
                ax.set_ylabel("Average Score")
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.legend()
                
                # Format x-axis dates
                fig.autofmt_xdate()
                
                # Save chart to BytesIO
                buffer = BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                
                # Convert to base64 for embedding in HTML
                charts['score_trend'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()
        
        # 3. Risk Level Analysis
        if 'risk_level' in df.columns:
            # Count occurrences of each risk level
            risk_counts = df['risk_level'].value_counts()
            
            # Check if risk levels are changing over time
            df['risk_numeric'] = df['risk_level'].map({
                'low': 1,
                'medium': 2,
                'high': 3,
                'critical': 4,
                'unknown': 0
            })
            
            # Group by date and calculate average risk level
            risk_by_date = df.groupby('date')['risk_numeric'].mean().reset_index()
            
            # Calculate trend line
            if len(risk_by_date) > 1:
                x = np.arange(len(risk_by_date))
                y = risk_by_date['risk_numeric'].values
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                
                # Determine trend direction
                trend_direction = "increasing" if z[0] > 0 else "decreasing"
                trend_strength = abs(z[0])
                
                # Add trend to results
                trends.append({
                    'type': 'risk_level',
                    'direction': trend_direction,
                    'strength': float(trend_strength),
                    'description': f"Average risk level is {trend_direction} over time",
                    'details': f"The average risk level has been {trend_direction} at a rate of {trend_strength:.2f} per day."
                })
                
                # Create risk level trend chart
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(risk_by_date['date'], risk_by_date['risk_numeric'], 'o-', label='Average Risk Level')
                ax.plot(risk_by_date['date'], p(x), '--', label='Trend Line')
                ax.set_title(f"Risk Level Trend Over Time")
                ax.set_xlabel("Date")
                ax.set_ylabel("Risk Level (1=Low, 4=Critical)")
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.legend()
                
                # Format x-axis dates
                fig.autofmt_xdate()
                
                # Save chart to BytesIO
                buffer = BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                
                # Convert to base64 for embedding in HTML
                charts['risk_trend'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()
            
            # Create risk level distribution chart
            if not risk_counts.empty:
                fig, ax = plt.subplots(figsize=(8, 6))
                colors = ['green', 'yellow', 'red', 'darkred', 'gray']
                risk_counts.plot(kind='bar', ax=ax, color=colors)
                ax.set_title(f"Risk Level Distribution")
                ax.set_xlabel("Risk Level")
                ax.set_ylabel("Count")
                
                # Save chart to BytesIO
                buffer = BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                
                # Convert to base64 for embedding in HTML
                charts['risk_distribution'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()
        
        # 4. User Participation Analysis
        if 'user_id' in df.columns:
            # Count responses by user
            user_counts = df.groupby('user_name').size().reset_index(name='count')
            user_counts = user_counts.sort_values('count', ascending=False).head(10)
            
            # Create user participation chart
            if not user_counts.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(x='count', y='user_name', data=user_counts, ax=ax)
                ax.set_title(f"Top 10 Users by Response Count")
                ax.set_xlabel("Number of Responses")
                ax.set_ylabel("User")
                
                # Save chart to BytesIO
                buffer = BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                
                # Convert to base64 for embedding in HTML
                charts['user_participation'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()
        
        # 5. Survey Category Analysis
        if 'survey_category' in df.columns and not df['survey_category'].isna().all():
            # Count responses by category
            category_counts = df.groupby('survey_category').size().reset_index(name='count')
            
            # Create category distribution chart
            if not category_counts.empty and len(category_counts) > 1:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(x='survey_category', y='count', data=category_counts, ax=ax)
                ax.set_title(f"Response Count by Category")
                ax.set_xlabel("Category")
                ax.set_ylabel("Number of Responses")
                
                # Rotate x-axis labels if needed
                plt.xticks(rotation=45, ha='right')
                
                # Save chart to BytesIO
                buffer = BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                
                # Convert to base64 for embedding in HTML
                charts['category_distribution'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()
            
            # Group by category and calculate average score
            category_scores = df.groupby('survey_category')['score'].mean().reset_index()
            
            # Create category score chart
            if not category_scores.empty and len(category_scores) > 1:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(x='survey_category', y='score', data=category_scores, ax=ax)
                ax.set_title(f"Average Score by Category")
                ax.set_xlabel("Category")
                ax.set_ylabel("Average Score")
                
                # Rotate x-axis labels if needed
                plt.xticks(rotation=45, ha='right')
                
                # Save chart to BytesIO
                buffer = BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                
                # Convert to base64 for embedding in HTML
                charts['category_scores'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()
        
        # Return the analysis results
        return {
            'success': True,
            'trends': trends,
            'charts': charts
        }
