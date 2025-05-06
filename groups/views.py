from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Avg, Count
from .models import Organization, OrganizationMember
from .forms import OrganizationForm, OrganizationMemberForm
from surveys.models import Questionnaire
from feedback.models import Response, Answer, AIAnalysis

User = get_user_model()

@login_required
def organization_list(request):
    """
    Display a list of all organizations
    """
    # Get organizations the user is a member of
    user_organizations = Organization.objects.filter(
        members__user=request.user,
        members__is_active=True
    ).distinct()

    # If user is staff, also show all organizations
    if request.user.is_staff:
        all_organizations = Organization.objects.all()
        # Combine the querysets without duplicates
        organizations = all_organizations.distinct()
    else:
        organizations = user_organizations

    # Apply filters if provided
    org_type = request.GET.get('type')
    if org_type:
        organizations = organizations.filter(type=org_type)

    # Get all organization types for the filter dropdown
    types = Organization._meta.get_field('type').choices

    context = {
        'organizations': organizations,
        'types': types,
    }

    return render(request, 'groups/organization_list.html', context)

@login_required
def organization_create(request):
    """
    Create a new organization
    """
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            organization = form.save(commit=False)
            organization.created_by = request.user
            organization.save()

            # Add the creator as an admin member
            OrganizationMember.objects.create(
                organization=organization,
                user=request.user,
                role='admin',
                is_active=True
            )

            messages.success(request, 'Organization created successfully!')
            return redirect('groups:organization_detail', pk=organization.pk)
    else:
        form = OrganizationForm()

    return render(request, 'groups/organization_form.html', {
        'form': form,
        'is_edit': False
    })

@login_required
def organization_detail(request, pk):
    """
    Display organization details
    """
    organization = get_object_or_404(Organization, pk=pk)

    # Check if user is a member of this organization
    try:
        user_membership = OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            is_active=True
        )
        user_role = user_membership.get_role_display()
        is_admin = user_membership.role == 'admin'
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not a member
        if request.user.is_staff:
            user_role = "Staff Admin"
            is_admin = True
        else:
            messages.error(request, "You don't have permission to view this organization.")
            return redirect('groups:organization_list')

    # Get all members of the organization
    members = organization.members.all().select_related('user')

    # Get recent surveys for this organization (limit to 5)
    try:
        surveys = Questionnaire.objects.filter(organization=organization).order_by('-created_at')[:5]
    except Exception as e:
        print(f"Error getting recent surveys: {e}")
        # Fallback to just getting the surveys without ordering
        surveys = Questionnaire.objects.filter(organization=organization)[:5]

    # Check if user can create surveys
    can_create_surveys = is_admin or user_role in ['Manager', 'Healthcare Provider']

    context = {
        'organization': organization,
        'members': members,
        'surveys': surveys,
        'user_role': user_role,
        'is_admin': is_admin,
        'can_create_surveys': can_create_surveys
    }

    return render(request, 'groups/organization_detail.html', context)

@login_required
def organization_edit(request, pk):
    """
    Edit an existing organization
    """
    organization = get_object_or_404(Organization, pk=pk)

    # Check if user has permission to edit
    try:
        OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            role='admin',
            is_active=True
        )
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not an admin member
        if not request.user.is_staff:
            messages.error(request, "You don't have permission to edit this organization.")
            return redirect('groups:organization_detail', pk=pk)

    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, 'Organization updated successfully!')
            return redirect('groups:organization_detail', pk=pk)
    else:
        form = OrganizationForm(instance=organization)

    return render(request, 'groups/organization_form.html', {
        'form': form,
        'organization': organization,
        'is_edit': True
    })

@login_required
def organization_delete(request, pk):
    """
    Delete an organization
    """
    organization = get_object_or_404(Organization, pk=pk)

    # Check if user has permission to delete
    try:
        OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            role='admin',
            is_active=True
        )
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not an admin member
        if not request.user.is_staff:
            messages.error(request, "You don't have permission to delete this organization.")
            return redirect('groups:organization_detail', pk=pk)

    if request.method == 'POST':
        organization.delete()
        messages.success(request, 'Organization deleted successfully!')
        return redirect('groups:organization_list')

    return render(request, 'groups/organization_confirm_delete.html', {'organization': organization})

