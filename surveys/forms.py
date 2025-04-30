from django import forms
from .models import Questionnaire, Question, QuestionChoice, QRCode, ScoringConfig, EmailTemplate

class SurveyForm(forms.ModelForm):
    class Meta:
        model = Questionnaire
        fields = ['title', 'description', 'instructions', 'type', 'category', 'status', 'organization']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'instructions': forms.Textarea(attrs={'rows': 4}),
        }
        # Explicitly set the table name to match the model's Meta.db_table
        db_table = 'surveys_survey'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make organization field optional
        self.fields['organization'].required = False
        # Set default values for required fields that aren't in the form
        if 'type' not in self.data:
            self.fields['type'].initial = 'standard'

    def save(self, commit=True):
        # Override the save method to handle the UUID to bigint conversion
        instance = super().save(commit=False)

        # If this is a new instance, we need to create it directly in the database
        if not instance.pk:
            from django.db import connection
            import uuid
            from django.utils.text import slugify

            # Generate slug if not provided
            if not instance.slug:
                instance.slug = slugify(instance.title)

                # Ensure slug is unique
                original_slug = instance.slug
                counter = 1
                while Questionnaire.objects.filter(slug=instance.slug).exists():
                    instance.slug = f"{original_slug}-{counter}"
                    counter += 1

            # Generate access code if not provided
            if not instance.access_code:
                instance.access_code = str(uuid.uuid4())[:8].upper()

            with connection.cursor() as cursor:
                # Insert directly into surveys_survey table
                cursor.execute("""
                    INSERT INTO surveys_survey
                    (title, slug, description, instructions, category, status,
                    is_template, allow_anonymous, requires_auth, created_by_id,
                    organization_id, created_at, updated_at, qr_code, access_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s)
                    RETURNING id
                """, [
                    instance.title,
                    instance.slug,
                    instance.description or '',
                    instance.instructions or '',
                    instance.category,
                    instance.status,
                    False,  # is_template
                    True,   # allow_anonymous
                    False,  # requires_auth
                    instance.created_by_id,
                    instance.organization_id if hasattr(instance, 'organization_id') and instance.organization_id else None,
                    None,   # qr_code
                    instance.access_code
                ])

                # Get the ID of the newly created record
                instance.id = cursor.fetchone()[0]

        # If commit is True, save the instance
        if commit and instance.pk:
            # For existing instances, use the normal save method
            if hasattr(instance, '_state'):
                instance._state.adding = False

        return instance

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'description', 'question_type', 'required', 'order', 'is_scored',
                 'is_visible', 'scoring_weight', 'max_score', 'category']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2}),
            'description': forms.Textarea(attrs={'rows': 2}),
            'question_type': forms.Select(attrs={'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the question_type field is properly initialized
        self.fields['question_type'].initial = self.instance.question_type if self.instance and self.instance.pk else 'text'

        # Make sure question_type is required
        self.fields['question_type'].required = True

        # Make scoring fields not required
        self.fields['scoring_weight'].required = False
        self.fields['max_score'].required = False

        # Try to get question types from the database
        try:
            from .models import QuestionType
            question_types = QuestionType.objects.all().order_by('display_order')
            if question_types.exists():
                self.fields['question_type'].choices = [(qt.code, qt.name) for qt in question_types]
        except Exception as e:
            # If there's an error, use the default choices from the model
            pass

        # Add help text for debugging
        self.fields['question_type'].help_text = "Current value: " + str(self.fields['question_type'].initial)

    def clean_question_type(self):
        """Ensure the question_type is properly cleaned and validated"""
        question_type = self.cleaned_data.get('question_type')
        if not question_type:
            # Default to 'text' if no question type is provided
            self.add_error('question_type', 'Question type is required')
            return 'text'

        # Validate that the question type is one of the allowed choices
        valid_types = [choice[0] for choice in Question.TYPE_CHOICES]
        if question_type not in valid_types:
            self.add_error('question_type', f'Invalid question type. Must be one of: {", ".join(valid_types)}')
            return 'text'

        return question_type

    def clean(self):
        """Validate the entire form"""
        cleaned_data = super().clean()

        # Validate text field
        text = cleaned_data.get('text')
        if not text or len(text.strip()) == 0:
            self.add_error('text', 'Question text is required')

        # Validate question type specific requirements
        question_type = cleaned_data.get('question_type')

        # For choice questions, we'll validate the choices in the view
        # We'll handle this with client-side validation instead of adding a form error
        if question_type in ['single_choice', 'multiple_choice']:
            # Just log a reminder, don't add an error
            pass

        # Handle scoring fields based on is_scored flag
        is_scored = cleaned_data.get('is_scored')

        if is_scored:
            # If question is scored, ensure scoring fields have default values if not provided
            scoring_weight = cleaned_data.get('scoring_weight')
            max_score = cleaned_data.get('max_score')

            # Set default values if not provided
            if scoring_weight is None:
                cleaned_data['scoring_weight'] = 1.0

            if max_score is None:
                cleaned_data['max_score'] = 0

            # For choice-based questions, ensure they can be scored
            if question_type in ['single_choice', 'multiple_choice', 'scale']:
                # These question types can be scored, so make sure scoring_weight is set
                if not cleaned_data.get('scoring_weight'):
                    cleaned_data['scoring_weight'] = 1.0
        else:
            # If question is not scored, set default values for scoring fields
            cleaned_data['scoring_weight'] = 1.0
            cleaned_data['max_score'] = 0

        return cleaned_data

class QuestionChoiceForm(forms.ModelForm):
    class Meta:
        model = QuestionChoice
        fields = ['text', 'order', 'score', 'is_correct']


class QRCodeForm(forms.ModelForm):
    class Meta:
        model = QRCode
        fields = ['survey', 'name', 'description', 'is_active', 'expires_at']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # Filter questionnaires to those the user has access to
            user_questionnaires = Questionnaire.objects.filter(created_by=user)
            org_questionnaires = Questionnaire.objects.filter(organization__members__user=user)
            questionnaires = (user_questionnaires | org_questionnaires).distinct()

            self.fields['survey'].queryset = questionnaires


class ScoringConfigForm(forms.ModelForm):
    class Meta:
        model = ScoringConfig
        fields = ['name', 'description', 'scoring_method', 'max_score', 'passing_score', 'rules', 'is_active', 'is_default']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'rules': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter scoring rules in JSON format'}),
        }

    def __init__(self, *args, **kwargs):
        questionnaire = kwargs.pop('questionnaire', None)
        super().__init__(*args, **kwargs)

        if questionnaire:
            self.initial['survey'] = questionnaire

    def clean(self):
        cleaned_data = super().clean()
        is_default = cleaned_data.get('is_default')
        survey = cleaned_data.get('survey')

        # If this config is set as default, unset any other default configs for this questionnaire
        if is_default and survey and not self.instance.pk:
            ScoringConfig.objects.filter(survey=survey, is_default=True).update(is_default=False)

        return cleaned_data


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['name', 'description', 'subject', 'message', 'html_content', 'variables', 'category', 'is_active', 'is_default', 'organization']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'message': forms.Textarea(attrs={'rows': 10}),
            'html_content': forms.Textarea(attrs={'rows': 15}),
            'variables': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter variables in JSON format'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_default = cleaned_data.get('is_default')
        category = cleaned_data.get('category')
        organization = cleaned_data.get('organization')

        # If this template is set as default, unset any other default templates in the same category and organization
        if is_default and category and not self.instance.pk:
            query = EmailTemplate.objects.filter(category=category, is_default=True)
            if organization:
                query = query.filter(organization=organization)
            else:
                query = query.filter(organization__isnull=True)
            query.update(is_default=False)

        return cleaned_data
