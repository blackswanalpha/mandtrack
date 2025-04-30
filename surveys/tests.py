from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from .models import Survey, Question, QuestionChoice
from groups.models import Organization

User = get_user_model()

class SurveyModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            type='healthcare',
            created_by=self.user
        )

        self.survey = Survey.objects.create(
            title='Test Survey',
            description='This is a test survey',
            instructions='Please answer all questions',
            category='anxiety',
            status='draft',
            created_by=self.user,
            organization=self.organization
        )

    def test_survey_creation(self):
        """Test that a survey can be created"""
        self.assertEqual(self.survey.title, 'Test Survey')
        self.assertEqual(self.survey.description, 'This is a test survey')
        self.assertEqual(self.survey.instructions, 'Please answer all questions')
        self.assertEqual(self.survey.category, 'anxiety')
        self.assertEqual(self.survey.status, 'draft')
        self.assertEqual(self.survey.created_by, self.user)
        self.assertEqual(self.survey.organization, self.organization)
        self.assertFalse(self.survey.is_template)

    def test_survey_slug_generation(self):
        """Test that a slug is automatically generated"""
        self.assertEqual(self.survey.slug, slugify(self.survey.title))

    def test_survey_access_code_generation(self):
        """Test that an access code is automatically generated"""
        self.assertIsNotNone(self.survey.access_code)
        self.assertEqual(len(self.survey.access_code), 8)

    def test_survey_qr_code_generation(self):
        """Test that a QR code is automatically generated"""
        self.assertIsNotNone(self.survey.qr_code)

    def test_survey_string_representation(self):
        """Test the string representation of a survey"""
        self.assertEqual(str(self.survey), 'Test Survey')

    def test_get_absolute_url(self):
        """Test the get_absolute_url method"""
        self.assertEqual(self.survey.get_absolute_url(), f"/surveys/{self.survey.slug}/")

    def test_get_question_count(self):
        """Test the get_question_count method"""
        # Initially no questions
        self.assertEqual(self.survey.get_question_count(), 0)

        # Add a question
        Question.objects.create(
            survey=self.survey,
            text='Test Question',
            question_type='text',
            required=True,
            order=1
        )

        # Now should have 1 question
        self.assertEqual(self.survey.get_question_count(), 1)


class QuestionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        self.survey = Survey.objects.create(
            title='Test Survey',
            description='This is a test survey',
            category='anxiety',
            status='draft',
            created_by=self.user
        )

        self.question = Question.objects.create(
            survey=self.survey,
            text='Test Question',
            description='This is a test question',
            question_type='radio',
            required=True,
            order=1
        )

        self.choice1 = QuestionChoice.objects.create(
            question=self.question,
            text='Choice 1',
            order=1,
            score=1
        )

        self.choice2 = QuestionChoice.objects.create(
            question=self.question,
            text='Choice 2',
            order=2,
            score=2
        )

    def test_question_creation(self):
        """Test that a question can be created"""
        self.assertEqual(self.question.text, 'Test Question')
        self.assertEqual(self.question.description, 'This is a test question')
        self.assertEqual(self.question.question_type, 'radio')
        self.assertTrue(self.question.required)
        self.assertEqual(self.question.order, 1)
        self.assertEqual(self.question.survey, self.survey)

    def test_question_string_representation(self):
        """Test the string representation of a question"""
        self.assertEqual(str(self.question), 'Test Question')

    def test_get_choices(self):
        """Test the get_choices method"""
        choices = self.question.get_choices()
        self.assertEqual(choices.count(), 2)
        self.assertIn(self.choice1, choices)
        self.assertIn(self.choice2, choices)


class QuestionChoiceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        self.survey = Survey.objects.create(
            title='Test Survey',
            category='anxiety',
            status='draft',
            created_by=self.user
        )

        self.question = Question.objects.create(
            survey=self.survey,
            text='Test Question',
            question_type='radio',
            required=True,
            order=1
        )

        self.choice = QuestionChoice.objects.create(
            question=self.question,
            text='Test Choice',
            order=1,
            score=5
        )

    def test_choice_creation(self):
        """Test that a choice can be created"""
        self.assertEqual(self.choice.text, 'Test Choice')
        self.assertEqual(self.choice.order, 1)
        self.assertEqual(self.choice.score, 5)
        self.assertEqual(self.choice.question, self.question)

    def test_choice_string_representation(self):
        """Test the string representation of a choice"""
        self.assertEqual(str(self.choice), 'Test Choice')