@login_required
def member_list(request, pk):
    """
    Display a list of members for an organization
    """
    organization = get_object_or_404(Organization, pk=pk)

    # Check if user is a member of this organization
    try:
        user_membership = OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            is_active=True
        )
        is_admin = user_membership.role == 'admin'
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not a member
        if request.user.is_staff:
            is_admin = True
        else:
            messages.error(request, "You don't have permission to view this organization's members.")
            return redirect('groups:organization_list')

    # Get all members of the organization
    members = organization.members.all().select_related('user')

    context = {
        'organization': organization,
        'members': members,
        'is_admin': is_admin
    }

    return render(request, 'groups/member_list.html', context)

@login_required
def member_add(request, org_pk):
    """
    Add a member to an organization
    """
    organization = get_object_or_404(Organization, pk=org_pk)

    # Check if user has permission to add members
    try:
        OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            role='admin',
            is_active=True
        )
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not an admin member
        if not request.user.is_staff:
            messages.error(request, "You don't have permission to add members to this organization.")
            return redirect('groups:member_list', pk=org_pk)

    # Get users who are not already members
    existing_member_ids = organization.members.values_list('user_id', flat=True)
    available_users = User.objects.exclude(id__in=existing_member_ids)

    if request.method == 'POST':
        form = OrganizationMemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.organization = organization
            member.save()
            messages.success(request, 'Member added successfully!')
            return redirect('groups:member_list', pk=org_pk)
    else:
        form = OrganizationMemberForm()
        # Limit user choices to available users
        form.fields['user'].queryset = available_users

    return render(request, 'groups/member_form.html', {
        'form': form,
        'organization': organization
    })

@login_required
def member_detail(request, org_pk, pk):
    """
    Display member details
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    member = get_object_or_404(OrganizationMember, pk=pk, organization=organization)

    # Check if user has permission to view member details
    try:
        user_membership = OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            is_active=True
        )
        is_admin = user_membership.role == 'admin'
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not a member
        if request.user.is_staff:
            is_admin = True
        else:
            messages.error(request, "You don't have permission to view this member's details.")
            return redirect('groups:organization_list')

    context = {
        'organization': organization,
        'member': member,
        'is_admin': is_admin
    }

    return render(request, 'groups/member_detail.html', context)

@login_required
def member_edit(request, org_pk, pk):
    """
    Edit an existing member
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    member = get_object_or_404(OrganizationMember, pk=pk, organization=organization)

    # Check if user has permission to edit members
    try:
        OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            role='admin',
            is_active=True
        )
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not an admin member
        if not request.user.is_staff:
            messages.error(request, "You don't have permission to edit members in this organization.")
            return redirect('groups:member_detail', org_pk=org_pk, pk=pk)

    # Don't allow editing the last admin
    if member.role == 'admin' and member.user == request.user:
        admin_count = OrganizationMember.objects.filter(
            organization=organization,
            role='admin',
            is_active=True
        ).count()

        if admin_count <= 1:
            messages.warning(request, "You cannot modify your own admin role as you are the only admin.")
            return redirect('groups:member_detail', org_pk=org_pk, pk=pk)

    if request.method == 'POST':
        form = OrganizationMemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Member updated successfully!')
            return redirect('groups:member_detail', org_pk=org_pk, pk=pk)
    else:
        form = OrganizationMemberForm(instance=member)

    return render(request, 'groups/member_form.html', {
        'form': form,
        'organization': organization,
        'member': member
    })

