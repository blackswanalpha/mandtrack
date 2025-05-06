import json
import os
import google.generativeai as genai
from django.conf import settings
from feedback.models import Response, Answer
from surveys.models import Questionnaire, Question
from feedback.models.base import AIAnalysis

class AdvancedAIService:
    """
    Service for advanced AI analysis of questionnaire responses using Google's Gemini API
    """
    
    @staticmethod
    def initialize_gemini():
        """Initialize the Gemini API with the API key"""
        api_key = getattr(settings, 'GEMINI_API_KEY', 'AIzaSyAp5usIOWlm16BgN1tfGje4aD0YKVa1Mjc')
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-pro')
    
    @staticmethod
    def analyze_response(response):
        """
        Analyze a response using the Gemini API
        
        Args:
            response: Response instance
            
        Returns:
            AIAnalysis instance with the analysis results
        """
        # Get the questionnaire and answers
        questionnaire = response.survey
        answers = Answer.objects.filter(response=response).select_related('question', 'selected_choice').prefetch_related('multiple_choices')
        
        # Format the answers for analysis
        formatted_answers = []
        for answer in answers:
            question_text = answer.question.text if answer.question else "Unknown Question"
            
            if answer.question and answer.question.question_type == 'text':
                answer_text = answer.text_answer or "No answer provided"
            elif answer.question and answer.question.question_type == 'single_choice':
                answer_text = answer.selected_choice.text if answer.selected_choice else "No answer provided"
            elif answer.question and answer.question.question_type == 'multiple_choice':
                choices = [choice.text for choice in answer.multiple_choices.all()]
                answer_text = ", ".join(choices) if choices else "No choices selected"
            elif answer.question and answer.question.question_type == 'rating':
                answer_text = f"{answer.rating_answer or 'No rating'} / {answer.question.max_rating or 5}"
            elif answer.question and answer.question.question_type == 'country':
                answer_text = answer.country_answer or "No country selected"
            else:
                answer_text = answer.text_answer or "No answer provided"
                
            formatted_answers.append({
                "question": question_text,
                "answer": answer_text,
                "question_type": answer.question.question_type if answer.question else "unknown"
            })
        
        # Get respondent information
        respondent_info = {
            "name": response.user.get_full_name() if response.user else response.patient_name or "Anonymous",
            "email": response.user.email if response.user else response.patient_email or "Not provided",
            "age": response.patient_age or "Not provided",
            "gender": response.patient_gender or "Not provided"
        }
        
        # Create the prompt for the AI
        prompt = f"""
        You are an expert in analyzing questionnaire responses and providing insights.
        
        Questionnaire Title: {questionnaire.title}
        Questionnaire Description: {questionnaire.description or 'No description provided'}
        
        Respondent Information:
        - Name: {respondent_info['name']}
        - Age: {respondent_info['age']}
        - Gender: {respondent_info['gender']}
        
        Responses:
        {json.dumps(formatted_answers, indent=2)}
        
        Please provide a comprehensive analysis of these responses, including:
        
        1. A concise summary of the key findings (2-3 sentences)
        2. A detailed analysis of the responses, identifying patterns, concerns, and notable insights
        3. Specific recommendations based on the responses
        4. Risk assessment (low, medium, or high) with justification
        5. Potential trends or comparisons with typical responses
        6. Areas that may require further investigation or follow-up
        
        Format your response as a JSON object with the following structure:
        {
            "summary": "Concise summary of key findings",
            "detailed_analysis": "Detailed analysis of the responses",
            "recommendations": "Specific recommendations based on the responses",
            "risk_assessment": {
                "level": "low|medium|high",
                "justification": "Explanation of the risk assessment"
            },
            "trends": "Potential trends or comparisons",
            "follow_up_areas": "Areas requiring further investigation"
        }
        
        Only return the JSON object, nothing else.
        """
        
        try:
            # Initialize the Gemini API
            model = AdvancedAIService.initialize_gemini()
            
            # Generate the analysis
            response_text = model.generate_content(prompt).text
            
            # Parse the JSON response
            try:
                analysis_data = json.loads(response_text)
            except json.JSONDecodeError:
                # If the response is not valid JSON, try to extract JSON from the text
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    try:
                        analysis_data = json.loads(json_str)
                    except:
                        # If still not valid JSON, create a basic structure
                        analysis_data = {
                            "summary": "Unable to generate proper analysis.",
                            "detailed_analysis": "The AI model did not return a valid response format.",
                            "recommendations": "Please try again or contact support.",
                            "risk_assessment": {
                                "level": "medium",
                                "justification": "Unable to properly assess risk due to processing error."
                            },
                            "trends": "No trend analysis available.",
                            "follow_up_areas": "Consider manual review of the responses."
                        }
                else:
                    # If no JSON-like structure found, create a basic structure
                    analysis_data = {
                        "summary": "Unable to generate proper analysis.",
                        "detailed_analysis": "The AI model did not return a valid response format.",
                        "recommendations": "Please try again or contact support.",
                        "risk_assessment": {
                            "level": "medium",
                            "justification": "Unable to properly assess risk due to processing error."
                        },
                        "trends": "No trend analysis available.",
                        "follow_up_areas": "Consider manual review of the responses."
                    }
            
            # Create or update the AIAnalysis object
            try:
                analysis = AIAnalysis.objects.get(response=response)
            except AIAnalysis.DoesNotExist:
                analysis = AIAnalysis(response=response)
            
            # Update the analysis fields
            analysis.summary = analysis_data.get("summary", "No summary provided")
            analysis.detailed_analysis = analysis_data.get("detailed_analysis", "No detailed analysis provided")
            analysis.recommendations = analysis_data.get("recommendations", "No recommendations provided")
            
            # Get risk assessment
            risk_assessment = analysis_data.get("risk_assessment", {})
            risk_level = risk_assessment.get("level", "medium").lower()
            risk_justification = risk_assessment.get("justification", "No justification provided")
            
            analysis.risk_level = risk_level
            analysis.risk_justification = risk_justification
            
            # Add additional fields
            analysis.trends = analysis_data.get("trends", "No trend analysis provided")
            analysis.follow_up_areas = analysis_data.get("follow_up_areas", "No follow-up areas identified")
            
            # Save the analysis
            analysis.save()
            
            # Update the response risk level based on the AI analysis
            response.risk_level = risk_level
            response.save(update_fields=['risk_level'])
            
            return analysis
            
        except Exception as e:
            print(f"Error generating AI analysis: {str(e)}")
            
            # Create a basic analysis in case of error
            try:
                analysis = AIAnalysis.objects.get(response=response)
            except AIAnalysis.DoesNotExist:
                analysis = AIAnalysis(response=response)
            
            analysis.summary = "Unable to generate analysis due to an error."
            analysis.detailed_analysis = f"Error: {str(e)}"
            analysis.recommendations = "Please try again later or contact support."
            analysis.risk_level = "medium"
            analysis.risk_justification = "Default risk level due to analysis error."
            analysis.trends = "No trend analysis available."
            analysis.follow_up_areas = "Consider manual review of the responses."
            
            analysis.save()
            
            return analysis
    
    @staticmethod
    def analyze_member_responses(member, organization, limit=10):
        """
        Analyze all responses from a member to identify trends and patterns
        
        Args:
            member: OrganizationMember instance
            organization: Organization instance
            limit: Maximum number of responses to analyze (default: 10)
            
        Returns:
            dict with analysis results
        """
        # Get responses for this member
        responses = Response.objects.filter(
            user=member.user,
            survey__organization=organization
        ).select_related('survey').order_by('-created_at')[:limit]
        
        if not responses:
            return {
                "summary": "No responses found for analysis.",
                "trends": [],
                "recommendations": "No recommendations available without responses."
            }
        
        # Format the responses for analysis
        formatted_responses = []
        for response in responses:
            # Get the questionnaire
            questionnaire = response.survey
            
            # Get the answers
            answers = Answer.objects.filter(response=response).select_related('question', 'selected_choice').prefetch_related('multiple_choices')
            
            # Format the answers
            formatted_answers = []
            for answer in answers:
                question_text = answer.question.text if answer.question else "Unknown Question"
                
                if answer.question and answer.question.question_type == 'text':
                    answer_text = answer.text_answer or "No answer provided"
                elif answer.question and answer.question.question_type == 'single_choice':
                    answer_text = answer.selected_choice.text if answer.selected_choice else "No answer provided"
                elif answer.question and answer.question.question_type == 'multiple_choice':
                    choices = [choice.text for choice in answer.multiple_choices.all()]
                    answer_text = ", ".join(choices) if choices else "No choices selected"
                elif answer.question and answer.question.question_type == 'rating':
                    answer_text = f"{answer.rating_answer or 'No rating'} / {answer.question.max_rating or 5}"
                else:
                    answer_text = answer.text_answer or "No answer provided"
                    
                formatted_answers.append({
                    "question": question_text,
                    "answer": answer_text
                })
            
            # Add the response to the list
            formatted_responses.append({
                "questionnaire": questionnaire.title,
                "date": response.created_at.strftime("%Y-%m-%d"),
                "score": response.score,
                "risk_level": response.risk_level,
                "answers": formatted_answers
            })
        
        # Create the prompt for the AI
        prompt = f"""
        You are an expert in analyzing trends and patterns in questionnaire responses over time.
        
        Member Information:
        - Name: {member.user.get_full_name() or member.user.email}
        - Organization: {organization.name}
        
        Here are the responses from this member, ordered from most recent to oldest:
        {json.dumps(formatted_responses, indent=2)}
        
        Please analyze these responses to identify trends, patterns, and changes over time. Focus on:
        
        1. How the member's responses have changed over time
        2. Any consistent patterns or themes in the responses
        3. Areas of improvement or deterioration
        4. Recommendations based on the trends observed
        
        Format your response as a JSON object with the following structure:
        {{
            "summary": "Overall summary of the trends and patterns",
            "trends": [
                {{
                    "trend": "Description of trend 1",
                    "evidence": "Evidence supporting this trend",
                    "impact": "Potential impact of this trend"
                }},
                // Additional trends...
            ],
            "recommendations": "Specific recommendations based on the trends"
        }}
        
        Only return the JSON object, nothing else.
        """
        
        try:
            # Initialize the Gemini API
            model = AdvancedAIService.initialize_gemini()
            
            # Generate the analysis
            response_text = model.generate_content(prompt).text
            
            # Parse the JSON response
            try:
                analysis_data = json.loads(response_text)
            except json.JSONDecodeError:
                # If the response is not valid JSON, try to extract JSON from the text
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    try:
                        analysis_data = json.loads(json_str)
                    except:
                        # If still not valid JSON, create a basic structure
                        analysis_data = {
                            "summary": "Unable to generate proper trend analysis.",
                            "trends": [
                                {
                                    "trend": "No trends identified",
                                    "evidence": "Analysis error",
                                    "impact": "Unknown"
                                }
                            ],
                            "recommendations": "Please try again or contact support."
                        }
                else:
                    # If no JSON-like structure found, create a basic structure
                    analysis_data = {
                        "summary": "Unable to generate proper trend analysis.",
                        "trends": [
                            {
                                "trend": "No trends identified",
                                "evidence": "Analysis error",
                                "impact": "Unknown"
                            }
                        ],
                        "recommendations": "Please try again or contact support."
                    }
            
            return analysis_data
            
        except Exception as e:
            print(f"Error generating trend analysis: {str(e)}")
            
            # Return a basic analysis in case of error
            return {
                "summary": "Unable to generate trend analysis due to an error.",
                "trends": [
                    {
                        "trend": "No trends identified",
                        "evidence": f"Error: {str(e)}",
                        "impact": "Unknown"
                    }
                ],
                "recommendations": "Please try again later or contact support."
            }
