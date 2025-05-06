"""
Data definitions for questionnaire selector features.
This file contains the standard choices for questionnaire categories, types, and statuses.
"""

# Questionnaire Categories
QUESTIONNAIRE_CATEGORIES = [
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

# Questionnaire Types
QUESTIONNAIRE_TYPES = [
    ('standard', 'Standard'),
    ('assessment', 'Assessment'),
    ('screening', 'Screening'),
    ('feedback', 'Feedback'),
    ('survey', 'Survey'),
    ('clinical', 'Clinical'),
    ('research', 'Research'),
    ('educational', 'Educational'),
    ('other', 'Other'),
]

# Questionnaire Statuses
QUESTIONNAIRE_STATUSES = [
    ('draft', 'Draft'),
    ('active', 'Active'),
    ('archived', 'Archived'),
]

# Question Types
QUESTION_TYPES = [
    ('text', 'Text'),
    ('textarea', 'Long Text'),
    ('number', 'Number'),
    ('single_choice', 'Single Choice'),
    ('multiple_choice', 'Multiple Choice'),
    ('scale', 'Scale'),
    ('date', 'Date'),
    ('time', 'Time'),
    ('file', 'File Upload'),
    ('country', 'Country'),
    ('email', 'Email'),
    ('phone', 'Phone'),
    ('image', 'Image Upload'),
    ('signature', 'Signature'),
    ('location', 'Location'),
    ('rating', 'Rating'),
    ('matrix', 'Matrix'),
    ('slider', 'Slider'),
    ('dropdown', 'Dropdown'),
    ('checkbox', 'Checkbox'),
    ('radio', 'Radio Button'),
    ('hidden', 'Hidden'),
]

# Question Categories
QUESTION_CATEGORIES = [
    ('demographic', 'Demographic'),
    ('clinical', 'Clinical'),
    ('behavioral', 'Behavioral'),
    ('satisfaction', 'Satisfaction'),
    ('feedback', 'Feedback'),
    ('knowledge', 'Knowledge'),
    ('other', 'Other'),
]
