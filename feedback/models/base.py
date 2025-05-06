"""
Base models for the feedback app.
This file is used to break circular imports.
"""
from django.db import models
from django.conf import settings
import uuid

class Response(models.Model):
    """
    Model for responses to questionnaires
    """
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    RISK_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
        ('unknown', 'Unknown'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('non-binary', 'Non-Binary'),
        ('prefer_not_to_say', 'Prefer Not to Say'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Use the correct model reference with the actual model name
    survey = models.ForeignKey('surveys.SurveysQuestionnaire', on_delete=models.CASCADE, related_name='responses', null=True)
    # Add a questionnaire field as an alias for survey to maintain compatibility
    questionnaire = models.ForeignKey('surveys.SurveysQuestionnaire', on_delete=models.CASCADE, related_name='questionnaire_responses', null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='questionnaire_responses')
    patient_identifier = models.CharField(max_length=50, blank=True, null=True)
    patient_name = models.CharField(max_length=255, blank=True, null=True)
    patient_email = models.EmailField(blank=True, null=True)
    patient_age = models.PositiveIntegerField(blank=True, null=True)
    patient_gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='unknown')
    flagged_for_review = models.BooleanField(default=False)
    completion_time = models.PositiveIntegerField(blank=True, null=True, help_text="Time to complete in seconds")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    metadata = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    organization = models.ForeignKey('groups.Organization', on_delete=models.SET_NULL, null=True, blank=True, related_name='responses')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Response'
        verbose_name_plural = 'Responses'
        indexes = [
            models.Index(fields=['survey'], name='fb_resp_survey_idx1'),
            models.Index(fields=['user'], name='fb_resp_user_idx1'),
            models.Index(fields=['organization'], name='fb_resp_org_idx1'),
            models.Index(fields=['patient_identifier'], name='fb_resp_patient_id_idx1'),
            models.Index(fields=['patient_email'], name='fb_resp_patient_email_idx1'),
            models.Index(fields=['risk_level'], name='fb_resp_risk_level_idx1'),
            models.Index(fields=['completed_at'], name='fb_resp_completed_at_idx1'),
            models.Index(fields=['created_at'], name='fb_resp_created_at_idx1'),
        ]

    def __str__(self):
        return f"Response to {self.survey.title} ({self.id})"


class Answer(models.Model):
    """
    Model for individual answers to questions
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='answers', null=True)
    # Use the correct model reference with the actual model name
    question = models.ForeignKey('surveys.SurveysQuestion', on_delete=models.CASCADE, related_name='answers', null=True)
    value = models.JSONField(blank=True, null=True)  # Store any type of answer in JSON format
    text_answer = models.TextField(blank=True, null=True)
    # Use the correct model reference with the actual model name
    selected_choice = models.ForeignKey('surveys.SurveysQuestionchoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='answers')
    # Use the correct model reference with the actual model name
    multiple_choices = models.ManyToManyField('surveys.SurveysQuestionchoice', blank=True, related_name='multiple_answers')
    numeric_value = models.FloatField(blank=True, null=True)
    date_value = models.DateField(blank=True, null=True)
    time_value = models.TimeField(blank=True, null=True)
    file_upload = models.FileField(upload_to='answer_files/', blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Fix the ordering issue by removing the reference to question__order
        ordering = ['created_at']
        verbose_name = 'Answer'
        verbose_name_plural = 'Answers'
        unique_together = ['response', 'question']
        indexes = [
            models.Index(fields=['response'], name='fb_ans_response_idx1'),
            models.Index(fields=['question'], name='fb_ans_question_idx1'),
        ]

    def __str__(self):
        return f"Answer to {self.question}"


class AIAnalysis(models.Model):
    """
    Model for AI analysis results of questionnaire responses
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response = models.OneToOneField(Response, on_delete=models.CASCADE, related_name='analysis', null=True)
    summary = models.TextField()
    detailed_analysis = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    insights = models.JSONField(blank=True, null=True)
    raw_data = models.JSONField(default=dict)
    model_used = models.CharField(max_length=100, blank=True, null=True)
    confidence_score = models.FloatField(blank=True, null=True)

    # Advanced analysis fields
    risk_level = models.CharField(max_length=20, choices=Response.RISK_LEVEL_CHOICES, default='unknown')
    risk_justification = models.TextField(blank=True)
    trends = models.TextField(blank=True)
    follow_up_areas = models.TextField(blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_analyses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Analysis'
        verbose_name_plural = 'AI Analyses'
        indexes = [
            models.Index(fields=['response'], name='fb_ai_response_idx1'),
            models.Index(fields=['created_by'], name='fb_ai_created_by_idx1'),
            models.Index(fields=['created_at'], name='fb_ai_created_at_idx1'),
        ]

    def __str__(self):
        return f"Analysis for {self.response}"
