class AIModel(models.Model):
    """
    Model for AI models that can be used for analysis
    """
    MODEL_TYPE_CHOICES = [
        ('sentiment', 'Sentiment Analysis'),
        ('classification', 'Classification'),
        ('clustering', 'Clustering'),
        ('regression', 'Regression'),
        ('nlp', 'Natural Language Processing'),
        ('custom', 'Custom Model'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPE_CHOICES)
    version = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    configuration = models.JSONField(default=dict, blank=True, help_text="Model configuration parameters")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_ai_models')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_active', 'name']
        verbose_name = 'AI Model'
        verbose_name_plural = 'AI Models'
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class AIAnalysisConfiguration(models.Model):
    """
    Configuration for AI analysis on a questionnaire
    """
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='ai_configurations')
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='questionnaire_configurations')
    is_enabled = models.BooleanField(default=True)
    auto_analyze = models.BooleanField(default=False, help_text="Automatically analyze new responses")
    parameters = models.JSONField(default=dict, blank=True, help_text="Analysis parameters specific to this questionnaire")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_ai_configs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['questionnaire', 'ai_model']
        verbose_name = 'AI Analysis Configuration'
        verbose_name_plural = 'AI Analysis Configurations'
        unique_together = ['questionnaire', 'ai_model']
    
    def __str__(self):
        return f"{self.ai_model.name} for {self.questionnaire.title}"


class AIAnalysisResult(models.Model):
    """
    Results of AI analysis on a response
    """
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='ai_analyses')
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='analysis_results')
    configuration = models.ForeignKey(AIAnalysisConfiguration, on_delete=models.SET_NULL, null=True, related_name='analysis_results')
    result_data = models.JSONField(help_text="Analysis results in JSON format")
    summary = models.TextField(blank=True, help_text="Human-readable summary of the analysis")
    confidence_score = models.FloatField(null=True, blank=True, help_text="Confidence level of the analysis (0-1)")
    analyzed_at = models.DateTimeField(auto_now_add=True)
    analyzed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='conducted_analyses')
    
    class Meta:
        ordering = ['-analyzed_at']
        verbose_name = 'AI Analysis Result'
        verbose_name_plural = 'AI Analysis Results'
    
    def __str__(self):
        return f"Analysis of {self.response} using {self.ai_model.name}"


class AIInsight(models.Model):
    """
    Insights derived from AI analysis
    """
    INSIGHT_TYPE_CHOICES = [
        ('trend', 'Trend'),
        ('anomaly', 'Anomaly'),
        ('pattern', 'Pattern'),
        ('recommendation', 'Recommendation'),
        ('prediction', 'Prediction'),
        ('other', 'Other'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, null=True, blank=True)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='ai_insights')
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='generated_insights')
    related_responses = models.ManyToManyField(Response, related_name='insights', blank=True)
    supporting_data = models.JSONField(default=dict, blank=True, help_text="Data supporting this insight")
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Insight'
        verbose_name_plural = 'AI Insights'
    
    def __str__(self):
        return self.title


class AIFeedback(models.Model):
    """
    Feedback on AI analysis results
    """
    FEEDBACK_TYPE_CHOICES = [
        ('accuracy', 'Accuracy'),
        ('relevance', 'Relevance'),
        ('usefulness', 'Usefulness'),
        ('other', 'Other'),
    ]
    
    analysis_result = models.ForeignKey(AIAnalysisResult, on_delete=models.CASCADE, related_name='feedback')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES)
    rating = models.IntegerField(help_text="Rating from 1-5")
    comments = models.TextField(blank=True)
    provided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='ai_feedback')
    provided_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-provided_at']
        verbose_name = 'AI Feedback'
        verbose_name_plural = 'AI Feedback'
    
    def __str__(self):
        return f"Feedback on {self.analysis_result} by {self.provided_by}"
