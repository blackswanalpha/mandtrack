import json
import logging
import requests
from django.conf import settings
from django.utils import timezone
import google.generativeai as genai
from typing import Dict, Any, List

# Set up logger
logger = logging.getLogger(__name__)

class GeminiService:
    """
    Service for interacting with Google's Gemini API
    """

    def __init__(self, api_key=None):
        """
        Initialize the Gemini service with the API key
        """
        self.api_key = api_key or settings.GEMINI_API_KEY
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')

    def analyze_text(self, text: str, analysis_type: str = 'general') -> Dict[str, Any]:
        """
        Analyze text using Gemini API

        Args:
            text: The text to analyze
            analysis_type: Type of analysis to perform (general, sentiment, themes, etc.)

        Returns:
            Dictionary containing analysis results
        """
        try:
            prompt = self._get_prompt_for_analysis(text, analysis_type)
            response = self.model.generate_content(prompt)

            # Parse the response
            if analysis_type == 'sentiment':
                return self._parse_sentiment_response(response.text)
            elif analysis_type == 'themes':
                return self._parse_themes_response(response.text)
            elif analysis_type == 'summary':
                return {'summary': response.text}
            else:
                # Try to parse as JSON, fall back to text if not possible
                try:
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    return {'analysis': response.text}

        except Exception as e:
            return {'error': str(e)}

    def analyze_responses(self, responses: List[Dict[str, Any]], analysis_type: str = 'patterns') -> Dict[str, Any]:
        """
        Analyze multiple responses to find patterns

        Args:
            responses: List of response dictionaries
            analysis_type: Type of analysis to perform (patterns, clusters, trends, etc.)

        Returns:
            Dictionary containing analysis results
        """
        try:
            # Convert responses to a format suitable for the API
            responses_text = json.dumps(responses, indent=2)
            prompt = self._get_prompt_for_responses_analysis(responses_text, analysis_type)

            response = self.model.generate_content(prompt)

            # Parse the response
            if analysis_type == 'patterns':
                return self._parse_patterns_response(response.text)
            elif analysis_type == 'clusters':
                return self._parse_clusters_response(response.text)
            elif analysis_type == 'trends':
                return self._parse_trends_response(response.text)
            else:
                # Try to parse as JSON, fall back to text if not possible
                try:
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    return {'analysis': response.text}

        except Exception as e:
            return {'error': str(e)}

    def generate_insights(self, data: Dict[str, Any], questionnaire_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate insights from response data

        Args:
            data: Dictionary containing response data
            questionnaire_info: Information about the questionnaire

        Returns:
            Dictionary containing insights
        """
        try:
            # Convert data to a format suitable for the API
            data_text = json.dumps(data, indent=2)
            questionnaire_text = json.dumps(questionnaire_info, indent=2)

            prompt = f"""
            You are an expert data analyst specializing in survey and questionnaire analysis.

            I'm going to provide you with response data from a questionnaire and information about the questionnaire itself.
            Please analyze this data and provide meaningful insights, recommendations, and observations.

            Questionnaire Information:
            {questionnaire_text}

            Response Data:
            {data_text}

            Please provide your analysis in the following JSON format:
            {{
                "key_insights": [
                    {{
                        "title": "Insight title",
                        "description": "Detailed description of the insight",
                        "confidence": 0.85,  // A number between 0 and 1 indicating confidence level
                        "supporting_data": "Reference to the data that supports this insight"
                    }}
                ],
                "patterns": [
                    {{
                        "pattern_name": "Name of the pattern",
                        "description": "Description of the pattern",
                        "frequency": "How often this pattern appears"
                    }}
                ],
                "recommendations": [
                    {{
                        "title": "Recommendation title",
                        "description": "Detailed description of the recommendation",
                        "priority": "high/medium/low",
                        "rationale": "Why this recommendation is important"
                    }}
                ],
                "summary": "Overall summary of the analysis"
            }}

            Focus on finding meaningful patterns, correlations, and insights that would be valuable for understanding the responses.
            """

            response = self.model.generate_content(prompt)

            # Try to parse as JSON, fall back to text if not possible
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                return {'insights': response.text}

        except Exception as e:
            return {'error': str(e)}

    def analyze_questionnaire_data(self, data: Dict[str, Any], questionnaire_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze questionnaire data and provide a comprehensive analysis

        Args:
            data: Dictionary containing response data
            questionnaire_info: Information about the questionnaire

        Returns:
            Dictionary containing analysis results
        """
        try:
            # Create a prompt for the analysis
            category = questionnaire_info.get('category', 'general')
            title = questionnaire_info.get('title', 'Questionnaire')
            description = questionnaire_info.get('description', '')

            # Get domain-specific context based on category
            domain_context = self._get_domain_context(category)

            # Extract key metrics for the prompt
            total_questions = len(data.get('answers', []))
            scored_questions = sum(1 for answer in data.get('answers', []) if answer.get('is_scored', False))

            # Get respondent info for context
            respondent_info = data.get('respondent', {})
            age = respondent_info.get('age')
            gender = respondent_info.get('gender')
            total_score = respondent_info.get('total_score')
            risk_level = respondent_info.get('risk_level')

            # Create an enhanced prompt with more context
            prompt = f"""
            You are an expert analyst specializing in {domain_context['expertise']}.
            Analyze the following questionnaire response data and provide a comprehensive analysis.

            Questionnaire Information:
            - Title: {title}
            - Category: {category}
            - Description: {description}
            - Total Questions: {total_questions}
            - Scored Questions: {scored_questions}

            Respondent Information:
            {f"- Age: {age}" if age else "- Age: Not provided"}
            {f"- Gender: {gender}" if gender else "- Gender: Not provided"}
            {f"- Total Score: {total_score}" if total_score is not None else "- Total Score: Not available"}
            {f"- Risk Level: {risk_level}" if risk_level else "- Risk Level: Not assessed"}

            {domain_context['context']}

            Response Data:
            {json.dumps(data, indent=2)}

            Please provide a detailed analysis with the following components:
            1. A brief summary of the response (2-3 sentences)
            2. A detailed analysis of the responses, including patterns, areas of concern, and notable findings
            3. Specific recommendations based on the responses, with priority levels (high/medium/low)
            4. Key insights extracted from the data, including sentiment analysis
            5. Suggested next steps with timeline recommendations (immediate/short-term/long-term)
            6. Risk assessment with confidence level
            7. Potential correlations between different answers
            8. Comparative analysis with typical responses for this category

            Format your response as a JSON object with the following structure:
            {{
                "summary": "Brief summary of the response",
                "detailed_analysis": "Detailed analysis of the responses...",
                "recommendations": [
                    {{
                        "text": "Specific recommendation",
                        "priority": "high/medium/low",
                        "rationale": "Why this recommendation is important"
                    }}
                ],
                "insights": {{
                    "key_findings": ["Finding 1", "Finding 2"],
                    "sentiment": "positive/negative/neutral/mixed",
                    "sentiment_score": 0.75,
                    "key_topics": ["Topic 1", "Topic 2"],
                    "notable_patterns": ["Pattern 1", "Pattern 2"]
                }},
                "next_steps": [
                    {{
                        "action": "Suggested action",
                        "timeline": "immediate/short-term/long-term",
                        "responsible_party": "patient/provider/caregiver"
                    }}
                ],
                "risk_assessment": {{
                    "level": "low/medium/high/critical",
                    "factors": ["Factor 1", "Factor 2"],
                    "confidence": 0.85
                }},
                "correlations": [
                    {{
                        "description": "Description of correlation",
                        "strength": "weak/moderate/strong",
                        "questions_involved": ["Question 1", "Question 2"]
                    }}
                ],
                "comparative_analysis": "How this response compares to typical responses..."
            }}

            {domain_context['additional_instructions']}
            """

            # Generate the analysis with a lower temperature for more consistent results
            response = self.model.generate_content(prompt, generation_config={
                "temperature": 0.2,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 4096
            })

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
                # If JSON parsing fails, create a structured response from the text
                structured_response = self._structure_analysis_response(response.text)

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
            logger.error(f"Error in analyze_questionnaire_data: {str(e)}")

            # Create a detailed error response
            error_response = {
                'error': {
                    'message': str(e),
                    'type': type(e).__name__,
                    'timestamp': timezone.now().isoformat(),
                    'recoverable': isinstance(e, (requests.RequestException, json.JSONDecodeError))
                },
                'summary': f"Error analyzing questionnaire data: {str(e)}",
                'detailed_analysis': "An error occurred during analysis. This may be due to a temporary issue with the AI service.",
                'recommendations': "Please try again in a few moments or contact support if the issue persists.",
                'insights': {},
                'next_steps': "",
                'risk_assessment': ""
            }

            return error_response

    def _get_domain_context(self, category: str) -> Dict[str, str]:
        """
        Get domain-specific context based on questionnaire category

        Args:
            category: The category of the questionnaire

        Returns:
            Dictionary containing domain-specific context
        """
        # Default context
        default_context = {
            'expertise': 'questionnaire analysis',
            'context': 'Focus on providing objective analysis of the responses.',
            'additional_instructions': 'Ensure your analysis is balanced and evidence-based.'
        }

        # Category-specific contexts
        contexts = {
            'anxiety': {
                'expertise': 'anxiety assessment and mental health',
                'context': '''
                For anxiety assessments, consider the following clinical guidelines:
                - Mild anxiety (scores 0-4): Generally doesn't significantly impact daily functioning
                - Moderate anxiety (scores 5-9): May cause some impairment in social or occupational functioning
                - Severe anxiety (scores 10-14): Significantly impacts daily functioning
                - Extreme anxiety (scores 15+): Severely debilitating, may include panic attacks

                Pay special attention to questions about:
                - Physical symptoms (racing heart, trembling, shortness of breath)
                - Avoidance behaviors
                - Excessive worry
                - Sleep disturbances
                - Impact on daily functioning
                ''',
                'additional_instructions': '''
                Be sensitive to the clinical implications of your analysis. For high-risk cases (scores 15+),
                emphasize the importance of professional mental health support. For all analyses, maintain a
                supportive and non-judgmental tone.
                '''
            },
            'depression': {
                'expertise': 'depression assessment and mental health',
                'context': '''
                For depression assessments, consider the following clinical guidelines:
                - Mild depression (scores 0-4): Minimal impact on daily functioning
                - Moderate depression (scores 5-9): Noticeable impact on daily functioning
                - Moderately severe depression (scores 10-14): Significant impairment
                - Severe depression (scores 15+): Severe impairment, may include suicidal ideation

                Pay special attention to questions about:
                - Persistent sadness or low mood
                - Loss of interest or pleasure
                - Fatigue or low energy
                - Sleep disturbances
                - Changes in appetite
                - Feelings of worthlessness or guilt
                - Suicidal thoughts
                ''',
                'additional_instructions': '''
                For any responses indicating suicidal thoughts, emphasize the urgent need for professional
                intervention. Maintain a compassionate tone and focus on hope and recovery in your analysis.
                '''
            },
            'stress': {
                'expertise': 'stress management and psychological well-being',
                'context': '''
                For stress assessments, consider:
                - Low stress (scores 0-4): Manageable levels of stress
                - Moderate stress (scores 5-9): Noticeable impact on well-being
                - High stress (scores 10-14): Significant impact on functioning
                - Severe stress (scores 15+): Overwhelming, may lead to burnout

                Pay special attention to questions about:
                - Work/life balance
                - Coping mechanisms
                - Physical manifestations of stress
                - Sleep quality
                - Social support
                ''',
                'additional_instructions': '''
                Focus on practical stress management techniques in your recommendations. Consider both
                immediate stress relief strategies and long-term lifestyle changes.
                '''
            },
            'ptsd': {
                'expertise': 'trauma assessment and PTSD',
                'context': '''
                For PTSD assessments, consider:
                - Key symptom clusters: re-experiencing, avoidance, negative alterations in cognition/mood, hyperarousal
                - Duration of symptoms (acute vs. chronic)
                - Impact on functioning
                - Presence of dissociative symptoms

                Pay special attention to questions about:
                - Intrusive memories or flashbacks
                - Avoidance behaviors
                - Negative beliefs about self or world
                - Hypervigilance
                - Emotional numbing
                - Sleep disturbances
                ''',
                'additional_instructions': '''
                Approach trauma-related responses with particular sensitivity. Emphasize the importance of
                trauma-informed care and evidence-based treatments like CPT, PE, or EMDR in your recommendations.
                '''
            },
            'addiction': {
                'expertise': 'addiction assessment and substance use disorders',
                'context': '''
                For addiction assessments, consider:
                - Patterns of substance use
                - Loss of control
                - Cravings
                - Tolerance and withdrawal
                - Continued use despite negative consequences
                - Impact on functioning

                Pay special attention to questions about:
                - Frequency and quantity of substance use
                - Failed attempts to cut down
                - Time spent obtaining, using, or recovering
                - Social or occupational impairment
                - Risky behaviors
                ''',
                'additional_instructions': '''
                Avoid stigmatizing language. Frame addiction as a treatable health condition rather than a
                moral failing. Emphasize evidence-based treatments and the possibility of recovery.
                '''
            },
            'adhd': {
                'expertise': 'ADHD assessment and neurodevelopmental disorders',
                'context': '''
                For ADHD assessments, consider:
                - Inattention symptoms
                - Hyperactivity/impulsivity symptoms
                - Duration and pervasiveness across settings
                - Age of onset
                - Impact on functioning

                Pay special attention to questions about:
                - Difficulty sustaining attention
                - Organizational challenges
                - Forgetfulness
                - Fidgeting or restlessness
                - Impulsive decisions
                - Interrupting others
                ''',
                'additional_instructions': '''
                Consider both pharmacological and non-pharmacological interventions in your recommendations.
                Focus on strengths and compensatory strategies, not just deficits.
                '''
            },
            'eating_disorder': {
                'expertise': 'eating disorder assessment and treatment',
                'context': '''
                For eating disorder assessments, consider:
                - Disturbances in eating behavior
                - Body image concerns
                - Fear of weight gain
                - Compensatory behaviors
                - Medical complications

                Pay special attention to questions about:
                - Restrictive eating
                - Binge episodes
                - Purging behaviors
                - Body checking or avoidance
                - Exercise patterns
                - Preoccupation with food, weight, or shape
                ''',
                'additional_instructions': '''
                Emphasize the seriousness of eating disorders as having the highest mortality rate among
                psychiatric conditions. Recommend appropriate levels of care based on symptom severity.
                '''
            },
            'personality': {
                'expertise': 'personality assessment and individual differences',
                'context': '''
                For personality assessments, consider:
                - Trait patterns rather than diagnostic categories
                - Consistency across situations and time
                - Cultural context of personality expression

                Pay special attention to questions about:
                - Interpersonal functioning
                - Emotional regulation
                - Impulse control
                - Self-concept
                - Coping styles
                ''',
                'additional_instructions': '''
                Avoid pathologizing personality differences. Focus on how personality traits may influence
                adaptation to different environments and relationships.
                '''
            },
            'cognitive': {
                'expertise': 'cognitive assessment and neuropsychology',
                'context': '''
                For cognitive assessments, consider:
                - Attention and concentration
                - Memory (working, short-term, long-term)
                - Executive functioning
                - Processing speed
                - Language abilities

                Pay special attention to questions about:
                - Difficulty with complex tasks
                - Memory lapses
                - Problem-solving challenges
                - Decision-making processes
                - Changes in cognitive abilities
                ''',
                'additional_instructions': '''
                Consider both cognitive strengths and weaknesses in your analysis. Recommend appropriate
                cognitive assessments for any concerning patterns.
                '''
            }
        }

        # Return category-specific context if available, otherwise default
        return contexts.get(category.lower(), default_context)

    def _structure_analysis_response(self, text: str) -> Dict[str, Any]:
        """
        Structure a text response into the expected format for questionnaire analysis
        """
        # Split the text into sections based on common headers
        sections = {}

        # Try to identify sections
        if "Summary" in text or "SUMMARY" in text:
            summary_start = max(text.find("Summary:"), text.find("SUMMARY:"))
            if summary_start >= 0:
                next_section = min(x for x in [
                    text.find("Detailed Analysis", summary_start),
                    text.find("DETAILED ANALYSIS", summary_start),
                    text.find("Recommendations", summary_start),
                    text.find("RECOMMENDATIONS", summary_start),
                    len(text)
                ] if x >= 0)
                sections["summary"] = text[summary_start:next_section].strip()

        if "Detailed Analysis" in text or "DETAILED ANALYSIS" in text:
            analysis_start = max(text.find("Detailed Analysis:"), text.find("DETAILED ANALYSIS:"))
            if analysis_start >= 0:
                next_section = min(x for x in [
                    text.find("Recommendations", analysis_start),
                    text.find("RECOMMENDATIONS", analysis_start),
                    text.find("Insights", analysis_start),
                    text.find("INSIGHTS", analysis_start),
                    len(text)
                ] if x >= 0)
                sections["detailed_analysis"] = text[analysis_start:next_section].strip()

        if "Recommendations" in text or "RECOMMENDATIONS" in text:
            recommendations_start = max(text.find("Recommendations:"), text.find("RECOMMENDATIONS:"))
            if recommendations_start >= 0:
                next_section = min(x for x in [
                    text.find("Insights", recommendations_start),
                    text.find("INSIGHTS", recommendations_start),
                    text.find("Next Steps", recommendations_start),
                    text.find("NEXT STEPS", recommendations_start),
                    len(text)
                ] if x >= 0)
                recommendations_text = text[recommendations_start:next_section].strip()

                # Try to parse recommendations into structured format
                recommendations = []
                import re
                # Look for numbered or bulleted recommendations
                recommendation_pattern = re.compile(r'(?:^|\n)(?:\d+\.|\*|\-)\s*(.*?)(?=(?:\n(?:\d+\.|\*|\-)|$))', re.DOTALL)
                matches = recommendation_pattern.findall(recommendations_text)

                if matches:
                    for match in matches:
                        # Try to identify priority level
                        priority = "medium"  # default
                        if "high priority" in match.lower() or "urgent" in match.lower() or "critical" in match.lower():
                            priority = "high"
                        elif "low priority" in match.lower() or "optional" in match.lower() or "consider" in match.lower():
                            priority = "low"

                        recommendations.append({
                            "text": match.strip(),
                            "priority": priority,
                            "rationale": ""  # We don't have a reliable way to extract this from unstructured text
                        })

                if recommendations:
                    sections["recommendations"] = recommendations
                else:
                    sections["recommendations"] = recommendations_text

        if "Insights" in text or "INSIGHTS" in text:
            insights_start = max(text.find("Insights:"), text.find("INSIGHTS:"))
            if insights_start >= 0:
                next_section = min(x for x in [
                    text.find("Next Steps", insights_start),
                    text.find("NEXT STEPS", insights_start),
                    text.find("Risk Assessment", insights_start),
                    text.find("RISK ASSESSMENT", insights_start),
                    text.find("Correlations", insights_start),
                    text.find("CORRELATIONS", insights_start),
                    len(text)
                ] if x >= 0)
                insights_text = text[insights_start:next_section].strip()

                # Try to extract key findings
                import re
                findings_pattern = re.compile(r'(?:^|\n)(?:\d+\.|\*|\-)\s*(.*?)(?=(?:\n(?:\d+\.|\*|\-)|$))', re.DOTALL)
                findings = findings_pattern.findall(insights_text)

                # Try to extract sentiment
                sentiment = "neutral"  # default
                sentiment_score = 0.0

                if "positive sentiment" in insights_text.lower():
                    sentiment = "positive"
                    sentiment_score = 0.7
                elif "negative sentiment" in insights_text.lower():
                    sentiment = "negative"
                    sentiment_score = -0.7
                elif "mixed sentiment" in insights_text.lower():
                    sentiment = "mixed"
                    sentiment_score = 0.0

                # Create structured insights
                insights = {
                    "key_findings": findings if findings else [],
                    "sentiment": sentiment,
                    "sentiment_score": sentiment_score,
                    "raw_text": insights_text
                }

                sections["insights"] = insights

        if "Next Steps" in text or "NEXT STEPS" in text:
            next_steps_start = max(text.find("Next Steps:"), text.find("NEXT STEPS:"))
            if next_steps_start >= 0:
                next_section = min(x for x in [
                    text.find("Risk Assessment", next_steps_start),
                    text.find("RISK ASSESSMENT", next_steps_start),
                    text.find("Correlations", next_steps_start),
                    text.find("CORRELATIONS", next_steps_start),
                    len(text)
                ] if x >= 0)
                next_steps_text = text[next_steps_start:next_section].strip()

                # Try to parse next steps into structured format
                next_steps = []
                import re
                steps_pattern = re.compile(r'(?:^|\n)(?:\d+\.|\*|\-)\s*(.*?)(?=(?:\n(?:\d+\.|\*|\-)|$))', re.DOTALL)
                matches = steps_pattern.findall(next_steps_text)

                if matches:
                    for match in matches:
                        # Try to identify timeline
                        timeline = "short-term"  # default
                        if "immediate" in match.lower() or "urgent" in match.lower() or "right away" in match.lower():
                            timeline = "immediate"
                        elif "long-term" in match.lower() or "ongoing" in match.lower() or "future" in match.lower():
                            timeline = "long-term"

                        # Try to identify responsible party
                        responsible_party = "provider"  # default
                        if "patient" in match.lower() or "client" in match.lower() or "self" in match.lower():
                            responsible_party = "patient"
                        elif "caregiver" in match.lower() or "family" in match.lower() or "support" in match.lower():
                            responsible_party = "caregiver"

                        next_steps.append({
                            "action": match.strip(),
                            "timeline": timeline,
                            "responsible_party": responsible_party
                        })

                if next_steps:
                    sections["next_steps"] = next_steps
                else:
                    sections["next_steps"] = next_steps_text

        if "Risk Assessment" in text or "RISK ASSESSMENT" in text:
            risk_start = max(text.find("Risk Assessment:"), text.find("RISK ASSESSMENT:"))
            if risk_start >= 0:
                next_section = min(x for x in [
                    text.find("Correlations", risk_start),
                    text.find("CORRELATIONS", risk_start),
                    text.find("Comparative Analysis", risk_start),
                    text.find("COMPARATIVE ANALYSIS", risk_start),
                    len(text)
                ] if x >= 0)
                risk_text = text[risk_start:next_section].strip()

                # Try to extract risk level
                risk_level = "medium"  # default
                if "low risk" in risk_text.lower():
                    risk_level = "low"
                elif "high risk" in risk_text.lower():
                    risk_level = "high"
                elif "critical risk" in risk_text.lower() or "severe risk" in risk_text.lower():
                    risk_level = "critical"

                # Try to extract risk factors
                import re
                factors_pattern = re.compile(r'(?:^|\n)(?:\d+\.|\*|\-)\s*(.*?)(?=(?:\n(?:\d+\.|\*|\-)|$))', re.DOTALL)
                factors = factors_pattern.findall(risk_text)

                # Create structured risk assessment
                risk_assessment = {
                    "level": risk_level,
                    "factors": factors if factors else [],
                    "confidence": 0.7,  # default confidence
                    "raw_text": risk_text
                }

                sections["risk_assessment"] = risk_assessment

        if "Correlations" in text or "CORRELATIONS" in text:
            correlations_start = max(text.find("Correlations:"), text.find("CORRELATIONS:"))
            if correlations_start >= 0:
                next_section = min(x for x in [
                    text.find("Comparative Analysis", correlations_start),
                    text.find("COMPARATIVE ANALYSIS", correlations_start),
                    len(text)
                ] if x >= 0)
                correlations_text = text[correlations_start:next_section].strip()

                # Try to parse correlations into structured format
                correlations = []
                import re
                correlation_pattern = re.compile(r'(?:^|\n)(?:\d+\.|\*|\-)\s*(.*?)(?=(?:\n(?:\d+\.|\*|\-)|$))', re.DOTALL)
                matches = correlation_pattern.findall(correlations_text)

                if matches:
                    for match in matches:
                        # Try to identify strength
                        strength = "moderate"  # default
                        if "strong" in match.lower() or "significant" in match.lower() or "high" in match.lower():
                            strength = "strong"
                        elif "weak" in match.lower() or "slight" in match.lower() or "minor" in match.lower():
                            strength = "weak"

                        correlations.append({
                            "description": match.strip(),
                            "strength": strength,
                            "questions_involved": []  # We don't have a reliable way to extract this from unstructured text
                        })

                if correlations:
                    sections["correlations"] = correlations

        if "Comparative Analysis" in text or "COMPARATIVE ANALYSIS" in text:
            comparative_start = max(text.find("Comparative Analysis:"), text.find("COMPARATIVE ANALYSIS:"))
            if comparative_start >= 0:
                sections["comparative_analysis"] = text[comparative_start:].strip()

        # If we couldn't identify sections, use the whole text as detailed_analysis
        if not sections:
            return {
                "summary": "Analysis of questionnaire response",
                "detailed_analysis": text,
                "recommendations": "Please review the analysis for recommendations.",
                "insights": {
                    "key_findings": [],
                    "sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "raw_text": ""
                },
                "next_steps": [],
                "risk_assessment": {
                    "level": "medium",
                    "factors": [],
                    "confidence": 0.5,
                    "raw_text": ""
                },
                "correlations": [],
                "comparative_analysis": ""
            }

        # Fill in any missing sections
        if "summary" not in sections:
            sections["summary"] = "Analysis of questionnaire response"
        if "detailed_analysis" not in sections:
            sections["detailed_analysis"] = "Detailed analysis not available."
        if "recommendations" not in sections:
            sections["recommendations"] = "Recommendations not available."
        if "insights" not in sections:
            sections["insights"] = {
                "key_findings": [],
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "raw_text": ""
            }
        if "next_steps" not in sections:
            sections["next_steps"] = []
        if "risk_assessment" not in sections:
            sections["risk_assessment"] = {
                "level": "medium",
                "factors": [],
                "confidence": 0.5,
                "raw_text": ""
            }
        if "correlations" not in sections:
            sections["correlations"] = []
        if "comparative_analysis" not in sections:
            sections["comparative_analysis"] = ""

        return sections

    def _get_prompt_for_analysis(self, text: str, analysis_type: str) -> str:
        """
        Get the appropriate prompt for the analysis type
        """
        if analysis_type == 'sentiment':
            return f"""
            Analyze the sentiment of the following text. Provide a detailed analysis including:
            1. Overall sentiment (positive, negative, or neutral)
            2. Sentiment score (a number between -1 and 1)
            3. Key emotional tones detected
            4. Confidence level in your analysis

            Return your analysis in JSON format with the following structure:
            {{
                "sentiment": "positive/negative/neutral",
                "score": 0.75,
                "emotional_tones": ["happy", "excited", "satisfied"],
                "confidence": 0.85
            }}

            Text to analyze:
            {text}
            """

        elif analysis_type == 'themes':
            return f"""
            Identify the main themes and topics in the following text. Provide a detailed analysis including:
            1. Main themes (at least 3 if possible)
            2. Key topics within each theme
            3. Relative importance of each theme

            Return your analysis in JSON format with the following structure:
            {{
                "themes": [
                    {{
                        "name": "Theme name",
                        "topics": ["topic 1", "topic 2", "topic 3"],
                        "importance": 0.85
                    }}
                ]
            }}

            Text to analyze:
            {text}
            """

        elif analysis_type == 'summary':
            return f"""
            Provide a concise summary of the following text, capturing the main points and key information.

            Text to summarize:
            {text}
            """

        else:  # general analysis
            return f"""
            Provide a general analysis of the following text. Include observations about:
            1. Main points and arguments
            2. Tone and style
            3. Any notable patterns or characteristics

            Text to analyze:
            {text}
            """

    def _get_prompt_for_responses_analysis(self, responses_text: str, analysis_type: str) -> str:
        """
        Get the appropriate prompt for analyzing multiple responses
        """
        if analysis_type == 'patterns':
            return f"""
            Analyze the following survey responses to identify patterns. Provide a detailed analysis including:
            1. Common response patterns
            2. Correlations between different answers
            3. Unusual or outlier responses

            Return your analysis in JSON format with the following structure:
            {{
                "patterns": [
                    {{
                        "description": "Pattern description",
                        "frequency": "How common this pattern is",
                        "examples": ["example 1", "example 2"]
                    }}
                ],
                "correlations": [
                    {{
                        "description": "Description of correlation",
                        "strength": 0.75,
                        "confidence": 0.85
                    }}
                ],
                "outliers": [
                    {{
                        "description": "Description of outlier",
                        "reason": "Why this is considered an outlier"
                    }}
                ]
            }}

            Responses to analyze:
            {responses_text}
            """

        elif analysis_type == 'clusters':
            return f"""
            Analyze the following survey responses to identify clusters or groups. Provide a detailed analysis including:
            1. Main clusters or groups of similar responses
            2. Characteristics of each cluster
            3. Size and significance of each cluster

            Return your analysis in JSON format with the following structure:
            {{
                "clusters": [
                    {{
                        "name": "Cluster name",
                        "characteristics": ["characteristic 1", "characteristic 2"],
                        "size": "Approximate percentage of responses in this cluster",
                        "significance": "Why this cluster is significant"
                    }}
                ]
            }}

            Responses to analyze:
            {responses_text}
            """

        elif analysis_type == 'trends':
            return f"""
            Analyze the following survey responses to identify trends over time. Provide a detailed analysis including:
            1. Main trends observed
            2. Changes in responses over time
            3. Potential factors influencing these trends

            Return your analysis in JSON format with the following structure:
            {{
                "trends": [
                    {{
                        "description": "Description of trend",
                        "direction": "increasing/decreasing/stable",
                        "magnitude": "Significance of the trend",
                        "potential_factors": ["factor 1", "factor 2"]
                    }}
                ]
            }}

            Responses to analyze:
            {responses_text}
            """

        else:  # general analysis
            return f"""
            Provide a general analysis of the following survey responses. Include observations about:
            1. Overall patterns and themes
            2. Notable insights
            3. Potential areas for further investigation

            Return your analysis in JSON format if possible.

            Responses to analyze:
            {responses_text}
            """

    def _parse_sentiment_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the response for sentiment analysis
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If not valid JSON, extract sentiment information manually
            sentiment = "neutral"
            if "positive" in response_text.lower():
                sentiment = "positive"
            elif "negative" in response_text.lower():
                sentiment = "negative"

            # Try to extract score
            score = 0.0
            import re
            score_match = re.search(r'score.*?(-?\d+\.\d+)', response_text, re.IGNORECASE)
            if score_match:
                try:
                    score = float(score_match.group(1))
                except ValueError:
                    pass

            return {
                "sentiment": sentiment,
                "score": score,
                "analysis": response_text
            }

    def _parse_themes_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the response for themes analysis
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If not valid JSON, return the raw text
            return {
                "themes": [],
                "analysis": response_text
            }

    def _parse_patterns_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the response for patterns analysis
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If not valid JSON, return the raw text
            return {
                "patterns": [],
                "analysis": response_text
            }

    def _parse_clusters_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the response for clusters analysis
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If not valid JSON, return the raw text
            return {
                "clusters": [],
                "analysis": response_text
            }

    def _parse_trends_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the response for trends analysis
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If not valid JSON, return the raw text
            return {
                "trends": [],
                "analysis": response_text
            }
