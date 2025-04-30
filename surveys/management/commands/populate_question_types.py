from django.core.management.base import BaseCommand
from surveys.models import QuestionType

class Command(BaseCommand):
    help = 'Populate the QuestionType model with default values'

    def handle(self, *args, **options):
        # Get default question types
        default_types = QuestionType.get_default_types()
        
        # Count existing question types
        existing_count = QuestionType.objects.count()
        self.stdout.write(f'Found {existing_count} existing question types')
        
        # Create default question types if none exist
        if existing_count == 0:
            self.stdout.write('Creating default question types...')
            created_count = 0
            
            for type_data in default_types:
                QuestionType.objects.create(**type_data)
                created_count += 1
                self.stdout.write(f'Created question type: {type_data["name"]}')
            
            self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} question types'))
        else:
            self.stdout.write('Question types already exist, skipping creation')
            
            # Update existing question types with default values
            self.stdout.write('Updating existing question types...')
            updated_count = 0
            
            for type_data in default_types:
                code = type_data['code']
                try:
                    question_type = QuestionType.objects.get(code=code)
                    # Update fields that might be missing
                    for key, value in type_data.items():
                        if key != 'code':  # Don't update the code
                            setattr(question_type, key, value)
                    question_type.save()
                    updated_count += 1
                    self.stdout.write(f'Updated question type: {type_data["name"]}')
                except QuestionType.DoesNotExist:
                    # Create if it doesn't exist
                    QuestionType.objects.create(**type_data)
                    self.stdout.write(f'Created missing question type: {type_data["name"]}')
                    updated_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} question types'))
