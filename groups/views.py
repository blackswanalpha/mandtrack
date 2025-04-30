from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def organization_list(request):
    """
    Display a list of all organizations
    """
    # In a real app, you'd fetch organizations from the database
    organizations = [
        {'id': 1, 'name': 'General Hospital', 'type': 'Healthcare', 'members': 15},
        {'id': 2, 'name': 'Community Clinic', 'type': 'Healthcare', 'members': 8},
        {'id': 3, 'name': 'Research Institute', 'type': 'Research', 'members': 12},
    ]
    return render(request, 'groups/organization_list.html', {'organizations': organizations})

@login_required
def organization_create(request):
    """
    Create a new organization
    """
    if request.method == 'POST':
        # Process form data
        messages.success(request, 'Organization created successfully!')
        return redirect('groups:organization_list')
    return render(request, 'groups/organization_form.html')

@login_required
def organization_detail(request, pk):
    """
    Display organization details
    """
    # In a real app, you'd fetch the organization from the database
    organization = {'id': pk, 'name': 'Sample Organization', 'type': 'Healthcare', 'members': 15}
    return render(request, 'groups/organization_detail.html', {'organization': organization})

@login_required
def organization_edit(request, pk):
    """
    Edit an existing organization
    """
    # In a real app, you'd fetch the organization from the database
    organization = {'id': pk, 'name': 'Sample Organization', 'type': 'Healthcare', 'members': 15}

    if request.method == 'POST':
        # Process form data
        messages.success(request, 'Organization updated successfully!')
        return redirect('groups:organization_detail', pk=pk)
    return render(request, 'groups/organization_form.html', {'organization': organization})

@login_required
def organization_delete(request, pk):
    """
    Delete an organization
    """
    # In a real app, you'd fetch and delete the organization from the database
    if request.method == 'POST':
        # Delete the organization
        messages.success(request, 'Organization deleted successfully!')
        return redirect('groups:organization_list')
    return render(request, 'groups/organization_confirm_delete.html', {'pk': pk})

@login_required
def member_list(request, pk):
    """
    Display a list of members for an organization
    """
    # In a real app, you'd fetch the organization and its members from the database
    organization = {'id': pk, 'name': 'Sample Organization'}
    members = [
        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com', 'role': 'Admin'},
        {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com', 'role': 'Member'},
        {'id': 3, 'name': 'Bob Johnson', 'email': 'bob@example.com', 'role': 'Member'},
    ]
    return render(request, 'groups/member_list.html', {'organization': organization, 'members': members})

@login_required
def member_add(request, org_pk):
    """
    Add a member to an organization
    """
    # In a real app, you'd fetch the organization from the database
    organization = {'id': org_pk, 'name': 'Sample Organization'}

    if request.method == 'POST':
        # Process form data
        messages.success(request, 'Member added successfully!')
        return redirect('groups:member_list', pk=org_pk)
    return render(request, 'groups/member_form.html', {'organization': organization})

@login_required
def member_detail(request, org_pk, pk):
    """
    Display member details
    """
    # In a real app, you'd fetch the organization and member from the database
    organization = {'id': org_pk, 'name': 'Sample Organization'}
    member = {'id': pk, 'name': 'John Doe', 'email': 'john@example.com', 'role': 'Admin'}
    return render(request, 'groups/member_detail.html', {'organization': organization, 'member': member})

@login_required
def member_edit(request, org_pk, pk):
    """
    Edit an existing member
    """
    # In a real app, you'd fetch the organization and member from the database
    organization = {'id': org_pk, 'name': 'Sample Organization'}
    member = {'id': pk, 'name': 'John Doe', 'email': 'john@example.com', 'role': 'Admin'}

    if request.method == 'POST':
        # Process form data
        messages.success(request, 'Member updated successfully!')
        return redirect('groups:member_detail', org_pk=org_pk, pk=pk)
    return render(request, 'groups/member_form.html', {'organization': organization, 'member': member})

@login_required
def member_remove(request, org_pk, pk):
    """
    Remove a member from an organization
    """
    # In a real app, you'd fetch and remove the member from the database
    if request.method == 'POST':
        # Remove the member
        messages.success(request, 'Member removed successfully!')
        return redirect('groups:member_list', pk=org_pk)
    return render(request, 'groups/member_confirm_remove.html', {'org_pk': org_pk, 'pk': pk})
