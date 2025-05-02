"""
Enhanced service for interacting with Google's Gemini API for more sophisticated analysis.
"""
import json
import logging
import requests
from django.conf import settings
from django.utils import timezone
import google.generativeai as genai
from typing import Dict, Any, List, Optional

# Set up logger
logger = logging.getLogger(__name__)

class EnhancedGeminiService:
    """
    Enhanced service for interacting with Google's Gemini API
    """

    def __init__(self, api_key=None):
        """
        Initialize the Gemini service with the API key
        """
        self.api_key = api_key or settings.GEMINI_API_KEY
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Define domain-specific prompts
        self.domain_prompts = {
            'depression': {
                'expertise': 'clinical psychology with specialization in depression assessment',
                'context': 'Depression is characterized by persistent sadness, loss of interest in activities, and various physical and cognitive symptoms that affect daily functioning.',
                'assessment_focus': 'Look for patterns related to mood, energy levels, sleep disturbances, concentration issues, and thoughts of self-harm.',
                'scoring_interpretation': 'PHQ-9 scores: 0-4 minimal, 5-9 mild, 10-14 moderate, 15-19 moderately severe, 20-27 severe depression.'
            },
            'anxiety': {
                'expertise': 'clinical psychology with specialization in anxiety disorders',
                'context': 'Anxiety disorders involve excessive worry, fear, and related behavioral disturbances that interfere with daily activities.',
                'assessment_focus': 'Look for patterns related to excessive worry, restlessness, fatigue, concentration problems, irritability, muscle tension, and sleep disturbances.',
                'scoring_interpretation': 'GAD-7 scores: 0-4 minimal, 5-9 mild, 10-14 moderate, 15-21 severe anxiety.'
            },
            'stress': {
                'expertise': 'health psychology with specialization in stress management',
                'context': 'Stress is the body\'s response to demands or threats, which can be acute or chronic, and affects physical and mental health.',
                'assessment_focus': 'Look for patterns related to perceived control, coping abilities, emotional responses to challenges, and physical manifestations of stress.',
                'scoring_interpretation': 'PSS-10 scores: 0-13 low, 14-26 moderate, 27-40 high perceived stress.'
            },
            'general': {
                'expertise': 'behavioral health assessment',
                'context': 'Mental health assessments evaluate various aspects of psychological functioning and well-being.',
                'assessment_focus': 'Look for patterns related to mood, behavior, cognition, social functioning, and overall well-being.',
                'scoring_interpretation': 'Consider both quantitative scores and qualitative response patterns.'
            }
        }

    def analyze_response(self, response_data: Dict[str, Any], questionnaire_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a questionnaire response with enhanced domain-specific context

        Args:
            response_data: Dictionary containing response data
            questionnaire_info: Information about the questionnaire

        Returns:
            Dictionary containing analysis results
        """
        try:
            # Get the category of the questionnaire
            category = questionnaire_info.get('category', 'general').lower()
            
            # Get domain context for this category
            domain_context = self.domain_prompts.get(category, self.domain_prompts['general'])
            
            # Prepare the data for analysis
            response_text = json.dumps(response_data, indent=2)
            questionnaire_text = json.dumps(questionnaire_info, indent=2)
            
            # Create a more sophisticated prompt with domain-specific context
            prompt = f"""
            You are an expert in {domain_context['expertise']}.

            I'm going to provide you with response data from a questionnaire and information about the questionnaire itself.
            Please analyze this data and provide a comprehensive clinical assessment.

            DOMAIN CONTEXT:
            {domain_context['context']}

            ASSESSMENT FOCUS:
            {domain_context['assessment_focus']}

            SCORING INTERPRETATION:
            {domain_context['scoring_interpretation']}

            QUESTIONNAIRE INFORMATION:
            {questionnaire_text}

            RESPONSE DATA:
            {response_text}

            Please provide a comprehensive analysis with the following structure:
            1. SUMMARY: A concise summary of the assessment findings (2-3 sentences)
            2. DETAILED ANALYSIS: A thorough analysis of the response patterns, including specific symptoms identified and their severity
            3. RISK ASSESSMENT: Evaluation of any risk factors identified, including safety concerns if present
            4. RECOMMENDATIONS: Specific, actionable recommendations based on the assessment
            5. KEY INSIGHTS: 3-5 key insights from the data that would be valuable for clinical decision-making
            6. CONFIDENCE ASSESSMENT: Your confidence level in this analysis (0.0-1.0) and any limitations

            Format your response as a JSON object with the following keys:
            {
                "summary": "...",
                "detailed_analysis": "...",
                "risk_assessment": "...",
                "recommendations": "...",
                "key_insights": [
                    {"title": "...", "description": "...", "supporting_data": "..."},
                    ...
                ],
                "confidence": 0.0-1.0,
                "limitations": "..."
            }
            """

            # Generate the analysis
            response = self.model.generate_content(prompt)
            
            # Parse the response
            try:
                # Try to parse as JSON
                result = json.loads(response.text)
                
                # Add metadata about the analysis
                result['analysis_metadata'] = {
                    'model': 'gemini-1.5-pro',
                    'timestamp': timezone.now().isoformat(),
                    'questionnaire_category': category,
                    'domain_expertise': domain_context['expertise']
                }
                
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, extract sections from the text
                structured_response = self._extract_sections_from_text(response.text)
                
                # Add metadata about the analysis
                structured_response['analysis_metadata'] = {
                    'model': 'gemini-1.5-pro',
                    'timestamp': timezone.now().isoformat(),
                    'questionnaire_category': category,
                    'domain_expertise': domain_context['expertise'],
                    'parsing_method': 'text_extraction'
                }
                
                return structured_response

        except Exception as e:
            logger.error(f"Error in analyze_response: {str(e)}")
            return {'error': str(e)}

    def analyze_multiple_responses(self, responses_data: List[Dict[str, Any]], questionnaire_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze multiple questionnaire responses to identify patterns and trends

        Args:
            responses_data: List of dictionaries containing response data
            questionnaire_info: Information about the questionnaire

        Returns:
            Dictionary containing analysis results
        """
        try:
            # Get the category of the questionnaire
            category = questionnaire_info.get('category', 'general').lower()
            
            # Get domain context for this category
            domain_context = self.domain_prompts.get(category, self.domain_prompts['general'])
            
            # Prepare the data for analysis
            responses_text = json.dumps(responses_data, indent=2)
            questionnaire_text = json.dumps(questionnaire_info, indent=2)
            
            # Create a sophisticated prompt for batch analysis
            prompt = f"""
            You are an expert in {domain_context['expertise']} with additional expertise in data analysis and pattern recognition.

            I'm going to provide you with multiple responses from the same questionnaire and information about the questionnaire itself.
            Please analyze this data to identify patterns, trends, and insights across all responses.

            DOMAIN CONTEXT:
            {domain_context['context']}

            ASSESSMENT FOCUS:
            {domain_context['assessment_focus']}

            SCORING INTERPRETATION:
            {domain_context['scoring_interpretation']}

            QUESTIONNAIRE INFORMATION:
            {questionnaire_text}

            MULTIPLE RESPONSE DATA (Total: {len(responses_data)} responses):
            {responses_text}

            Please provide a comprehensive batch analysis with the following structure:
            1. SUMMARY: A concise summary of the overall findings across all responses (2-3 sentences)
            2. PATTERN ANALYSIS: Identification of common patterns and trends across responses
            3. DEMOGRAPHIC INSIGHTS: Any patterns related to demographic factors (age, gender, etc.)
            4. RISK DISTRIBUTION: Analysis of risk levels across the population
            5. RECOMMENDATIONS: Population-level recommendations based on the analysis
            6. KEY INSIGHTS: 3-5 key insights from the aggregate data
            7. STATISTICAL SUMMARY: Brief statistical summary of the data (averages, distributions, etc.)

            Format your response as a JSON object with the following keys:
            {
                "summary": "...",
                "pattern_analysis": "...",
                "demographic_insights": "...",
                "risk_distribution": "...",
                "recommendations": "...",
                "key_insights": [
                    {"title": "...", "description": "...", "supporting_data": "..."},
                    ...
                ],
                "statistical_summary": "...",
                "confidence": 0.0-1.0
            }
            """

            # Generate the analysis
            response = self.model.generate_content(prompt)
            
            # Parse the response
            try:
                # Try to parse as JSON
                result = json.loads(response.text)
                
                # Add metadata about the analysis
                result['analysis_metadata'] = {
                    'model': 'gemini-1.5-pro',
                    'timestamp': timezone.now().isoformat(),
                    'questionnaire_category': category,
                    'domain_expertise': domain_context['expertise'],
                    'response_count': len(responses_data)
                }
                
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, extract sections from the text
                structured_response = self._extract_sections_from_text(response.text)
                
                # Add metadata about the analysis
                structured_response['analysis_metadata'] = {
                    'model': 'gemini-1.5-pro',
                    'timestamp': timezone.now().isoformat(),
                    'questionnaire_category': category,
                    'domain_expertise': domain_context['expertise'],
                    'response_count': len(responses_data),
                    'parsing_method': 'text_extraction'
                }
                
                return structured_response

        except Exception as e:
            logger.error(f"Error in analyze_multiple_responses: {str(e)}")
            return {'error': str(e)}

    def generate_visualization_recommendations(self, data: Dict[str, Any], questionnaire_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate recommendations for visualizing questionnaire data

        Args:
            data: Dictionary containing response data
            questionnaire_info: Information about the questionnaire

        Returns:
            Dictionary containing visualization recommendations
        """
        try:
            # Prepare the data
            data_text = json.dumps(data, indent=2)
            questionnaire_text = json.dumps(questionnaire_info, indent=2)
            
            # Create a prompt for visualization recommendations
            prompt = f"""
            You are an expert in data visualization and clinical assessment data.

            I'm going to provide you with questionnaire response data and information about the questionnaire.
            Please recommend the most effective visualizations for this data to provide clinical insights.

            QUESTIONNAIRE INFORMATION:
            {questionnaire_text}

            RESPONSE DATA:
            {data_text}

            For each recommended visualization, please provide:
            1. CHART TYPE: The type of chart or visualization (e.g., bar chart, line chart, heatmap)
            2. PURPOSE: What clinical insight this visualization would provide
            3. DATA MAPPING: Which data elements should be mapped to which visual elements
            4. INTERPRETATION GUIDE: How to interpret the visualization for clinical decision-making

            Recommend 3-5 different visualizations that would provide complementary insights.

            Format your response as a JSON object with the following structure:
            {
                "summary": "Overall summary of visualization approach",
                "visualizations": [
                    {
                        "chart_type": "...",
                        "purpose": "...",
                        "data_mapping": "...",
                        "interpretation_guide": "..."
                    },
                    ...
                ]
            }
            """

            # Generate the recommendations
            response = self.model.generate_content(prompt)
            
            # Parse the response
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                return {'recommendations': response.text}

        except Exception as e:
            logger.error(f"Error in generate_visualization_recommendations: {str(e)}")
            return {'error': str(e)}

    def generate_report(self, response_data: Dict[str, Any], analysis_results: Dict[str, Any], questionnaire_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive clinical report based on questionnaire responses and analysis

        Args:
            response_data: Dictionary containing response data
            analysis_results: Dictionary containing analysis results
            questionnaire_info: Information about the questionnaire

        Returns:
            Dictionary containing the report
        """
        try:
            # Prepare the data
            response_text = json.dumps(response_data, indent=2)
            analysis_text = json.dumps(analysis_results, indent=2)
            questionnaire_text = json.dumps(questionnaire_info, indent=2)
            
            # Get the category of the questionnaire
            category = questionnaire_info.get('category', 'general').lower()
            
            # Get domain context for this category
            domain_context = self.domain_prompts.get(category, self.domain_prompts['general'])
            
            # Create a prompt for report generation
            prompt = f"""
            You are an expert in {domain_context['expertise']} with experience in clinical report writing.

            I'm going to provide you with questionnaire response data, analysis results, and information about the questionnaire.
            Please generate a comprehensive clinical report based on this information.

            DOMAIN CONTEXT:
            {domain_context['context']}

            QUESTIONNAIRE INFORMATION:
            {questionnaire_text}

            RESPONSE DATA:
            {response_text}

            ANALYSIS RESULTS:
            {analysis_text}

            Please generate a professional clinical report with the following sections:
            1. EXECUTIVE SUMMARY: Brief overview of key findings
            2. ASSESSMENT DETAILS: Information about the assessment tool and process
            3. RESULTS: Detailed presentation of assessment results
            4. CLINICAL INTERPRETATION: Professional interpretation of the results
            5. RECOMMENDATIONS: Specific recommendations based on the assessment
            6. FOLLOW-UP PLAN: Suggested next steps and follow-up timeline

            The report should be written in a professional clinical tone, suitable for inclusion in a patient's medical record.
            Include appropriate clinical terminology while remaining clear and understandable.

            Format your response as a JSON object with the following structure:
            {
                "executive_summary": "...",
                "assessment_details": "...",
                "results": "...",
                "clinical_interpretation": "...",
                "recommendations": "...",
                "follow_up_plan": "..."
            }
            """

            # Generate the report
            response = self.model.generate_content(prompt)
            
            # Parse the response
            try:
                report = json.loads(response.text)
                
                # Add metadata
                report['report_metadata'] = {
                    'generated_at': timezone.now().isoformat(),
                    'questionnaire_title': questionnaire_info.get('title', 'Unknown'),
                    'questionnaire_category': category,
                    'model': 'gemini-1.5-pro'
                }
                
                return report
            except json.JSONDecodeError:
                # If JSON parsing fails, extract sections from the text
                structured_report = self._extract_sections_from_text(response.text)
                
                # Add metadata
                structured_report['report_metadata'] = {
                    'generated_at': timezone.now().isoformat(),
                    'questionnaire_title': questionnaire_info.get('title', 'Unknown'),
                    'questionnaire_category': category,
                    'model': 'gemini-1.5-pro',
                    'parsing_method': 'text_extraction'
                }
                
                return structured_report

        except Exception as e:
            logger.error(f"Error in generate_report: {str(e)}")
            return {'error': str(e)}

    def _extract_sections_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract structured sections from unstructured text response

        Args:
            text: The text to extract sections from

        Returns:
            Dictionary with extracted sections
        """
        # Common section headers to look for
        sections = {
            'summary': ['SUMMARY', 'EXECUTIVE SUMMARY'],
            'detailed_analysis': ['DETAILED ANALYSIS', 'PATTERN ANALYSIS'],
            'risk_assessment': ['RISK ASSESSMENT', 'RISK DISTRIBUTION'],
            'recommendations': ['RECOMMENDATIONS'],
            'key_insights': ['KEY INSIGHTS'],
            'confidence': ['CONFIDENCE ASSESSMENT', 'CONFIDENCE'],
            'limitations': ['LIMITATIONS'],
            'statistical_summary': ['STATISTICAL SUMMARY'],
            'demographic_insights': ['DEMOGRAPHIC INSIGHTS'],
            'assessment_details': ['ASSESSMENT DETAILS'],
            'results': ['RESULTS'],
            'clinical_interpretation': ['CLINICAL INTERPRETATION'],
            'follow_up_plan': ['FOLLOW-UP PLAN', 'FOLLOW UP PLAN']
        }
        
        result = {}
        
        # Split the text into lines
        lines = text.split('\n')
        
        current_section = None
        section_content = []
        
        # Process each line
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line is a section header
            is_header = False
            for section_key, headers in sections.items():
                for header in headers:
                    # Check for exact header or header with colon
                    if line.upper() == header or line.upper().startswith(f"{header}:"):
                        # If we were collecting content for a previous section, save it
                        if current_section and section_content:
                            result[current_section] = '\n'.join(section_content).strip()
                        
                        # Start a new section
                        current_section = section_key
                        section_content = []
                        is_header = True
                        break
                if is_header:
                    break
            
            # If not a header, add to current section content
            if not is_header and current_section:
                section_content.append(line)
        
        # Save the last section
        if current_section and section_content:
            result[current_section] = '\n'.join(section_content).strip()
        
        # Special handling for key insights
        if 'key_insights' in result and isinstance(result['key_insights'], str):
            # Try to parse key insights into a structured format
            insights_text = result['key_insights']
            insights = []
            
            # Split by numbered items or bullet points
            insight_items = []
            current_item = []
            
            for line in insights_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Check if this is a new numbered item or bullet point
                if line.startswith(('1.', '2.', '3.', '4.', '5.', '•', '-', '*')):
                    if current_item:
                        insight_items.append('\n'.join(current_item))
                        current_item = []
                    current_item.append(line)
                else:
                    current_item.append(line)
            
            # Add the last item
            if current_item:
                insight_items.append('\n'.join(current_item))
            
            # Process each insight item
            for item in insight_items:
                # Try to extract title and description
                parts = item.split(':', 1)
                if len(parts) > 1:
                    title = parts[0].strip()
                    # Remove any leading numbers or bullets
                    title = title.lstrip('1234567890.-*• ')
                    description = parts[1].strip()
                else:
                    title = "Insight"
                    description = item
                
                insights.append({
                    "title": title,
                    "description": description,
                    "supporting_data": ""
                })
            
            if insights:
                result['key_insights'] = insights
        
        # Try to extract confidence score
        if 'confidence' in result and isinstance(result['confidence'], str):
            confidence_text = result['confidence']
            import re
            # Look for a number between 0 and 1
            confidence_match = re.search(r'(\d+\.\d+|\d+)', confidence_text)
            if confidence_match:
                try:
                    confidence_value = float(confidence_match.group(1))
                    # Ensure it's between 0 and 1
                    if confidence_value > 1:
                        confidence_value /= 100  # Convert percentage to decimal
                    result['confidence'] = confidence_value
                except ValueError:
                    pass
        
        return result
