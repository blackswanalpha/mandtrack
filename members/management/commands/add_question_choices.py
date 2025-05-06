from django.core.management.base import BaseCommand
from surveys.models import Questionnaire, Question, QuestionChoice

class Command(BaseCommand):
    help = 'Adds choices to existing questions'

    def handle(self, *args, **options):
        # Get the test questionnaire
        try:
            questionnaire = Questionnaire.objects.get(title='Mental Health Assessment')
        except Questionnaire.DoesNotExist:
            self.stdout.write(self.style.ERROR('Test questionnaire not found.'))
            return
        
        # Define choices for each question
        choices_data = {
            'How would you rate your overall mental health?': [
                {'text': 'Excellent', 'score': 5},
                {'text': 'Good', 'score': 4},
                {'text': 'Fair', 'score': 3},
                {'text': 'Poor', 'score': 2},
                {'text': 'Very poor', 'score': 1}
            ],
            'How often do you feel stressed?': [
                {'text': 'Never', 'score': 5},
                {'text': 'Rarely', 'score': 4},
                {'text': 'Sometimes', 'score': 3},
                {'text': 'Often', 'score': 2},
                {'text': 'Always', 'score': 1}
            ],
            'How would you rate your sleep quality?': [
                {'text': 'Excellent', 'score': 5},
                {'text': 'Good', 'score': 4},
                {'text': 'Fair', 'score': 3},
                {'text': 'Poor', 'score': 2},
                {'text': 'Very poor', 'score': 1}
            ],
            'Which of the following symptoms have you experienced in the past two weeks?': [
                {'text': 'Feeling down or depressed', 'score': 1},
                {'text': 'Little interest or pleasure in activities', 'score': 1},
                {'text': 'Trouble falling or staying asleep', 'score': 1},
                {'text': 'Feeling tired or having little energy', 'score': 1},
                {'text': 'Poor appetite or overeating', 'score': 1},
                {'text': 'Trouble concentrating', 'score': 1},
                {'text': 'None of the above', 'score': 0}
            ]
        }
        
        # Get all questions for this questionnaire
        questions = Question.objects.filter(survey=questionnaire)
        
        for question in questions:
            # Skip questions that don't need choices
            if question.question_type not in ['single_choice', 'multiple_choice']:
                continue
            
            # Skip questions that already have choices
            if question.choices.exists():
                self.stdout.write(self.style.WARNING(f'Question "{question.text}" already has choices. Skipping.'))
                continue
            
            # Get choices for this question
            if question.text in choices_data:
                choices = choices_data[question.text]
                
                # Create choices
                for i, choice_data in enumerate(choices):
                    QuestionChoice.objects.create(
                        question=question,
                        text=choice_data['text'],
                        score=choice_data.get('score', 0),
                        order=i + 1
                    )
                
                self.stdout.write(self.style.SUCCESS(f'Added {len(choices)} choices to question "{question.text}"'))
            else:
                self.stdout.write(self.style.WARNING(f'No choices defined for question "{question.text}"'))
        
        self.stdout.write(self.style.SUCCESS('Finished adding choices to questions.'))
