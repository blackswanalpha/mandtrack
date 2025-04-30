from django.core.management.base import BaseCommand
from surveys.models import Questionnaire, Question, QuestionChoice
import json

class Command(BaseCommand):
    help = 'Check questions in the database and diagnose any issues'

    def add_arguments(self, parser):
        parser.add_argument('--questionnaire_id', type=str, help='Questionnaire ID to check')
        parser.add_argument('--question_id', type=str, help='Question ID to check')

    def handle(self, *args, **options):
        questionnaire_id = options.get('questionnaire_id')
        question_id = options.get('question_id')

        if questionnaire_id:
            self.check_questionnaire(questionnaire_id)
        elif question_id:
            self.check_question(question_id)
        else:
            self.check_all()

    def check_all(self):
        """Check all questionnaires and questions"""
        self.stdout.write(self.style.SUCCESS('Checking all questionnaires and questions...'))
        
        # Count questionnaires
        questionnaire_count = Questionnaire.objects.count()
        self.stdout.write(f'Found {questionnaire_count} questionnaires')
        
        # Count questions
        question_count = Question.objects.count()
        self.stdout.write(f'Found {question_count} questions')
        
        # Count choices
        choice_count = QuestionChoice.objects.count()
        self.stdout.write(f'Found {choice_count} question choices')
        
        # Check for questions without questionnaires
        orphaned_questions = Question.objects.filter(survey__isnull=True).count()
        if orphaned_questions > 0:
            self.stdout.write(self.style.WARNING(f'Found {orphaned_questions} questions without a questionnaire'))
        
        # Check for choices without questions
        orphaned_choices = QuestionChoice.objects.filter(question__isnull=True).count()
        if orphaned_choices > 0:
            self.stdout.write(self.style.WARNING(f'Found {orphaned_choices} choices without a question'))
        
        # Check for choice questions without choices
        choice_questions = Question.objects.filter(question_type__in=['single_choice', 'multiple_choice'])
        for q in choice_questions:
            if q.choices.count() == 0:
                self.stdout.write(self.style.WARNING(f'Question {q.id} is a {q.question_type} but has no choices'))

    def check_questionnaire(self, questionnaire_id):
        """Check a specific questionnaire"""
        try:
            questionnaire = Questionnaire.objects.get(pk=questionnaire_id)
            self.stdout.write(self.style.SUCCESS(f'Found questionnaire: {questionnaire.title}'))
            
            # Count questions
            questions = questionnaire.questions.all()
            self.stdout.write(f'Found {questions.count()} questions for this questionnaire')
            
            # List all questions
            for i, q in enumerate(questions):
                self.stdout.write(f'{i+1}. {q.text[:50]}... (ID: {q.id}, Type: {q.question_type})')
                
                # For choice questions, list choices
                if q.question_type in ['single_choice', 'multiple_choice']:
                    choices = q.choices.all()
                    if choices.count() == 0:
                        self.stdout.write(self.style.WARNING(f'   This question has no choices!'))
                    else:
                        for j, c in enumerate(choices):
                            self.stdout.write(f'   {j+1}. {c.text} (Score: {c.score})')
            
        except Questionnaire.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Questionnaire with ID {questionnaire_id} not found'))

    def check_question(self, question_id):
        """Check a specific question"""
        try:
            question = Question.objects.get(pk=question_id)
            self.stdout.write(self.style.SUCCESS(f'Found question: {question.text[:50]}...'))
            
            # Show question details
            self.stdout.write('Question details:')
            question_data = {
                'id': question.id,
                'text': question.text,
                'description': question.description,
                'question_type': question.question_type,
                'required': question.required,
                'order': question.order,
                'is_scored': question.is_scored,
                'is_visible': question.is_visible,
                'survey_id': question.survey_id if question.survey else None,
            }
            self.stdout.write(json.dumps(question_data, indent=2))
            
            # Check if question has a questionnaire
            if question.survey:
                self.stdout.write(f'Belongs to questionnaire: {question.survey.title} (ID: {question.survey.id})')
            else:
                self.stdout.write(self.style.ERROR('This question is not associated with any questionnaire!'))
            
            # For choice questions, list choices
            if question.question_type in ['single_choice', 'multiple_choice']:
                choices = question.choices.all()
                if choices.count() == 0:
                    self.stdout.write(self.style.WARNING('This is a choice question but has no choices!'))
                else:
                    self.stdout.write(f'Found {choices.count()} choices:')
                    for i, c in enumerate(choices):
                        self.stdout.write(f'{i+1}. {c.text} (Score: {c.score})')
            
        except Question.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Question with ID {question_id} not found'))
