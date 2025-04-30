from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import SurveyResponse, Answer, AnalysisResult
from surveys.models import Survey, Question, QuestionChoice

User = get_user_model()

class SurveyResponseModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        self.survey = Survey.objects.create(
            title='Test Survey',
            category='anxiety',
            status='active',
            created_by=self.user
        )

        self.response = SurveyResponse.objects.create(
            survey=self.survey,
            respondent=self.user,
            respondent_name='Test User',
            respondent_email='test@example.com',
            status='completed',
            total_score=10,
            risk_level='low'
        )

    def test_response_creation(self):
        """Test that a survey response can be created"""
        self.assertEqual(self.response.survey, self.survey)
        self.assertEqual(self.response.respondent, self.user)
        self.assertEqual(self.response.respondent_name, 'Test User')
        self.assertEqual(self.response.respondent_email, 'test@example.com')
        self.assertEqual(self.response.status, 'completed')
        self.assertEqual(self.response.total_score, 10)
        self.assertEqual(self.response.risk_level, 'low')

    def test_response_id_generation(self):
        """Test that a response ID is automatically generated"""
        self.assertIsNotNone(self.response.response_id)
        self.assertEqual(len(self.response.response_id), 10)

    def test_response_string_representation(self):
        """Test the string representation of a response"""
        self.assertEqual(str(self.response), f"Response {self.response.response_id} for {self.survey.title}")

    def test_get_answer_count(self):
        """Test the get_answer_count method"""
        # Initially no answers
        self.assertEqual(self.response.get_answer_count(), 0)

        # Create a question
        question = Question.objects.create(
            survey=self.survey,
            text='Test Question',
            question_type='text',
            required=True,
            order=1
        )

        # Add an answer
        Answer.objects.create(
            response=self.response,
            question=question,
            text_answer='Test Answer'
        )

        # Now should have 1 answer
        self.assertEqual(self.response.get_answer_count(), 1)


class AnswerModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        self.survey = Survey.objects.create(
            title='Test Survey',
            category='anxiety',
            status='active',
            created_by=self.user
        )

        self.response = SurveyResponse.objects.create(
            survey=self.survey,
            respondent=self.user,
            status='completed'
        )

        # Create different types of questions
        self.text_question = Question.objects.create(
            survey=self.survey,
            text='Text Question',
            question_type='text',
            required=True,
            order=1
        )

        self.radio_question = Question.objects.create(
            survey=self.survey,
            text='Radio Question',
            question_type='radio',
            required=True,
            order=2
        )

        self.choice = QuestionChoice.objects.create(
            question=self.radio_question,
            text='Test Choice',
            order=1,
            score=5
        )

        # Create different types of answers
        self.text_answer = Answer.objects.create(
            response=self.response,
            question=self.text_question,
            text_answer='Test Answer'
        )

        self.choice_answer = Answer.objects.create(
            response=self.response,
            question=self.radio_question,
            selected_choice=self.choice
        )

    def test_text_answer_creation(self):
        """Test that a text answer can be created"""
        self.assertEqual(self.text_answer.response, self.response)
        self.assertEqual(self.text_answer.question, self.text_question)
        self.assertEqual(self.text_answer.text_answer, 'Test Answer')

    def test_choice_answer_creation(self):
        """Test that a choice answer can be created"""
        self.assertEqual(self.choice_answer.response, self.response)
        self.assertEqual(self.choice_answer.question, self.radio_question)
        self.assertEqual(self.choice_answer.selected_choice, self.choice)

    def test_get_answer_display(self):
        """Test the get_answer_display method"""
        self.assertEqual(self.text_answer.get_answer_display(), 'Test Answer')
        self.assertEqual(self.choice_answer.get_answer_display(), 'Test Choice')

    def test_answer_string_representation(self):
        """Test the string representation of an answer"""
        self.assertEqual(str(self.text_answer), f"Answer to {self.text_question.text}")


class AnalysisResultModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        self.survey = Survey.objects.create(
            title='Test Survey',
            category='anxiety',
            status='active',
            created_by=self.user
        )

        self.response = SurveyResponse.objects.create(
            survey=self.survey,
            respondent=self.user,
            status='completed'
        )

        self.analysis = AnalysisResult.objects.create(
            response=self.response,
            summary='Test Summary',
            detailed_analysis='Test Detailed Analysis',
            recommendations='Test Recommendations'
        )

    def test_analysis_creation(self):
        """Test that an analysis result can be created"""
        self.assertEqual(self.analysis.response, self.response)
        self.assertEqual(self.analysis.summary, 'Test Summary')
        self.assertEqual(self.analysis.detailed_analysis, 'Test Detailed Analysis')
        self.assertEqual(self.analysis.recommendations, 'Test Recommendations')

    def test_analysis_string_representation(self):
        """Test the string representation of an analysis result"""
        self.assertEqual(str(self.analysis), f"Analysis for {self.response}")
