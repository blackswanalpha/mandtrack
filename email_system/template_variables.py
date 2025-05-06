"""
Template variables system for email templates.

This module provides a system for defining and rendering template variables
in email templates. It includes a registry of available variables and
functions for rendering templates with variable substitution.
"""
from django.utils import timezone
from django.conf import settings
import re
import json
from datetime import datetime

class TemplateVariableRegistry:
    """
    Registry of available template variables.
    """
    def __init__(self):
        self.variables = {}
        self.categories = {}
        self._register_default_variables()
    
    def register_variable(self, name, description, example, category="General", callback=None):
        """
        Register a new template variable.
        
        Args:
            name (str): The variable name (without {{ }})
            description (str): Description of the variable
            example (str): Example value
            category (str): Category for grouping variables
            callback (callable, optional): Function to call to get the value
        """
        self.variables[name] = {
            'name': name,
            'description': description,
            'example': example,
            'category': category,
            'callback': callback
        }
        
        # Add to category
        if category not in self.categories:
            self.categories[category] = []
        
        if name not in self.categories[category]:
            self.categories[category].append(name)
    
    def get_variable(self, name):
        """
        Get a variable by name.
        """
        return self.variables.get(name)
    
    def get_all_variables(self):
        """
        Get all registered variables.
        """
        return self.variables
    
    def get_variables_by_category(self):
        """
        Get variables organized by category.
        """
        result = {}
        for category, var_names in self.categories.items():
            result[category] = [self.variables[name] for name in var_names]
        return result
    
    def _register_default_variables(self):
        """
        Register default variables.
        """
        # System variables
        self.register_variable(
            'site.name',
            'The name of the site',
            'MindTrack',
            'System',
            lambda context: settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'MindTrack'
        )
        
        self.register_variable(
            'site.url',
            'The URL of the site',
            'https://mindtrack.example.com',
            'System',
            lambda context: settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://mindtrack.example.com'
        )
        
        self.register_variable(
            'date.today',
            'Current date',
            timezone.now().strftime('%B %d, %Y'),
            'Date & Time',
            lambda context: timezone.now().strftime('%B %d, %Y')
        )
        
        self.register_variable(
            'date.now',
            'Current date and time',
            timezone.now().strftime('%B %d, %Y %H:%M'),
            'Date & Time',
            lambda context: timezone.now().strftime('%B %d, %Y %H:%M')
        )
        
        # User variables
        self.register_variable(
            'user.email',
            'Email address of the recipient',
            'user@example.com',
            'User',
            lambda context: context.get('user', {}).get('email', '')
        )
        
        self.register_variable(
            'user.name',
            'Full name of the recipient',
            'John Doe',
            'User',
            lambda context: context.get('user', {}).get('name', '')
        )
        
        self.register_variable(
            'user.first_name',
            'First name of the recipient',
            'John',
            'User',
            lambda context: context.get('user', {}).get('first_name', '')
        )
        
        # Organization variables
        self.register_variable(
            'organization.name',
            'Name of the organization',
            'Acme Inc.',
            'Organization',
            lambda context: context.get('organization', {}).get('name', '')
        )
        
        self.register_variable(
            'organization.address',
            'Address of the organization',
            '123 Main St, City, Country',
            'Organization',
            lambda context: context.get('organization', {}).get('address', '')
        )
        
        # Response variables
        self.register_variable(
            'response.id',
            'ID of the response',
            '12345',
            'Response',
            lambda context: str(context.get('response', {}).get('id', ''))
        )
        
        self.register_variable(
            'response.score',
            'Score of the response',
            '85',
            'Response',
            lambda context: str(context.get('response', {}).get('score', ''))
        )
        
        self.register_variable(
            'response.date',
            'Date the response was submitted',
            'January 1, 2023',
            'Response',
            lambda context: context.get('response', {}).get('created_at', timezone.now()).strftime('%B %d, %Y')
        )
        
        # Questionnaire variables
        self.register_variable(
            'questionnaire.title',
            'Title of the questionnaire',
            'Mental Health Assessment',
            'Questionnaire',
            lambda context: context.get('questionnaire', {}).get('title', '')
        )
        
        self.register_variable(
            'questionnaire.description',
            'Description of the questionnaire',
            'A comprehensive assessment of mental health factors',
            'Questionnaire',
            lambda context: context.get('questionnaire', {}).get('description', '')
        )


class TemplateRenderer:
    """
    Renderer for email templates with variable substitution.
    """
    def __init__(self, registry=None):
        self.registry = registry or TemplateVariableRegistry()
        self.variable_pattern = r'{{(.*?)}}'
    
    def render(self, template, context=None):
        """
        Render a template with variable substitution.
        
        Args:
            template (str): The template string
            context (dict, optional): Context data for variables
        
        Returns:
            str: The rendered template
        """
        context = context or {}
        
        def replace_variable(match):
            var_name = match.group(1).strip()
            variable = self.registry.get_variable(var_name)
            
            if variable and variable['callback']:
                return str(variable['callback'](context))
            
            # Check if it's a nested context variable (e.g., user.profile.name)
            parts = var_name.split('.')
            value = context
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    # Variable not found, return the original placeholder
                    return match.group(0)
            
            return str(value)
        
        return re.sub(self.variable_pattern, replace_variable, template)
    
    def get_preview_context(self):
        """
        Get a sample context for previewing templates.
        
        Returns:
            dict: Sample context data
        """
        return {
            'user': {
                'email': 'user@example.com',
                'name': 'John Doe',
                'first_name': 'John',
                'last_name': 'Doe'
            },
            'organization': {
                'name': 'Acme Inc.',
                'address': '123 Main St, City, Country',
                'phone': '(123) 456-7890',
                'email': 'info@acme.com'
            },
            'response': {
                'id': 12345,
                'score': 85,
                'created_at': timezone.now(),
                'status': 'completed'
            },
            'questionnaire': {
                'title': 'Mental Health Assessment',
                'description': 'A comprehensive assessment of mental health factors',
                'category': 'Mental Health'
            }
        }


# Create global instances
variable_registry = TemplateVariableRegistry()
template_renderer = TemplateRenderer(variable_registry)


def render_template(template, context=None):
    """
    Render a template with variable substitution.
    
    Args:
        template (str): The template string
        context (dict, optional): Context data for variables
    
    Returns:
        str: The rendered template
    """
    return template_renderer.render(template, context)


def get_available_variables():
    """
    Get all available template variables.
    
    Returns:
        dict: Variables organized by category
    """
    return variable_registry.get_variables_by_category()


def register_variable(name, description, example, category="General", callback=None):
    """
    Register a new template variable.
    
    Args:
        name (str): The variable name (without {{ }})
        description (str): Description of the variable
        example (str): Example value
        category (str): Category for grouping variables
        callback (callable, optional): Function to call to get the value
    """
    variable_registry.register_variable(name, description, example, category, callback)
