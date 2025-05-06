from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from feedback.models import Response, AIAnalysis
from groups.models import Organization, OrganizationMember
from analytics.services.advanced_ai_service import AdvancedAIService

@login_required
def analyze_response(request, response_id):
    """
    Analyze a response using the advanced AI service
    """
    response = get_object_or_404(Response, pk=response_id)
    
    # Check if user has permission to analyze this response
    if response.organization:
        try:
            user_membership = OrganizationMember.objects.get(
                organization=response.organization,
                user=request.user,
                is_active=True
            )
            is_admin = user_membership.role == 'admin'
            can_view_responses = user_membership.can_view_responses()
        except OrganizationMember.DoesNotExist:
            # If user is staff, allow access even if not a member
            if request.user.is_staff:
                is_admin = True
                can_view_responses = True
            else:
                messages.error(request, "You don't have permission to analyze this response.")
                return redirect('feedback:response_detail', pk=response_id)
        
        # If user is not admin and can't view responses, deny access
        if not is_admin and not can_view_responses:
            messages.error(request, "You don't have permission to analyze this response.")
            return redirect('feedback:response_detail', pk=response_id)
    
    # If this is an AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            # Analyze the response
            analysis = AdvancedAIService.analyze_response(response)
            
            # Return the analysis as JSON
            return JsonResponse({
                'success': True,
                'analysis': {
                    'summary': analysis.summary,
                    'detailed_analysis': analysis.detailed_analysis,
                    'recommendations': analysis.recommendations,
                    'risk_level': analysis.risk_level,
                    'risk_justification': analysis.risk_justification,
                    'trends': analysis.trends,
                    'follow_up_areas': analysis.follow_up_areas
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # If this is a regular request, analyze and redirect
    try:
        # Analyze the response
        analysis = AdvancedAIService.analyze_response(response)
        messages.success(request, "Response analyzed successfully.")
    except Exception as e:
        messages.error(request, f"Error analyzing response: {str(e)}")
    
    # Redirect to the response detail page
    return redirect('feedback:response_detail', pk=response_id)

@login_required
def analyze_member_responses(request, org_pk, member_pk):
    """
    Analyze all responses from a member to identify trends and patterns
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    member = get_object_or_404(OrganizationMember, pk=member_pk, organization=organization)
    
    # Check if user has permission to view member dashboard
    try:
        user_membership = OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            is_active=True
        )
        is_admin = user_membership.role == 'admin'
        can_view_responses = user_membership.can_view_responses()
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not a member
        if request.user.is_staff:
            is_admin = True
            can_view_responses = True
        else:
            messages.error(request, "You don't have permission to analyze this member's responses.")
            return redirect('groups:organization_list')
    
    # If user is not admin and can't view responses, deny access
    if not is_admin and not can_view_responses:
        messages.error(request, "You don't have permission to analyze this member's responses.")
        return redirect('groups:member_detail', org_pk=org_pk, pk=member_pk)
    
    # If this is an AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            # Analyze the member's responses
            analysis = AdvancedAIService.analyze_member_responses(member, organization)
            
            # Return the analysis as JSON
            return JsonResponse({
                'success': True,
                'analysis': analysis
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # If this is a regular request, analyze and redirect
    try:
        # Analyze the member's responses
        analysis = AdvancedAIService.analyze_member_responses(member, organization)
        
        # Store the analysis in the session for display
        request.session['member_analysis'] = analysis
        
        messages.success(request, "Member responses analyzed successfully.")
    except Exception as e:
        messages.error(request, f"Error analyzing member responses: {str(e)}")
    
    # Redirect to the member dashboard
    return redirect('groups:view_member_dashboard', org_pk=org_pk, member_pk=member_pk)