@login_required
def member_remove(request, org_pk, pk):
    """
    Remove a member from an organization
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    member = get_object_or_404(OrganizationMember, pk=pk, organization=organization)

    # Check if user has permission to remove members
    try:
        OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            role='admin',
            is_active=True
        )
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not an admin member
        if not request.user.is_staff:
            messages.error(request, "You don't have permission to remove members from this organization.")
            return redirect('groups:member_detail', org_pk=org_pk, pk=pk)

    # Don't allow removing yourself if you're the last admin
    if member.user == request.user and member.role == 'admin':
        admin_count = OrganizationMember.objects.filter(
            organization=organization,
            role='admin',
            is_active=True
        ).count()

        if admin_count <= 1:
            messages.warning(request, "You cannot remove yourself as you are the only admin.")
            return redirect('groups:member_detail', org_pk=org_pk, pk=pk)

    if request.method == 'POST':
        member.delete()
        messages.success(request, 'Member removed successfully!')
        return redirect('groups:member_list', pk=org_pk)

    return render(request, 'groups/member_confirm_remove.html', {
        'org_pk': org_pk,
        'pk': pk
    })

@login_required
def organization_questionnaires(request, pk):
    """
    Display questionnaires for an organization
    """
    organization = get_object_or_404(Organization, pk=pk)

    # Check if user is a member of this organization
    try:
        user_membership = OrganizationMember.objects.get(
            organization=organization,
            user=request.user,
            is_active=True
        )
        is_admin = user_membership.role == 'admin'
    except OrganizationMember.DoesNotExist:
        # If user is staff, allow access even if not a member
        if request.user.is_staff:
            is_admin = True
        else:
            messages.error(request, "You don't have permission to view this organization's questionnaires.")
            return redirect('groups:organization_list')

    # Get questionnaires for this organization
    try:
        questionnaires = Questionnaire.objects.filter(organization=organization)

        # Apply filters if provided
        questionnaire_type = request.GET.get('type')
        if questionnaire_type:
            questionnaires = questionnaires.filter(type=questionnaire_type)

        questionnaire_category = request.GET.get('category')
        if questionnaire_category:
            questionnaires = questionnaires.filter(category=questionnaire_category)

        questionnaire_status = request.GET.get('status')
        if questionnaire_status:
            questionnaires = questionnaires.filter(status=questionnaire_status)
    except Exception as e:
        print(f"Error filtering questionnaires: {e}")
        # Fallback to an empty queryset
        questionnaires = Questionnaire.objects.none()

    # Paginate the results
    page = request.GET.get('page', 1)
    paginator = Paginator(questionnaires, 9)  # Show 9 questionnaires per page

    try:
        questionnaires = paginator.page(page)
    except PageNotAnInteger:
        questionnaires = paginator.page(1)
    except EmptyPage:
        questionnaires = paginator.page(paginator.num_pages)

    # Get choices for filter dropdowns
    try:
        questionnaire_types = Questionnaire._meta.get_field('type').choices
    except Exception as e:
        print(f"Error getting questionnaire types: {e}")
        questionnaire_types = [
            ('standard', 'Standard'),
            ('assessment', 'Assessment'),
            ('feedback', 'Feedback'),
            ('survey', 'Survey'),
            ('quiz', 'Quiz'),
            ('test', 'Test'),
        ]

    try:
        questionnaire_categories = Questionnaire._meta.get_field('category').choices
    except Exception as e:
        print(f"Error getting questionnaire categories: {e}")
        questionnaire_categories = [
            ('anxiety', 'Anxiety'),
            ('depression', 'Depression'),
            ('stress', 'Stress'),
            ('general', 'General'),
            ('mental_health', 'Mental Health'),
            ('physical_health', 'Physical Health'),
            ('education', 'Education'),
            ('customer_satisfaction', 'Customer Satisfaction'),
            ('employee_feedback', 'Employee Feedback'),
            ('research', 'Research'),
            ('clinical_assessment', 'Clinical Assessment'),
            ('custom', 'Custom'),
        ]

    try:
        questionnaire_statuses = Questionnaire._meta.get_field('status').choices
    except Exception as e:
        print(f"Error getting questionnaire statuses: {e}")
        questionnaire_statuses = [
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('archived', 'Archived'),
            ('inactive', 'Inactive'),
        ]

    context = {
        'organization': organization,
        'questionnaires': questionnaires,
        'is_admin': is_admin,
        'questionnaire_types': questionnaire_types,
        'questionnaire_categories': questionnaire_categories,
        'questionnaire_statuses': questionnaire_statuses,
    }

    return render(request, 'groups/organization_questionnaires.html', context)

@login_required
def view_member_dashboard(request, org_pk, member_pk):
    """
    View a member's dashboard from the admin portal
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
            messages.error(request, "You don't have permission to view this member's dashboard.")
            return redirect('groups:organization_list')

    # If user is not admin and can't view responses, deny access
    if not is_admin and not can_view_responses:
        messages.error(request, "You don't have permission to view this member's dashboard.")
        return redirect('groups:member_detail', org_pk=org_pk, pk=member_pk)

    # Check if this is a request to send an email
    if request.method == 'POST' and 'send_email' in request.POST:
        response_id = request.POST.get('response_id')
        email_type = request.POST.get('email_type')

        if response_id and email_type:
            response = get_object_or_404(Response, pk=response_id)

            # Check if the response belongs to this member
            if response.user == member.user:
                # Import the email service
                from feedback.services.email_service import EmailService

                if email_type == 'high_risk':
                    # Send high risk notification to admin
                    success = EmailService.send_high_risk_notification(response)
                    if success:
                        messages.success(request, "High risk notification email sent successfully.")
                    else:
                        messages.error(request, "Failed to send high risk notification email.")

                elif email_type == 'report':
                    # Send report to member
                    success = EmailService.send_response_report(response, member.user.email)
                    if success:
                        messages.success(request, "Response report email sent successfully.")
                    else:
                        messages.error(request, "Failed to send response report email.")
            else:
                messages.error(request, "Invalid response selected.")

        return redirect('groups:view_member_dashboard', org_pk=org_pk, member_pk=member_pk)

    # Check if this is a request to generate a PDF report
    if request.method == 'POST' and 'generate_pdf' in request.POST:
        report_type = request.POST.get('report_type')

        # Import the PDF service
        from feedback.services.pdf_service import PDFService

        if report_type == 'member_report':
            # Generate comprehensive member report
            return PDFService.generate_member_report(member, organization)

        elif report_type == 'response_report' and request.POST.get('response_id'):
            # Generate report for a specific response
            response_id = request.POST.get('response_id')
            response = get_object_or_404(Response, pk=response_id)

            # Check if the response belongs to this member
            if response.user == member.user:
                return PDFService.generate_response_report(response)
            else:
                messages.error(request, "Invalid response selected.")

        return redirect('groups:view_member_dashboard', org_pk=org_pk, member_pk=member_pk)

    # Get all responses for this member's user
    responses = Response.objects.filter(
        user=member.user,
        survey__organization=organization
    ).select_related('survey').order_by('-created_at')

    # Calculate statistics
    total_responses = responses.count()
    completed_responses = responses.filter(status='completed').count()
    average_score = responses.aggregate(Avg('score'))['score__avg'] or 0
    average_time = responses.aggregate(Avg('completion_time'))['completion_time__avg'] or 0

    # Get recent responses
    recent_responses = responses[:5]

    # Get questionnaires for this organization
    questionnaires = Questionnaire.objects.filter(organization=organization)

    # Get response count by questionnaire
    response_counts = []
    for questionnaire in questionnaires:
        count = Response.objects.filter(
            user=member.user,
            survey=questionnaire
        ).count()
        if count > 0:
            response_counts.append({
                'questionnaire': questionnaire,
                'count': count
            })

    # Determine risk level based on average score
    risk_level = 'low'
    risk_description = "Based on responses, this member appears to be at low risk. Continue with current practices and monitor regularly."

    if average_score < 50:
        risk_level = 'high'
        risk_description = "Responses indicate a higher level of risk. We recommend reviewing the detailed assessment and considering the suggested actions."
    elif average_score < 70:
        risk_level = 'medium'
        risk_description = "Responses indicate a moderate level of risk. Consider implementing some of the recommendations to improve the situation."

    # Check if any responses have been flagged for review
    flagged_responses = responses.filter(flagged_for_review=True)
    has_flagged_responses = flagged_responses.exists()

    # Check if any responses have high risk level
    high_risk_responses = responses.filter(risk_level='high')
    has_high_risk_responses = high_risk_responses.exists()

    context = {
        'organization': organization,
        'member': member,
        'total_responses': total_responses,
        'completed_responses': completed_responses,
        'average_score': average_score,
        'average_time': average_time,
        'recent_responses': recent_responses,
        'response_counts': response_counts,
        'risk_level': risk_level,
        'risk_description': risk_description,
        'has_flagged_responses': has_flagged_responses,
        'has_high_risk_responses': has_high_risk_responses,
        'flagged_responses': flagged_responses,
        'high_risk_responses': high_risk_responses,
        'is_admin': is_admin
    }

    return render(request, 'groups/member_dashboard.html', context)
